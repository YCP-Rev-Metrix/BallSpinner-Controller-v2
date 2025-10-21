from .iMotor import iMotor
import RPi.GPIO as GPIO

class BDCMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
     
    def __init__(self, GPIOPin : int):
        pass

    # Turns on Motor at Specified Power (Duty Cycle)
    def start(self, dutyCycle = 100):
        pass

    def stop(self):
        pass

    def changeSpeed(self, dutyCycle : int):
        pass

    def int getCurrentSpeed(self):
        pass

    def rampUp(self):
        pass

    def setDutyCycle(self, dutyCycle : int):
        pass