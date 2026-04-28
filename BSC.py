from backend.smartdot.SmartDotConnectionManager import SmartDotConnectionManager
# from backend.models.DataController import DataController
from backend.cloud_api.CloudAPI import CloudAPI
# from backend.models.SessionData import SessionData
import utils
import random
import time

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

        def returnToZero(self):
            self.currSpeed = 0.0

        def setCurrentPositionZero(self):
            self.currSpeed = 0.0

        def zero(self):
            self.currSpeed = 0.0
            return True

        def home(self):
            self.zero()

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
ADS1115CurrentSensor = None
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
        from backend.sensors.ADS1115CurrentSensor import ADS1115CurrentSensor
    except Exception:
        ADS1115CurrentSensor = None
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
    # Limit default: J8 physical pin 8 = BCM GPIO 14 (UART0 TX). Not to be confused with J8 pin 15 (= GPIO22).
    # GPIO 14 shares UART0 TX — release UART from kernel if the pin reads busy / wrong.
    # Unusable as a GPIO limit while the kernel/console keeps UART0 on GPIO14/15. Prefer another
    # BCM pin via "limit_switch_pin" in motor_tuning.json, or on the Pi run:
    #   sudo bash scripts/disable_serial_console_boot.sh --disable-uart-driver && sudo reboot
    # USBBDCMotor is unaffected: it uses pyserial on the USB device (e.g. /dev/ttyACM0 from
    # motor_tuning motor1.comm.port), not the Pi’s UART TX/RX pins — UART-over-USB keeps working.
    LIMIT_SWITCH_PIN = 14
    # False = switch connects GPIO to logic high when closed (internal pull-down → open reads LOW).
    # True = switch shorts GPIO to GND when closed (internal pull-up → open reads HIGH).
    LIMIT_SWITCH_ACTIVE_LOW = False

    def __init__(self):
        self.smartdotConnectionManager = SmartDotConnectionManager()
        self.cloud_api = CloudAPI()
        self.session = None
        self.data_controller = None
        # Shared sampling interval (milliseconds) used by UI pages
        self.sample_interval_ms = 50
        self._tuning_config = None
        try:
            from tuning_config import load_tuning_config
            self._tuning_config = load_tuning_config()
            interval_ms = self._tuning_config.get("sample_interval_ms")
            if isinstance(interval_ms, (int, float)):
                self.sample_interval_ms = interval_ms
        except Exception:
            self._tuning_config = None

        self.motor_mode = "simulated"
        self.motor_mode_locked = False
        self.motor_mode_locked_reason = None
        self.motor_mode_locked_due_to_vesc = False
        self.motor_mode_locked_due_to_pin_busy = False
        self._real_motor_supported = utils.is_raspberry_pi_5()
        self.h = None
        self.motor1 = None
        self.motor2 = None
        self.motor3 = None
        self.current_sensor = None
        self.limit_switch_pin = self.LIMIT_SWITCH_PIN
        self.limit_switch_active_low = self.LIMIT_SWITCH_ACTIVE_LOW
        self.limit_switch_pull = None  # None = auto from polarity; else "up"|"down"|"none"
        if isinstance(self._tuning_config, dict):
            lp = self._tuning_config.get("limit_switch_pin")
            if isinstance(lp, int) and lp >= 0:
                self.limit_switch_pin = lp
            al = self._tuning_config.get("limit_switch_active_low")
            if isinstance(al, bool):
                self.limit_switch_active_low = al
            pull = self._tuning_config.get("limit_switch_pull")
            if isinstance(pull, str):
                pl = pull.strip().lower()
                if pl in ("up", "down", "none"):
                    self.limit_switch_pull = pl

        self._initialize_motors()

        if self._tuning_config:
            try:
                from tuning_config import apply_tuning_config
                apply_tuning_config(self, self._tuning_config, apply_comm=False)
            except Exception:
                pass

    @property
    def diagnostic_sample_interval_ms(self):
        return self.sample_interval_ms

    @diagnostic_sample_interval_ms.setter
    def diagnostic_sample_interval_ms(self, value):
        self.sample_interval_ms = value

    def _initialize_motors(self):
        if not self._real_motor_supported:
            self.use_simulated_motors(
                "Simulated motors locked.",
                locked=True,
                due_to_vesc=False,
            )
            return

        try:
            self.use_real_motors()
        except Exception as e:
            err = str(e)
            is_pin_busy = "limit switch pin gpio" in err.lower() and "busy" in err.lower()
            reason = err if is_pin_busy else "Simulated motors locked."
            self.use_simulated_motors(
                reason,
                locked=True,
                due_to_vesc=True,
                due_to_pin_busy=is_pin_busy,
            )

    def _create_real_motors(self):
        # Steppers are required for real mode; spin (USB VESC) can fall back to simulation
        # when pyserial/pyvesc are missing so limit homing and tilt/angle GPIO still work.
        if StepMotor is None:
            raise RuntimeError(
                "StepMotor is unavailable (need lgpio and backend/motors/StepMotor)."
            )
        if lgpio is None:
            raise RuntimeError("lgpio is unavailable")

        self.h = lgpio.gpiochip_open(0)
        try:
            if self.limit_switch_pull == "up":
                _pull = lgpio.SET_PULL_UP
            elif self.limit_switch_pull == "down":
                _pull = lgpio.SET_PULL_DOWN
            elif self.limit_switch_pull == "none":
                _pull = lgpio.SET_PULL_NONE
            else:
                _pull = (
                    lgpio.SET_PULL_UP
                    if self.limit_switch_active_low
                    else lgpio.SET_PULL_DOWN
                )
            lgpio.gpio_claim_input(self.h, self.limit_switch_pin, _pull)
        except Exception as e:
            raise RuntimeError(
                f"Limit switch pin GPIO{self.limit_switch_pin} is busy. "
                "Release the pin from UART/other process and restart."
            ) from e
        self.current_sensor = None
        if ADS1115CurrentSensor is not None:
            try:
                self.current_sensor = ADS1115CurrentSensor()
            except Exception as e:
                print(f"Warning: ADS1115 current sensor initialization failed: {e}")
                self.current_sensor = None

        # Tilt and angle stepper motors both use the shared ADS1115 sensor.
        # Channel 0 is assigned to motor2 and channel 1 is assigned to motor3.
        # If the sensor is unavailable, current readings will remain None and the rest of the
        # real motor stack continues to work.
        motor_cfg = {}
        comm_cfg = {}
        if isinstance(self._tuning_config, dict):
            motor_cfg = self._tuning_config.get("motor1") or {}
            if isinstance(motor_cfg, dict):
                comm_cfg = motor_cfg.get("comm") or {}
        if USBBDCMotor is not None:
            self.motor1 = USBBDCMotor(
                h=self.h,
                duty_cycle_scale=motor_cfg.get("duty_cycle_scale") if isinstance(motor_cfg, dict) else None,
                serial_port=comm_cfg.get("port") if isinstance(comm_cfg, dict) else None,
                serial_baud=comm_cfg.get("baud") if isinstance(comm_cfg, dict) else None,
                serial_timeout_s=comm_cfg.get("serial_timeout_s") if isinstance(comm_cfg, dict) else None,
                get_values_timeout_s=comm_cfg.get("get_values_timeout_s") if isinstance(comm_cfg, dict) else None,
            )
        else:
            print(
                "Warning: USBBDCMotor not loaded (e.g. pyserial/pyvesc missing); "
                "using SimMotor for spin while tilt/angle use real steppers."
            )
            self.motor1 = SimMotor(2)
        homing_cfg = {}
        if isinstance(self._tuning_config, dict):
            hc = self._tuning_config.get("homing")
            if isinstance(hc, dict):
                homing_cfg = hc
        self.motor2 = StepMotor(
            23,
            24,
            self.h,
            6,
            False,
            current_sensor=self.current_sensor,
            current_sensor_channel=0,
            limit_switch_pin=self.limit_switch_pin,
            limit_switch_active_low=self.limit_switch_active_low,
            homing_config=homing_cfg or None,
        )
        self.motor3 = StepMotor(
            27,
            17,
            self.h,
            5,
            False,
            current_sensor=self.current_sensor,
            current_sensor_channel=1,
            limit_switch_pin=self.limit_switch_pin,
            limit_switch_active_low=self.limit_switch_active_low,
            homing_config=homing_cfg or None,
        )

    def _create_simulated_motors(self):
        self.motor1 = SimMotor(2)
        self.motor2 = SimMotor(2)
        self.motor3 = SimMotor(2)

    def use_real_motors(self):
        if not self._real_motor_supported:
            raise RuntimeError("Real motor mode is not supported on this device")

        self.disconnect_all_motors()
        self._create_real_motors()
        if self._tuning_config:
            try:
                from tuning_config import apply_tuning_config
                apply_tuning_config(self, self._tuning_config, apply_comm=False)
            except Exception:
                pass
        self.motor_mode = "real"
        self.motor_mode_locked = False
        self.motor_mode_locked_reason = None
        self.motor_mode_locked_due_to_pin_busy = False

    def use_simulated_motors(self, reason=None, locked=False, due_to_vesc=False, due_to_pin_busy=False):
        self.disconnect_all_motors()
        self._create_simulated_motors()
        self.motor_mode = "simulated"
        self.motor_mode_locked = locked
        self.motor_mode_locked_reason = reason
        self.motor_mode_locked_due_to_vesc = due_to_vesc
        self.motor_mode_locked_due_to_pin_busy = due_to_pin_busy

    def set_motor_mode(self, mode):
        if mode == "real":
            if self.motor_mode == "real" and not self.motor_mode_locked:
                return True
            if not self._real_motor_supported:
                self.use_simulated_motors(
                    "Simulated motors locked.",
                    locked=True,
                    due_to_vesc=False,
                )
                return False
            try:
                self.use_real_motors()
                return True
            except Exception:
                self.use_simulated_motors(
                    "Simulated motors locked.",
                    locked=True,
                    due_to_vesc=True,
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

    def home(self):
        self.zero()

    def _tilt_soft_reference(self):
        """Tilt cannot reach the shared limit from both directions.

        Disconnect the tilt stepper GPIO, wait, reconnect, jog by ``tilt_soft_home_deg``
        from tuning (default −5°), then ``setCurrentPositionZero()`` so that pose is the
        new software zero. Simulated tilt keeps using ``SimMotor.zero()``."""
        m3 = getattr(self, "motor3", None)
        if m3 is None:
            return False
        if StepMotor is None or not isinstance(m3, StepMotor):
            if hasattr(m3, "zero"):
                return bool(m3.zero())
            return False

        hc = {}
        if isinstance(self._tuning_config, dict):
            hc = self._tuning_config.get("homing") or {}
        tilt_deg = float(hc.get("tilt_soft_home_deg", -5.0))
        sleep_s = float(hc.get("tilt_soft_disconnect_sleep_s", 1.0))
        move_time = float(hc.get("tilt_soft_move_time_s", 0.5))

        try:
            m3.disconnect()
            time.sleep(max(0.0, sleep_s))
            m3.start()
            cw = tilt_deg >= 0.0
            m3._move_angle_timed(abs(tilt_deg), max(0.05, move_time), cw)
            m3.setCurrentPositionZero()
            return True
        except Exception as e:
            print(f"Tilt soft reference failed: {e}")
            return False

    def zero(self, silent=False, phase_callback=None):
        """Home angle (motor 2) then tilt (motor 3); shared limit GPIO requires this order.

        ``phase_callback(name, info)`` is optional; ``name`` is ``\"after_angle\"`` | ``\"before_tilt\"``
        | ``\"after_tilt\"``. ``info`` is a dict with ``\"ok\": bool`` where applicable (UI may refresh).

        Returns True if both axes homed successfully, False otherwise. Raises on unexpected error.
        """
        try:
            # Angle (motor2) must home before tilt (motor3); shared limit GPIO.
            m2 = getattr(self, "motor2", None)
            if m2 is not None and hasattr(m2, "zero"):
                ok_angle = m2.zero()
                if phase_callback:
                    try:
                        phase_callback("after_angle", {"ok": ok_angle is not False})
                    except Exception:
                        pass
                if ok_angle is False:
                    if not silent:
                        utils.notify_user("Angle (motor 2) homing failed.")
                    return False
            else:
                if phase_callback:
                    try:
                        phase_callback("after_angle", {"ok": False})
                    except Exception:
                        pass
                if not silent:
                    utils.notify_user("Motor 2 does not support zeroing.")
                return False

            m3 = getattr(self, "motor3", None)
            if m3 is None:
                if not silent:
                    utils.notify_user("Motor 3 does not support zeroing.")
                return False
            if phase_callback:
                try:
                    phase_callback("before_tilt", {})
                except Exception:
                    pass
            ok_tilt = self._tilt_soft_reference()
            if phase_callback:
                try:
                    phase_callback("after_tilt", {"ok": ok_tilt is not False})
                except Exception:
                    pass
            if ok_tilt is False:
                if not silent:
                    utils.notify_user("Tilt (motor 3) soft reference failed.")
                return False
            return True
        except Exception as e:
            print(f"Error zeroing motors: {e}")
            raise

    def zero_angle_only(self, silent=False):
        """Home the angle stepper (motor 2) only; does not move tilt (motor 3).

        If ``silent`` is False (default), failed homing surfaces a GUI notification when possible.
        """
        try:
            m2 = getattr(self, "motor2", None)
            if m2 is None or not hasattr(m2, "zero"):
                if not silent:
                    utils.notify_user("Motor 2 does not support zeroing.")
                return False
            ok = m2.zero()
            if ok is False and not silent:
                utils.notify_user("Angle (motor 2) homing failed.")
            return bool(ok)
        except Exception as e:
            print(f"Error homing angle: {e}")
            raise

    def zero_tilt_only(self, silent=False):
        """Establish tilt reference without limit homing (see ``_tilt_soft_reference``).

        If ``silent`` is False (default), failure surfaces a GUI notification when possible.
        """
        try:
            ok = self._tilt_soft_reference()
            if ok is False and not silent:
                utils.notify_user("Tilt (motor 3) soft reference failed.")
            return bool(ok)
        except Exception as e:
            print(f"Error homing tilt: {e}")
            raise


    def disconnect_all_motors(self):
        for motor_name in ("motor1", "motor2", "motor3"):
            motor = getattr(self, motor_name, None)
            if motor is not None and hasattr(motor, "disconnect"):
                try:
                    motor.disconnect()
                except Exception:
                    pass
                try:
                    if hasattr(motor, "returnToZero"):
                        motor.returnToZero()
                except Exception:
                    pass

        if getattr(self, "current_sensor", None) is not None:
            try:
                self.current_sensor.close()
            except Exception:
                pass
            self.current_sensor = None

        if getattr(self, "h", None) is not None and lgpio is not None:
            try:
                limit_pin = getattr(self, "limit_switch_pin", None)
                if limit_pin is not None:
                    try:
                        lgpio.gpio_free(self.h, limit_pin)
                    except Exception:
                        pass
                lgpio.gpiochip_close(self.h)
            except Exception:
                pass
            finally:
                self.h = None

        self.connected = False

    def disconnect_motor_drivers(self):
        """Disable each motor driver (disconnect/stop pins, VESC enable release) **without**
        closing the shared gpiochip, limit-switch input, or current sensor — so hardware stays
        ready for the next shot aside from intentional tilt disconnect during ``zero()``."""
        for motor_name in ("motor1", "motor2", "motor3"):
            motor = getattr(self, motor_name, None)
            if motor is not None and hasattr(motor, "disconnect"):
                try:
                    motor.disconnect()
                except Exception:
                    pass
                try:
                    if hasattr(motor, "returnToZero"):
                        motor.returnToZero()
                except Exception:
                    pass


bsc = BSC()
