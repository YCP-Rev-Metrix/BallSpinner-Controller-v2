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
    def changeSpeed(self, dutyCycle : float, isShotMode : bool):
        pass

    @abstractmethod
    def getCurrentSpeed(self):
        pass

    @abstractmethod
    def rampUp(self):
        pass

    @property
    @abstractmethod
    def Kp(self) -> float:
        pass

    @Kp.setter
    @abstractmethod
    def Kp(self, value: float):
        pass

    @property
    @abstractmethod
    def duty_cycle_scale(self) -> float:
        pass

    @duty_cycle_scale.setter
    @abstractmethod
    def duty_cycle_scale(self, value: float):
        pass