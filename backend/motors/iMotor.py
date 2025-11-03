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
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def changeSpeed(self, dutyCycle : float):
        pass

    @abstractmethod
    def getCurrentSpeed(self):
        pass

    @abstractmethod
    def rampUp(self):
        pass