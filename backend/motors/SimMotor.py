from .iMotor import iMotor
import random
import time


class SimMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26

    DEFAULT_KP = 1.0
    DEFAULT_KI = 0.0
    DEFAULT_KD = 0.0
    DEFAULT_DUTY_CYCLE_SCALE = 0.000043333333

    def __init__(
        self,
        GPIOPin: int,
        mode: str = "vesc",
        max_speed: float = 600.0,
        time_constant: float = 0.1,
        noise_std: float = 1.5,
    ):
        self.GPIO_Pin = GPIOPin
        self._Kp = self.DEFAULT_KP
        self._Ki = self.DEFAULT_KI
        self._Kd = self.DEFAULT_KD
        self._duty_cycle_scale = self.DEFAULT_DUTY_CYCLE_SCALE

        self.mode = mode
        self.max_speed = max_speed
        self.time_constant = time_constant
        self.noise_std = noise_std

        # Configurable tuning parameters (aligned with USBBDCMotor)
        self.target_speed_min = 0.0
        self.target_speed_max = max_speed
        self.integral_limit = 1200.0
        self.ramp_step = 12.0

        self._enabled = False
        self._last_update = time.time()
        self.targetSpeed = 0.0
        self.currSpeed = 0.0

    def connect(self, GPIOPin: int = None):
        self.GPIO_Pin = GPIOPin if GPIOPin is not None else self.GPIO_Pin
        self._enabled = True
        return True

    def disconnect(self, GPIOPin: int = None):
        self._enabled = False
        return True

    # Turns on Motor at Specified Power (Duty Cycle)
    def start(self, dutyCycle=0):
        self._enabled = True
        self.targetSpeed = 0.0
        self.currSpeed = 0.0
        self._last_update = time.time()

    def stop(self):
        self.targetSpeed = 0.0
        self.currSpeed = 0.0
        self._enabled = False
        self._last_update = time.time()

    def returnToZero(self):
        self.targetSpeed = 0.0
        self.currSpeed = 0.0
        self._last_update = time.time()

    def setCurrentPositionZero(self):
        # Sim motor has no positional encoder; treat zero as stopped.
        self.targetSpeed = 0.0
        self.currSpeed = 0.0
        self._last_update = time.time()

    def _update_sim(self):
        """Advance the simulated speed toward the target speed."""
        now = time.time()
        dt = max(0.05, now - self._last_update)
        self._last_update = now

        if self.mode in ("instant", "step"):
            self.currSpeed = self.targetSpeed
            return self.currSpeed

        # Simple first-order response: approach the target speed smoothly.
        alpha = dt / max(dt + self.time_constant, 1e-6)
        self.currSpeed += (self.targetSpeed - self.currSpeed) * alpha
        self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

        if self.noise_std > 0.0 and self.currSpeed > 0:
            self.currSpeed += random.gauss(0.0, self.noise_std)
            self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

        return self.currSpeed

    def changeSpeed(self, dutyCycle: float, isShotMode: bool):
        """Set the simulated motor target speed and update the current speed.

        This mirrors the USBBDCMotor semantic where `dutyCycle` is treated as the
        target RPM value. The simulator responds smoothly unless it is in
        instant or step mode.
        """
        new_target = max(self.target_speed_min, min(dutyCycle, self.target_speed_max))
        self._enabled = True
        self.targetSpeed = new_target

        if self.mode == "step":
            self.currSpeed = new_target
            return

        if self.mode == "instant":
            self.currSpeed = new_target
        else:
            self._update_sim()

    def rampUp(self, step: float = 12.0):
        """Increase the current simulated speed toward the target speed."""
        if self.mode == "step":
            return
        if self.currSpeed < self.targetSpeed:
            self.currSpeed = min(self.currSpeed + step, self.targetSpeed)
            self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

    def rampDown(self, step: float = 12.0):
        """Decrease the current simulated speed toward the target speed."""
        if self.mode == "step":
            return
        if self.currSpeed > self.targetSpeed:
            self.currSpeed = max(self.currSpeed - step, self.targetSpeed)
            self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

    def setTargetSpeed(self, targetSpeed: float):
        self.targetSpeed = max(self.target_speed_min, min(targetSpeed, self.target_speed_max))

    def setTargetPower(self, targetPower: float):
        self.targetPower = targetPower

    def getCurrentSpeed(self):
        """Return the current simulated motor speed, updating internal state."""
        if not self._enabled:
            self._enabled = True
        return self._update_sim()

    @property
    def Kp(self) -> float:
        return self._Kp

    @Kp.setter
    def Kp(self, value: float):
        if value < 0.0:
            raise ValueError("Kp must be non-negative")
        self._Kp = value

    @property
    def Kd(self) -> float:
        return self._Kd

    @Kd.setter
    def Kd(self, value: float):
        if value < 0.0:
            raise ValueError("Kd must be non-negative")
        self._Kd = value

    @property
    def Ki(self) -> float:
        return self._Ki

    @Ki.setter
    def Ki(self, value: float):
        if value < 0.0:
            raise ValueError("Ki must be non-negative")
        self._Ki = value

    @property
    def duty_cycle_scale(self) -> float:
        return self._duty_cycle_scale

    @duty_cycle_scale.setter
    def duty_cycle_scale(self, value: float):
        if value <= 0.0:
            raise ValueError("duty_cycle_scale must be positive")
        self._duty_cycle_scale = value

    def set_Kp(self, kp: float):
        self.Kp = kp

    def set_duty_cycle_scale(self, scale: float):
        self.duty_cycle_scale = scale

    def getTargetSpeed(self):
        return self.targetSpeed

    def getTargetPower(self):
        return self.targetPower
