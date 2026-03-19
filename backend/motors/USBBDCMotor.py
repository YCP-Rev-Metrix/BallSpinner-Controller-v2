import time
import serial
import struct

from pyvesc import encode
from pyvesc.VESC.messages import SetDutyCycle

from .iMotor import iMotor
from logs.logger_config import get_logger
logger = get_logger(__name__)

PORT = "/dev/ttyACM0"   # or "/dev/ttyUSB0"
BAUD = 115200

DUTY = 0.05        # 5% duty
RUN_TIME = 10      # seconds

COMM_GET_VALUES = 4  # VESC command id for "get values"

STEP = 2

# ---------- VESC packet helpers (no pyvesc for GetValues) ----------

def crc16(data: bytes) -> int:
    """
    CRC16-CCITT (polynomial 0x1021, init 0) used by VESC.
    """
    crc = 0
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def make_packet(payload: bytes) -> bytes:
    """
    Build a full VESC UART packet from a payload.
    We only handle "short" packets (len <= 255) which is fine here.
    """
    length = len(payload)
    assert length <= 255
    packet = bytearray()
    packet.append(2)        # start byte for short packet
    packet.append(length)   # length
    packet.extend(payload)  # payload
    c = crc16(payload)
    packet.append((c >> 8) & 0xFF)  # CRC high
    packet.append(c & 0xFF)        # CRC low
    packet.append(3)        # stop byte
    return bytes(packet)


def send_get_values(ser: serial.Serial):
    """
    Send a COMM_GET_VALUES request to the VESC.
    """
    payload = bytes([COMM_GET_VALUES])
    pkt = make_packet(payload)
    ser.write(pkt)


def read_mc_values(ser: serial.Serial, timeout: float = 0.2):
    """
    Read one VESC packet and, if it's a COMM_GET_VALUES reply,
    decode key fields and return them as a dict.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        head = ser.read(1)
        if not head:
            continue

        h = head[0]
        if h not in (2, 3):
            continue

        # length
        if h == 2:
            lb = ser.read(1)
            if len(lb) != 1:
                continue
            length = lb[0]
        else:  # long packet (not expected for GetValues, but handle anyway)
            lb = ser.read(2)
            if len(lb) != 2:
                continue
            length = (lb[0] << 8) | lb[1]

        payload = ser.read(length)
        if len(payload) != length:
            continue

        # crc + end
        crc_bytes = ser.read(2)
        end = ser.read(1)
        if len(crc_bytes) != 2 or end != b'\x03':
            continue

        # (optional) check CRC
        # if crc16(payload) != ((crc_bytes[0] << 8) | crc_bytes[1]):
        #     continue

        # First byte of payload is command
        if not payload or payload[0] != COMM_GET_VALUES:
            continue

        # ----- Decode fields according to COMM_GET_VALUES layout -----
        ind = 1  # skip command byte

        def read_f16(scale):
            nonlocal ind
            raw = struct.unpack(">h", payload[ind:ind+2])[0]
            ind += 2
            return raw / scale

        def read_f32(scale):
            nonlocal ind
            raw = struct.unpack(">i", payload[ind:ind+4])[0]
            ind += 4
            return raw / scale

        def read_i32():
            nonlocal ind
            raw = struct.unpack(">i", payload[ind:ind+4])[0]
            ind += 4
            return raw

        temp_fet      = read_f16(10.0)
        temp_motor    = read_f16(10.0)
        motor_current = read_f32(100.0)
        input_current = read_f32(100.0)
        _id           = read_f32(100.0)
        _iq           = read_f32(100.0)
        duty_now      = read_f16(1000.0)
        rpm           = read_f32(1.0)
        v_in          = read_f16(10.0)
        amp_hours     = read_f32(10000.0)
        amp_hours_ch  = read_f32(10000.0)
        wh            = read_f32(10000.0)
        wh_ch         = read_f32(10000.0)
        tachometer    = read_i32()
        tach_abs      = read_i32()
        fault         = payload[ind]

        return {
            "temp_fet": temp_fet,
            "temp_motor": temp_motor,
            "motor_current": motor_current,
            "input_current": input_current,
            "duty_now": duty_now,
            "rpm": rpm,
            "v_in": v_in,
            "tachometer": tachometer,
            "tachometer_abs": tach_abs,
            "fault": fault,
        }

    return None

class USBBDCMotor(iMotor):
    # Default scale factor to convert a 0-600 command value into a VESC duty cycle (0-2.6).
    DEFAULT_DUTY_CYCLE_SCALE = 0.000043333333

    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 0
    motor = None
    ser = serial.Serial(PORT, BAUD, timeout = 0.05)

    def __init__(self, duty_cycle_scale: float = None):
        # ser = serial.Serial(PORT, BAUD, timeout = 0.05)
        self._duty_cycle_scale = (
            duty_cycle_scale
            if duty_cycle_scale is not None
            else self.DEFAULT_DUTY_CYCLE_SCALE
        )
        self.ser.write(encode(SetDutyCycle(0.0)))

    @property
    def duty_cycle_scale(self) -> float:
        """Gets the scale factor used to convert a 0-600 command value into a VESC duty cycle."""
        return self._duty_cycle_scale

    @duty_cycle_scale.setter
    def duty_cycle_scale(self, value: float):
        """Sets the scale factor used in duty cycle conversions."""
        if value <= 0.0:
            raise ValueError("duty_cycle_scale must be positive")
        self._duty_cycle_scale = value

    # ---------------- CONNECT / DISCONNECT ----------------
    def connect(self):
        pass

    def disconnect(self):
        pass

    def clamp(self, x, lo, hi):
        return max(lo, min(x, hi))

    def start(self):
        pass

    def stop(self):
        self.targetSpeed = 0.0
        self.rampDown()

    def changeSpeed(self, dutyCycle: float, isShotMode: bool):
        self.targetSpeed = self.clamp(dutyCycle, 0, 1200) # Clamp to bounds of graph (in case weird values)
        self.delta= self.targetSpeed-self.getCurrentSpeed()
        self.speed = self.targetSpeed + self.delta
        self.ser.write(encode(SetDutyCycle(self.targetSpeed * self.duty_cycle_scale)))
        self.currSpeed = self.targetSpeed
        self.getCurrentSpeed()

    def getCurrentSpeed(self):
        '''send_get_values(ser)
        vals = read_mc_values(ser)
        if vals is not None:
            
            return vals["rpm"]/2.0 #Encoder implement, maybe working'''
        send_get_values(self.ser)
        vals = read_mc_values(self.ser)
        if vals is not None:
            erpm = vals["rpm"]

            # Your 4-pole RC motor = 2 pole pairs → mech RPM = ERPM / 2
            mech_rpm = erpm / 2.0


        print(f"ERPM: {erpm:9.1f} | RPM: {mech_rpm:9.1f} | I_motor: {vals['motor_current']:6.2f} A | V_in: {vals['v_in']:5.2f} V | Duty: {vals['duty_now']*100:5.1f}% | Fault: {vals['fault']}")
        return mech_rpm

    def rampUp(self):
        while self.currSpeed < self.targetSpeed:
            self.currSpeed += STEP
            if self.currSpeed > self.targetSpeed:
                self.currSpeed = self.targetSpeed

            # Scale input x (0-600) to a range 0-2.6 for SetDutyCycle (which is a tiny eenie weenie bit over 600, like 605 but whatever)
            self.ser.write(encode(SetDutyCycle(self.currSpeed * self.duty_cycle_scale)))
            # time.sleep(0.02)

    def rampDown(self):
        while self.currSpeed > self.targetSpeed:
            self.currSpeed -= STEP
            if self.currSpeed < self.targetSpeed:
                self.currSpeed = self.targetSpeed

            # Scale input x (0-600) to a range 0-2.6 for SetDutyCycle (which is a tiny eenie weenie bit over 600, like 605 but whatever)
            self.ser.write(encode(SetDutyCycle(self.currSpeed * self.duty_cycle_scale)))
            # time.sleep(0.02)
        self.ser.write(encode(SetDutyCycle(self.currSpeed * self.duty_cycle_scale)))


# ---------- Main program ----------
'''
print(f"Opening {PORT}...")
with serial.Serial(PORT, BAUD, timeout=0.05) as ser:
    print("Connected.")

    # Stop motor initially
    ser.write(encode(SetDutyCycle(0.0)))
    time.sleep(0.2)

    print("Running at 5% duty and printing encoder/RPM data...")

    start = time.time()
    while time.time() - start < RUN_TIME:
        # 1) keep motor commanded
        ser.write(encode(SetDutyCycle(0.026)))#(time.time()-start)*DUTY*0.1)))

        # 2) ask for values
        send_get_values(ser)

        # 3) read and decode reply
        vals = read_mc_values(ser)
        if vals is not None:
            erpm = vals["rpm"]

            # Your 4-pole RC motor = 2 pole pairs → mech RPM = ERPM / 2
            mech_rpm = erpm / 2.0

            print(
                f"ERPM: {erpm:9.1f} | "
                f"RPM: {mech_rpm:9.1f} | "
                f"I_motor: {vals['motor_current']:6.2f} A | "
                f"V_in: {vals['v_in']:5.2f} V | "
                f"Duty: {vals['duty_now']*100:5.1f}% | "
                f"Fault: {vals['fault']}"
            )

        time.sleep(0.05)

    print("Stopping motor...")
    for _ in range(10):
        ser.write(encode(SetDutyCycle(0.0)))
        time.sleep(0.05)

print("Done.")
'''
