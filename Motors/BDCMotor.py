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

     
    def __init__(self, GPIOPin : int):
        start(self)
        

    def set_pulse(pi):
        pi.set_servo_pulsewidth(PIN, int(currSpeed))

    def arm(pi):
        set_pulse(pi, MIN_THR)
        time.sleep(ARM_TIME_S)

    def disarm(pi):
        set_pulse(pi, 0)

    # Turns on Motor at Specified Power (Duty Cycle)
    def start(self):
        pi = pigpio.pi()
        if not pi.connected:
            sys.stderr.write(
                "pigpio daemon not running.\n"
                "Start it with:  sudo systemctl start pigpiod\n"
                "Or enable it:  sudo systemctl enable --now pigpiod\n"
            )
            sys.exit(1)
        arm(pi)
        time.sleep(2)


    def stop(self):
        disarm(pi)
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
                set_pulse(pi, currSpeed)
                time.sleep(0.01)
            else:
                break

    def setDutyCycle(self, dutyCycle : int):
        pass

        