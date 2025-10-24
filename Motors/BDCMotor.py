from .iMotor import iMotor
from gpiozero import PWMOutputDevice
import time
import pigpio

MIN_THR = 0.050
MID_THR = 0.075
MAX_THR = 0.100
STEP = 0.002   # ~2 per-mille
FREQ = 50
ARM_TIME_S = 3.0

class BDCMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26; #GPIO Pin for the Motor
    motor = PWMOutputDevice(GPIO_Pin, frequency=FREQ)
    pi = pigpio.pi()
     
    def __init__(self, GPIOPin : int):
        self.start(self)
        
    def connect(self, GPIOPin : int):
        pass

    def disconnect(self, GPIOPin : int):
        pass

    def set_pulse():
        pi.set_servo_pulsewidth(PIN, int(currSpeed))

    def arm():
        currSpeed = MIN_THR
        set_pulse()
        time.sleep(ARM_TIME_S)

    def disarm():
        currSpeed = 0
        self.set_pulse()

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
            self.arm()
            time.sleep(2)


    def stop(self):
        self.disarm()
        pi.stop()

    def changeSpeed(self, dutyCycle : float):
        targetSpeed = self.clamp(dutyCycle/8000+0.05, MIN_THR, MAX_THR)
        rampUp(self)


    def getCurrentSpeed(self):
        return currSpeed

    def rampUp(self):
        while True:
            if currSpeed < targetSpeed:
                currSpeed += STEP
                if currSpeed > targetSpeed:
                    currSpeed = targetSpeed
                self.set_pulse(currSpeed)
                time.sleep(0.01)
            else:
                break

    def setDutyCycle(self, dutyCycle : int):
        pass

        