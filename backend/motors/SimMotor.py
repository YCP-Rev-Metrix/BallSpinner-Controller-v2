from .iMotor import iMotor
from gpiozero import Device, LED, PWMOutputDevice
from gpiozero.pins.mock import MockFactory, MockPWMPin
import random

class SimMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26

    DEFAULT_KP = 0.1
    DEFAULT_DUTY_CYCLE_SCALE = 0.000043333333

    def __init__(self, GPIOPin : int):
        factory = MockFactory()
        Device.pin_factory = MockFactory(pin_class=MockPWMPin)
        motor = PWMOutputDevice(self.GPIO_Pin)
        self._Kp = self.DEFAULT_KP
        self._duty_cycle_scale = self.DEFAULT_DUTY_CYCLE_SCALE

    def connect(self, GPIOPin : int):
        pass

    def disconnect(self, GPIOPin : int = None):
        pass

    # Turns on Motor at Specified Power (Duty Cycle)
    def start(self, dutyCycle = 100):
        #print("Motor started in motor object")
        pass    

    def stop(self):
        pass

    def changeSpeed(self, dutyCycle : int, isShotMode: bool):
        #print("speed changed in motor object")
        self.currSpeed = dutyCycle

    def rampUp(self):
        pass

    def setTargetSpeed(self, targetSpeed : float):
        self.targetSpeed = targetSpeed

    def setTargetPower(self, targetPower : float):
        self.targetPower = targetPower

    def getCurrentSpeed(self):
        return self.currSpeed + random.uniform(-20, 20) # Simulate some noise in the speed measurement

    @property
    def Kp(self) -> float:
        return self._Kp

    @Kp.setter
    def Kp(self, value: float):
        self._Kp = value

    @property
    def duty_cycle_scale(self) -> float:
        return self._duty_cycle_scale

    @duty_cycle_scale.setter
    def duty_cycle_scale(self, value: float):
        self._duty_cycle_scale = value

    def set_Kp(self, kp: float):
        self.Kp = kp

    def set_duty_cycle_scale(self, scale: float):
        self.duty_cycle_scale = scale

    def getTargetSpeed(self):
        return self.targetSpeed

    def getTargetPower(self):
        return self.targetPower