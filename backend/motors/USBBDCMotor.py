import time
import serial
import struct

from pyvesc import encode
from pyvesc.VESC.messages import SetRPM, SetDutyCycle

from .iMotor import iMotor
from logs.logger_config import get_logger
logger = get_logger(__name__)

PORT = "/dev/ttyACM0"   # or "/dev/ttyUSB0"
BAUD = 115200

DUTY = 0.05        # 5% duty
RUN_TIME = 10      # seconds

COMM_GET_VALUES = 4  # VESC command id for "get values"

STEP = 2

# RPM control parameters
POLE_PAIRS = 2  # Flipsky 5065 4-pole motor = 2 pole pairs
MAX_RPM = 1200  # Maximum mechanical RPM target (0-600 command → 0-1200 RPM)
VOLTAGE = 24  # Operating voltage (volts)
MOTOR_KV = 270  # Motor kV rating
ERPM_SCALE = POLE_PAIRS  # Convert mechanical RPM to ERPM

# VESC firmware response scaling: firmware only achieves ~20% of commanded ERPM
# Test showed 4000 ERPM cmd → 838 ERPM actual, so use 5.0x as optimal scaling
# This is the best balance: reduces undershoot without creating oscillation or saturation
VESC_ERPM_RESPONSE_FACTOR = 5.0

# PID Controller parameters for low-speed dead zone compensation
MIN_ERPM_THRESHOLD = 250 * ERPM_SCALE  # ~250 mechanical RPM before VESC responds
PID_KP = 0.8  # Proportional gain (reduces steady-state error quickly)
PID_KI = 0.6  # Integral gain (accumulates error for persistent correction)
PID_KD = 0.06  # Derivative gain (dampens oscillation)
PID_MAX_INTEGRAL = 25000  # Anti-windup clamp
SPEED_LOOP_RATE = 0.02  # Update rate (50 Hz)

# Low-speed feedforward boost to overcome VESC dead zone
LOW_SPEED_BOOST_THRESHOLD = 300 * ERPM_SCALE  # Boost threshold (reduced now that VESC scaling helps)
LOW_SPEED_BOOST_MAGNITUDE = 400 * ERPM_SCALE  # Boost magnitude (reduced from 800 with VESC scaling)
LOW_SPEED_BOOST_FALLOFF = 2.0  # How quickly boost decreases at higher speeds

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
    # Default scale factor to convert a 0-600 command value into RPM (0-1200).
    DEFAULT_RPM_SCALE = MAX_RPM / 600.0

    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 0
    motor = None
    ser = serial.Serial(PORT, BAUD, timeout = 0.05)

    def __init__(self, rpm_scale: float = None):
        self._rpm_scale = (
            rpm_scale
            if rpm_scale is not None
            else self.DEFAULT_RPM_SCALE
        )
        # Initialize motor to zero RPM
        self.ser.write(encode(SetRPM(0)))
        
        # PID controller state
        self._pid_integral = 0.0
        self._pid_prev_error = 0.0
        self._last_speed_poll_time = time.time()

    @property
    def rpm_scale(self) -> float:
        """Gets the scale factor used to convert a 0-600 command value into mechanical RPM."""
        return self._rpm_scale

    @rpm_scale.setter
    def rpm_scale(self, value: float):
        """Sets the scale factor used in RPM conversions."""
        if value <= 0.0:
            raise ValueError("rpm_scale must be positive")
        self._rpm_scale = value

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
        self._pid_integral = 0.0  # Reset integral windup
        self._pid_prev_error = 0.0
        self.ser.write(encode(SetRPM(0)))

    def changeSpeed(self, dutyCycle: float, isShotMode: bool):
        """
        Change motor speed using native VESC RPM control with aggressive PID + feedforward.
        
        Note: Parameter named 'dutyCycle' for interface compatibility, but now represents
        an RPM command value (0-600 maps to 0-1200 mechanical RPM) sent to VESC's native
        closed-loop speed controller instead of raw duty cycle.
        
        Uses:
        - Host-side PID controller to reduce overshoot/undershoot
        - Feedforward boost to overcome low-speed dead zone
        
        Args:
            dutyCycle: RPM command (0-600 maps to 0-1200 mechanical RPM)
            isShotMode: Flag for shot mode operation (for future extended logic)
        """
        # Clamp input to valid range
        clamped_rpm = self.clamp(dutyCycle, 0, 600)
        
        # Convert command (0-600) to mechanical RPM (0-1200)
        target_mech_rpm = clamped_rpm * self._rpm_scale
        self.targetSpeed = target_mech_rpm
        
        # Poll current speed for PID feedback
        actual_mech_rpm = self.getCurrentSpeed()
        
        if actual_mech_rpm is None:
            actual_mech_rpm = 0.0
        
        # Compute speed error
        speed_error = target_mech_rpm - actual_mech_rpm
        
        # PID controller to adjust ERPM command
        # P term: proportional to current error
        p_term = PID_KP * speed_error
        
        # I term: accumulate error over time (with anti-windup)
        self._pid_integral += speed_error * SPEED_LOOP_RATE
        self._pid_integral = self.clamp(self._pid_integral, -PID_MAX_INTEGRAL, PID_MAX_INTEGRAL)
        i_term = PID_KI * self._pid_integral
        
        # D term: dampen rapid changes (derivative of error)
        d_term = PID_KD * (speed_error - self._pid_prev_error) / SPEED_LOOP_RATE
        self._pid_prev_error = speed_error
        
        # Compute PID correction (in mechanical RPM)
        pid_correction = p_term + i_term + d_term
        
        # Minimal feedforward boost only for very low speeds (below 50 RPM) 
        # VESC scaling (5x) takes care of most low-speed response
        feedforward_boost = 0.0
        if target_mech_rpm < 50:
            feedforward_boost = 200 * ERPM_SCALE  # Only 200 ERPM boost at absolute minimum
        
        # Final ERPM command = target + PID correction + feedforward boost
        adjusted_mech_rpm = target_mech_rpm + pid_correction + feedforward_boost / ERPM_SCALE
        
        # Clamp to safe limits (0 to ~2x target max)
        adjusted_mech_rpm = self.clamp(adjusted_mech_rpm, 0, MAX_RPM * 2)
        
        # Convert to ERPM and apply VESC response scaling (firmware only achieves ~20% of command)
        target_erpm = int(adjusted_mech_rpm * ERPM_SCALE * VESC_ERPM_RESPONSE_FACTOR)
        
        # Log diagnostics at low speeds for debugging
        if target_mech_rpm < 400 and target_mech_rpm > 0:
            logger.debug(f"Low-speed: target={target_mech_rpm:.0f} RPM, actual={actual_mech_rpm:.0f}, error={speed_error:.0f}, pid_corr={pid_correction:.0f}, boost={feedforward_boost:.0f}, ERPM_cmd={target_erpm}")
        
        self.ser.write(encode(SetRPM(target_erpm)))
        self.currSpeed = actual_mech_rpm

    def getCurrentSpeed(self):
        """
        Poll VESC telemetry and return actual mechanical RPM.
        Returns None if telemetry read fails.
        """
        send_get_values(self.ser)
        vals = read_mc_values(self.ser)
        
        if vals is not None:
            erpm = vals["rpm"]
            # Your 4-pole RC motor = 2 pole pairs → mech RPM = ERPM / 2
            mech_rpm = erpm / ERPM_SCALE
            
            # Debug output (comment out if too verbose)
            # print(f"ERPM: {erpm:9.1f} | RPM: {mech_rpm:9.1f} | I_motor: {vals['motor_current']:6.2f} A | V_in: {vals['v_in']:5.2f} V | Duty: {vals['duty_now']*100:5.1f}% | Fault: {vals['fault']}")
            return mech_rpm
        
        return None

    def rampUp(self):
        """
        Ramp motor speed up to target.
        PID controller handles smooth acceleration automatically.
        """
        # PID handles ramping - just send current target
        target_erpm = int(self.targetSpeed * ERPM_SCALE)
        self.ser.write(encode(SetRPM(target_erpm)))

    def rampDown(self):
        """
        Ramp motor speed down to target.
        PID controller handles smooth deceleration automatically.
        """
        # PID handles ramping - just send current target
        target_erpm = int(self.targetSpeed * ERPM_SCALE)
        self.ser.write(encode(SetRPM(target_erpm)))


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
