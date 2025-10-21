from abc import ABCMeta, abstractmethod

class iMotor(metaclass=ABCMeta): 
    motorID : int
    currSpeed : float
    targetSpeed : float
    targetPower : float

    @abstractmethod
    def __init__(self, GPIOPin : int): 
        pass

    @abstractmethod
    def connect(self, GPIOPin : int):
        pass

    @abstractmethod
    def disconnect(self, GPIOPin : int):
        pass

    # Turns on Motor at Specified Power (Duty Cycle)
    @abstractmethod
    def start(self, dutyCycle = 100):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def changeSpeed(self, dutyCycle : int):
        pass

    @abstractmethod
    def int getCurrentSpeed(self):
        pass

    @abstractmethod
    def rampUp(self):
        pass