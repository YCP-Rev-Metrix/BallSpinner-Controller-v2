from .iMotor import iMotor
from gpiozero import PWMOutputDevice
import time

MIN_THR = 0.050
MID_THR = 0.075
MAX_THR = 0.100
STEP = 0.002   # ~2 per-mille
FREQ = 50

class BDCMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26; #GPIO Pin for the Motor
    motor = PWMOutputDevice(GPIO_Pin, frequency=FREQ)

    def clamp(x, lo, hi):
        return max(lo, min(hi, x))
     
    def __init__(self, GPIOPin : int):
        thr = MID_THR
        self.motor.value = 0.0


    # Turns on Motor at Specified Power (Duty Cycle)
    def start(self, dutyCycle = 100):
        pass

    def stop(self):
        pass

    def changeSpeed(self, dutyCycle : int):
        dutyCycle = self.clamp(dutyCycle, 0, 100)

    def int getCurrentSpeed(self):
        pass

    def rampUp(self):
        pass

    def setDutyCycle(self, dutyCycle : int):
        pass