from .iMotor import iMotor
from gpiozero import Device, LED, PWMOutputDevice
from gpiozero.pins.mock import MockFactory, MockPWMPin
import random
import time


class SimMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26

    DEFAULT_KP = 1.0
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
        factory = MockFactory()
        Device.pin_factory = MockFactory(pin_class=MockPWMPin)
        motor = PWMOutputDevice(self.GPIO_Pin)

        self.GPIO_Pin = GPIOPin
        self._Kp = self.DEFAULT_KP
        self._Kd = self.DEFAULT_KD
        self._duty_cycle_scale = self.DEFAULT_DUTY_CYCLE_SCALE

        self.mode = mode
        self.max_speed = max_speed
        self.time_constant = time_constant
        self.noise_std = noise_std

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

    def _update_sim(self):
        now = time.time()
        dt = max(1e-6, now - self._last_update)
        self._last_update = now

        if self.mode == "instant":
            self.currSpeed = self.targetSpeed
            return self.currSpeed
        elif self.mode == "step":
            # legacy behavior: direct assignment to preserve compatibility
            self.currSpeed = self.targetSpeed
            return self.currSpeed
        else:
            # first-order dynamic response to simulate inertia and controller action
            alpha = 1.0 - pow(2.718281828459045, -dt / max(1e-6, self.time_constant))
            self.currSpeed += (self.targetSpeed - self.currSpeed) * alpha
            self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

            if self.noise_std > 0.0 and self.currSpeed > 0:
                self.currSpeed += random.gauss(0.0, self.noise_std)
                self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

        return self.currSpeed

        return self.currSpeed

    def changeSpeed(self, dutyCycle: float, isShotMode: bool):
        # Accept the same command range as USBBDCMotor (0-1200), clamp it.
        new_target = max(0.0, min(dutyCycle, 1200.0))

        # Ensure we can read values without requiring explicit start() first.
        self._enabled = True

        if self.mode == "step":
            # Step motor compatibility path remains in BSC-style angle semantics.
            self.currSpeed = new_target
            self.targetSpeed = new_target
            return

        self.targetSpeed = new_target
        if self.mode == "instant":
            self.currSpeed = new_target
        else:
            self._update_sim()

    def rampUp(self, step: float = 12.0):
        if self.mode == "step":
            return

        if self.targetSpeed <= self.currSpeed:
            return

        # Naive ramp towards target, respecting the max speed and preserving dynamics.
        self.currSpeed = min(self.targetSpeed, self.currSpeed + step)
        self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

    def rampDown(self, step: float = 12.0):
        if self.mode == "step":
            return

        if self.targetSpeed >= self.currSpeed:
            return

        self.currSpeed = max(self.targetSpeed, self.currSpeed - step)
        self.currSpeed = max(0.0, min(self.currSpeed, self.max_speed))

    def setTargetSpeed(self, targetSpeed: float):
        self.targetSpeed = max(0.0, min(targetSpeed, 1200.0))

    def setTargetPower(self, targetPower: float):
        self.targetPower = targetPower

    def getCurrentSpeed(self):
        # Allow current speed reads even if start() hasn't been explicitly called,
        # for compatibility with existing tests and control flows.
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
