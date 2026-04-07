from backend.smartdot.SmartDotConnectionManager import SmartDotConnectionManager
# from backend.models.DataController import DataController
from backend.cloud_api.CloudAPI import CloudAPI
# from backend.models.SessionData import SessionData
import utils
import random

try:
    from backend.motors.SimMotor import SimMotor
except ModuleNotFoundError:
    class SimMotor:
        def __init__(self, GPIOPin: int):
            self.currSpeed = 0.0
            self.targetSpeed = 0.0
            self.targetPower = 0.0

        def connect(self, GPIOPin: int):
            pass

        def disconnect(self, GPIOPin: int = None):
            pass

        def start(self, dutyCycle=100):
            self.currSpeed = float(dutyCycle)

        def stop(self):
            self.currSpeed = 0.0

        def changeSpeed(self, dutyCycle: int, isShotMode: bool):
            self.currSpeed = float(dutyCycle)

        def rampUp(self):
            pass

        def setTargetSpeed(self, targetSpeed: float):
            self.targetSpeed = targetSpeed

        def setTargetPower(self, targetPower: float):
            self.targetPower = targetPower

        def getCurrentSpeed(self):
            return self.currSpeed + random.uniform(-20, 20)

        def getTargetSpeed(self):
            return self.targetSpeed

        def getTargetPower(self):
            return self.targetPower

        def trigger_fault(self, fault_code: int = 5):
            print(f"Simulated motor fault triggered (code={fault_code})")

        def clear_fault(self):
            print("Simulated motor fault cleared")
lgpio = None
USBBDCMotor = None
StepMotor = None
if utils.is_raspberry_pi_5():
    try:
        from backend.motors.USBBDCMotor import USBBDCMotor  # UNCOMMENT AFTER STEPPER
    except Exception:
        USBBDCMotor = None
    try:
        from backend.motors.StepMotor import StepMotor  # uncomment when stepper works
    except Exception:
        StepMotor = None
    try:
        import lgpio
    except ImportError:
        lgpio = None


class MotorData:
    def __init__(self, dt, length, spin, tilt, angle):
        self.spin = spin
        self.tilt = tilt
        self.angle = angle
        self.dt = dt
        self.length = length
        self.connected = True

        
class BSC:
    def __init__(self):
        self.smartdotConnectionManager = SmartDotConnectionManager()
        self.cloud_api = CloudAPI()
        self.session = None
        self.data_controller = None
        # Diagnostic sampling interval (milliseconds) used by UI pages
        self.diagnostic_sample_interval_ms = 30

        self.motor_mode = "simulated"
        self.motor_mode_locked = False
        self.motor_mode_locked_reason = None
        self._real_motor_supported = utils.is_raspberry_pi_5()
        self.h = None
        self.motor1 = None
        self.motor2 = None
        self.motor3 = None

        self._initialize_motors()

    def _initialize_motors(self):
        if not self._real_motor_supported:
            self.use_simulated_motors(
                "Simulated motors locked.",
                locked=True,
            )
            return

        try:
            self.use_real_motors()
        except Exception:
            self.use_simulated_motors(
                "Simulated motors locked.",
                locked=True,
            )

    def _create_real_motors(self):
        if USBBDCMotor is None or StepMotor is None:
            raise RuntimeError("Real motor classes are unavailable")
        if lgpio is None:
            raise RuntimeError("lgpio is unavailable")

        self.h = lgpio.gpiochip_open(0)
        self.motor1 = USBBDCMotor(h=self.h)
        self.motor2 = StepMotor(27, 17, self.h, 5, False)
        self.motor3 = StepMotor(23, 24, self.h, 6, False)

    def use_real_motors(self):
        if not self._real_motor_supported:
            raise RuntimeError("Real motor mode is not supported on this device")

        self.disconnect_all_motors()
        self._create_real_motors()
        self.motor_mode = "real"
        self.motor_mode_locked = False
        self.motor_mode_locked_reason = None

    def use_simulated_motors(self, reason=None, locked=False):
        self.disconnect_all_motors()
        self.motor1 = SimMotor(2)
        self.motor2 = SimMotor(2)
        self.motor3 = SimMotor(2)
        self.motor_mode = "simulated"
        self.motor_mode_locked = locked
        self.motor_mode_locked_reason = reason

    def set_motor_mode(self, mode):
        if mode == "real":
            if self.motor_mode == "real" and not self.motor_mode_locked:
                return True
            if not self._real_motor_supported:
                self.use_simulated_motors(
                    "Simulated motors locked.",
                    locked=True,
                )
                return False
            try:
                self.use_real_motors()
                return True
            except Exception:
                self.use_simulated_motors(
                    "Simulated motors locked.",
                    locked=True,
                )
                return False
        elif mode == "simulated":
            self.use_simulated_motors(reason=None, locked=False)
            return True
        else:
            raise ValueError(f"Unknown motor mode: {mode}")

    def get_motor_status_message(self):
        if self.motor_mode_locked_reason:
            return self.motor_mode_locked_reason
        if self.motor_mode == "real":
            return "Using real motors."
        return "Using simulated motors."

    def get_smartdotConnectionManager(self):
        return self.smartdotConnectionManager

    def get_cloud_api(self):
        return self.cloud_api

    def get_session(self):
        return self.session

    def set_session(self, session):
        self.session = session

    def get_data_controller(self):
        return self.data_controller
        
    def set_data_controller(self, data_controller):
        self.data_controller = data_controller

    def disconnect_all_motors(self):
        for motor_name in ("motor1", "motor2", "motor3"):
            motor = getattr(self, motor_name, None)
            if motor is not None and hasattr(motor, "disconnect"):
                try:
                    motor.disconnect()
                except Exception:
                    pass

        if getattr(self, "h", None) is not None and lgpio is not None:
            try:
                lgpio.gpiochip_close(self.h)
            except Exception:
                pass
            finally:
                self.h = None

        self.connected = False


bsc = BSC()
