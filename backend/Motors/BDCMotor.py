from .iMotor import iMotor
from gpiozero import PWMOutputDevice, Device
from gpiozero.pins.native import NativeFactory
import time
import pigpio

MIN_THR = 1050
MID_THR = 1500
MAX_THR = 2000
STEP = 2   # ~2 per-mille
FREQ = 50
ARM_TIME_S = 3.0
pi = pigpio.pi()


class BDCMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26; #GPIO Pin for the Motor
    motor = PWMOutputDevice(GPIO_Pin, frequency=FREQ)
    #motor.pin_factory = NativeFactory()
    pi=pigpio.pi()
    isRunning=True

    def __init__(self, GPIOPin : int):
        self.start(self)
        
    def connect(self, GPIOPin : int):
        pass

    def disconnect(self, GPIOPin : int):
        pass

    def clamp(self, x, lo, hi):
        return lo if x < lo else hi if x > hi else x

    def set_pulse(self):
        pi.set_servo_pulsewidth(self.GPIO_Pin, int(self.currSpeed))

    def arm(self, pi):
        if not self.isRunning :
            pi.start()
            self.isRunning=True
        self.currSpeed = MIN_THR
        self.set_pulse()
        time.sleep(ARM_TIME_S)
        print("armed")

    def disarm(self, pi):
        self.currSpeed = 0
        self.set_pulse()

        pi.stop()
        self.isRunning=False

    # Turns on Motor at Specified Power (Duty Cycle)
    def start(self, rpm=1):
        if not self.pi.connected:
            sys.stderr.write(
                "pigpio daemon not running.\n"
                "Start it with:  sudo systemctl start pigpiod\n"
                "Or enable it:  sudo systemctl enable --now pigpiod\n"
            )
            sys.exit(1)
        else :
            self.arm(self)
            time.sleep(2)


    def stop(self):
        self.disarm(pi)
        print("running pi.stop")
        pi.stop()

    def changeSpeed(self, dutyCycle : float):
        print("Changing speed to ", dutyCycle/12.6315789474+1050) 
        self.targetSpeed = self.clamp(dutyCycle/12.6315789474+1050, MIN_THR, MAX_THR)
        if(self.targetSpeed>self.currSpeed) : self.rampUp() 
        else : self.rampDown()


    def getCurrentSpeed(self):
        return self.currSpeed

    def rampUp(self):
        while True:
            if self.currSpeed < self.targetSpeed:
                self.currSpeed += STEP
                if self.currSpeed > self.targetSpeed:
                    self.currSpeed = self.targetSpeed
                self.set_pulse()
                time.sleep(0.01)
            else:
                break

    def rampDown(self):
        while True:
            if self.currSpeed > self.targetSpeed:
                self.currSpeed -= STEP
                if self.currSpeed < self.targetSpeed:
                    self.currSpeed = self.targetSpeed
                self.set_pulse()
                time.sleep(0.01)
            else:
                break

    def setDutyCycle(self, dutyCycle : int):
        pass

        