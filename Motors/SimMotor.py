from .iMotor import iMotor
import RPi.GPIO as GPIO

class SimMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0

    def __init__(self, GPIOPin : int):
        pass

    def connect(self, GPIOPin : int):
        pass

    def disconnect(self, GPIOPin : int):
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

    def setTargetSpeed(self, targetSpeed : float):
        pass

    def setTargetPower(self, targetPower : float):
        pass

    def getCurrentSpeed(self):
        return self.currSpeed

    def getTargetSpeed(self):
        return self.targetSpeed

    def getTargetPower(self):
        return self.targetPower