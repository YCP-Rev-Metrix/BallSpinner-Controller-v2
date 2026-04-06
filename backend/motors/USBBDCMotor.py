import time
import serial
import struct

from pyvesc import encode
from pyvesc.VESC.messages import SetDutyCycle
import utils
try:
    import lgpio
except ImportError:
    lgpio = None
from .iMotor import iMotor
from logs.logger_config import get_logger
logger = get_logger(__name__)

PORT = "/dev/ttyACM0"   # or "/dev/ttyUSB0"
BAUD = 115200

DUTY = 0.05        # 5% duty
RUN_TIME = 10      # seconds

COMM_GET_VALUES = 4  # VESC command id for "get values"

STEP = 2

FAULT_CODES = {
    0: "No fault",
    1: "Over voltage",
    2: "Under voltage",
    3: "Over temperature FETs",
    4: "Over temperature motor",
    5: "Motor stalled",
    6: "Current sensor fault",
    7: "Encoder fault",
}
FAULT_LIGHT_PIN = 25

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
    #0.000043333333
    DEFAULT_DUTY_CYCLE_SCALE = 0.0000218 # Tuned via testing to give good response across the full speed range without being too aggressive at low speeds. Adjust as needed based on your motor and performance preferences.
    

    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 0
    motor = None
    ser = serial.Serial(PORT, BAUD, timeout = 0.05)

    def __init__(self, duty_cycle_scale: float = None, h=None):
        # ser = serial.Serial(PORT, BAUD, timeout = 0.05)
        self._duty_cycle_scale = (
            duty_cycle_scale
            if duty_cycle_scale is not None
            else self.DEFAULT_DUTY_CYCLE_SCALE
        )

        logger.info("USBBDCMotor initialized: duty_cycle_scale=%.8f", self._duty_cycle_scale)

        # Track consecutive failed reads for getCurrentSpeed so we can log a warning
        self._missed_speed_reads = 0
        self._missed_speed_warn_threshold = 10

        # Default PID gains
        self.Kp = 0.05
        self.Ki = 0.02
        self.Kd = 0.0000

        self.h = h
        # For integral & derivative computation
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_time = time.time()

        self.ser.write(encode(SetDutyCycle(0.0)))
        if lgpio:
            lgpio.gpio_claim_output(self.h, self.GPIO_Pin, 0)

    @property
    def duty_cycle_scale(self) -> float:
        """Scale factor used to convert a 0-600 command value into a VESC duty cycle."""
        return self._duty_cycle_scale

    @duty_cycle_scale.setter
    def duty_cycle_scale(self, value: float):
        if value <= 0.0:
            raise ValueError("duty_cycle_scale must be positive")
        self._duty_cycle_scale = value

    @property
    def Kp(self) -> float:
        """Proportional gain used by changeSpeed()."""
        return self._Kp

    @Kp.setter
    def Kp(self, value: float):
        if value < 0.0:
            raise ValueError("Kp must be non-negative")
        self._Kp = value

    @property
    def Ki(self) -> float:
        """Integral gain used by changeSpeed()."""
        return self._Ki

    @Ki.setter
    def Ki(self, value: float):
        if value < 0.0:
            raise ValueError("Ki must be non-negative")
        self._Ki = value

    @property
    def Kd(self) -> float:
        """Derivative gain used by changeSpeed()."""
        return self._Kd

    @Kd.setter
    def Kd(self, value: float):
        if value < 0.0:
            raise ValueError("Kd must be non-negative")
        self._Kd = value

    # ---------------- CONNECT / DISCONNECT ----------------
    def connect(self):
        logger.info("USBBDCMotor.connect() called")
        # no-op placeholder in this implementation (GPIO VESC managed elsewhere)

    def disconnect(self):
        logger.info("USBBDCMotor.disconnect() called")
        if lgpio:
            lgpio.gpio_release(self.h, self.GPIO_Pin)

    def clamp(self, x, lo, hi):
        return max(lo, min(x, hi))

    def start(self):
        logger.info("USBBDCMotor.start() called")
        # start is a no-op at the low-level VESC interface here

    def stop(self):
        logger.info("USBBDCMotor.stop() called")
        self.targetSpeed = 0.0
        self.rampDown()

        # Clear PID state parameters so control restarts cleanly next time
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_time = time.time()

    def changeSpeed(self, dutyCycle: float, isShotMode: bool):
        """Basic P-style output toward a target speed."""

        self.targetSpeed = self.clamp(dutyCycle, 0, 1200)
        self.currSpeed = self.getCurrentSpeed()

        error = self.targetSpeed - self.currSpeed

        now = time.time()
        dt = now - self._prev_time if self._prev_time else 0.0
        if dt <= 0.0:
            dt = 1e-6
        d_error = (error - self._prev_error) / dt

        # Integral update (always run unless dt is zero) + anti-windup
        self._integral += error * dt
        self._integral = self.clamp(self._integral, -1200, 1200)

        self._prev_error = error
        self._prev_time = now
        if self.currSpeed < min(self.targetSpeed**2/900, self.targetSpeed) and self.targetSpeed != 0:
            # Motor is stopped give big kick to get it going, then let PID take over
            command = 1/self.duty_cycle_scale  # Garbage for logging purposes since we're not really using the PID output for this case
            duty = min(self.targetSpeed/6000, 1.0)  # run at 100% duty until we get a speed reading, then PID can take over
        else:
            command = (
                self.targetSpeed
                + (error * self.Kp)
                + (self._integral * self.Ki)
                + (d_error * self.Kd)
            )
            duty = self.clamp(command * self.duty_cycle_scale, 0.0, 1.0)

        logger.debug(
            "changeSpeed target=%.1f curr=%.1f err=%.1f cmd=%.1f duty=%.4f shot=%s",
            self.targetSpeed,
            self.currSpeed,
            error,
            command,
            duty,
            isShotMode,
        )

        self.ser.write(encode(SetDutyCycle(duty)))
        logger.debug("USBBDCMotor.changeSpeed() wrote duty=%.4f", duty)

    def getCurrentSpeed(self):
        '''Request the current speed from the VESC and return the mechanical RPM.

        If the VESC does not reply in time, keep the last-known speed.
        '''
        send_get_values(self.ser)
        vals = read_mc_values(self.ser)
        if vals is None:
            self._missed_speed_reads += 1
            if self._missed_speed_reads >= self._missed_speed_warn_threshold:
                logger.warning(
                    "No reply from VESC for getCurrentSpeed for %d consecutive reads; keeping last known speed %.1f RPM",
                    self._missed_speed_reads,
                    self.currSpeed,
                )
            else:
                logger.debug(
                    "No reply from VESC for getCurrentSpeed; keeping last known speed %.1f RPM",
                    self.currSpeed,
                )
            return self.currSpeed

        # Reset the missed-read counter on a successful read
        self._missed_speed_reads = 0

        erpm = vals["rpm"]

        # Your 4-pole RC motor = 2 pole pairs → mech RPM = ERPM / 2
        mech_rpm = erpm / 2.0

        self.currSpeed = mech_rpm
        logger.debug(
            "ERPM: %9.1f | RPM: %9.1f | I_motor: %6.2f A | V_in: %5.2f V | Duty: %5.1f%% | Fault: %s",
            erpm,
            mech_rpm,
            vals["motor_current"],
            vals["v_in"],
            vals["duty_now"] * 100,
            vals["fault"],
        )
        if vals["fault"] != 0:
            self.HandleFault(vals["fault"])
        return mech_rpm 
    def getVals(self):
        send_get_values(self.ser)
        vals = read_mc_values(self.ser)
        if vals is None:
            self._missed_speed_reads += 1
            if self._missed_speed_reads >= self._missed_speed_warn_threshold:
                logger.warning(
                    "No reply from VESC for getCurrentSpeed for %d consecutive reads; keeping last known speed %.1f RPM",
                    self._missed_speed_reads,
                    self.currSpeed,
                )
            else:
                logger.debug(
                    "No reply from VESC for getCurrentSpeed; keeping last known speed %.1f RPM",
                    self.currSpeed,
                )
            return self.currSpeed
        return vals

    def rampUp(self):
        logger.debug("USBBDCMotor.rampUp() from %.2f to %.2f", self.currSpeed, self.targetSpeed)
        while self.currSpeed < self.targetSpeed:
            self.currSpeed += STEP
            if self.currSpeed > self.targetSpeed:
                self.currSpeed = self.targetSpeed

            # Scale input x (0-600) to a range 0-2.6 for SetDutyCycle (which is a tiny eenie weenie bit over 600, like 605 but whatever)
            duty = self.currSpeed * self.duty_cycle_scale
            self.ser.write(encode(SetDutyCycle(duty)))
            logger.debug("USBBDCMotor.rampUp() duty=%.4f currSpeed=%.1f", duty, self.currSpeed)
            # time.sleep(0.02)

    def rampDown(self):
        logger.debug("USBBDCMotor.rampDown() from %.2f to %.2f", self.currSpeed, self.targetSpeed)
        while self.currSpeed > self.targetSpeed:
            self.currSpeed -= STEP
            if self.currSpeed < self.targetSpeed:
                self.currSpeed = self.targetSpeed

            duty = self.currSpeed * self.duty_cycle_scale
            self.ser.write(encode(SetDutyCycle(duty)))
            logger.debug("USBBDCMotor.rampDown() duty=%.4f currSpeed=%.1f", duty, self.currSpeed)
            # time.sleep(0.02)
        self.ser.write(encode(SetDutyCycle(self.currSpeed * self.duty_cycle_scale)))


    def HandleFault(self, faultCode):
        if faultCode == 0:
            if lgpio and getattr(self, 'h', None) is not None:
                lgpio.gpio_write(self.h, FAULT_LIGHT_PIN, 0)  # turn off fault light
            return
        
        faultDescription = FAULT_CODES.get(faultCode, "Unknown fault")
        logger.error("VESC fault code: %s (%s)", faultCode, faultDescription)
        utils.notify_user(f"VESC fault: {faultDescription} (code {faultCode})", title="Primary Motor Fault", type="critical")
        if lgpio and getattr(self, 'h', None) is not None:
            lgpio.gpio_write(self.h, FAULT_LIGHT_PIN, 1)  # turn on fault light

    def trigger_fault(self, fault_code: int = 5):
        """Trigger a simulated VESC fault via the motor fault handler."""
        self.HandleFault(fault_code)

    def clear_fault(self):
        """Clear any active motor fault indicator and fault state."""
        self.HandleFault(0)




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
