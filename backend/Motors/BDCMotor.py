from .iMotor import iMotor
from gpiozero import PWMOutputDevice
import time

MIN_THR = 1050
MID_THR = 1500
MAX_THR = 2000
STEP = 2   # ~2 per-mille
FREQ = 50
ARM_TIME_S = 3.0


class BDCMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26
    motor = None

    def __init__(self, GPIOPin: int):
        self.GPIO_Pin = GPIOPin
        #print(f"pin: {self.GPIO_Pin}")
        # Initialize software PWM using gpiozero
        self.motor = PWMOutputDevice(GPIOPin, frequency=FREQ)
        self.start()

    # ---------------- CONNECT / DISCONNECT ----------------
    def connect(self, GPIOPin: int):
        # No special hardware setup needed with gpiozero
        pass

    def disconnect(self, GPIOPin: int):
        if self.motor:
            self.motor.close()
        print(f"Motor on GPIO{GPIOPin} disconnected.")

    # ---------------- UTILITY ----------------
    def clamp(self, x, lo, hi):
        return lo if x < lo else hi if x > hi else x

    # ---------------- PULSE CONTROL ----------------
    def set_pulse(self):
        if self.motor:
            # ESC expects 1050–2000 µs, 50 Hz => duty 0.0525–0.1
            duty = (self.currSpeed - MIN_THR) / (MAX_THR - MIN_THR)  # 0..1
            duty = duty * (0.1 - 0.05) + 0.05  # Map to ESC duty range
            self.motor.value = self.clamp(duty, 0.05, 0.1)
            print(f"self.motor duty value: {self.motor.value}")


    # ---------------- ARM / DISARM ----------------
    def arm(self):
        self.currSpeed = MIN_THR
        print("Full speed")
        self.motor.value = .1
        time.sleep(2)

        print("Low speed")
        self.motor.value = .05
        time.sleep(2)

        #print("Half speed")
        #self.motor.value = .075
        #time.sleep(4)
        #self.set_pulse()
        # time.sleep(ARM_TIME_S)
        self.motor.value = .05
        print("armed")

    def disarm(self):
        self.targetSpeed = MIN_THR
        self.rampDown()
        self.currSpeed = 0
        self.set_pulse()
        print("disarmed")

    # ---------------- MOTOR CONTROL ----------------
    def start(self, rpm=1):
        self.arm()
        time.sleep(.5)

    def stop(self):
        self.disarm()
        self.disconnect(self.GPIO_Pin)

    def changeSpeed(self, dutyCycle: float):
        self.targetSpeed = self.clamp(dutyCycle / 12.0 + 1119.5, MIN_THR, MAX_THR)
        if self.targetSpeed >= 1120.0:
            self.targetSpeed += 5.0
        if self.targetSpeed > self.currSpeed:
            self.rampUp()
        else:
            self.rampDown()

    def getCurrentSpeed(self):
        return self.currSpeed

    def rampUp(self):
        while self.currSpeed < self.targetSpeed:
            self.currSpeed += STEP
            if self.currSpeed > self.targetSpeed:
                self.currSpeed = self.targetSpeed
            self.set_pulse()
            time.sleep(0.01)

    def rampDown(self):
        while self.currSpeed > self.targetSpeed:
            self.currSpeed -= STEP
            if self.currSpeed < self.targetSpeed:
                self.currSpeed = self.targetSpeed
            self.set_pulse()
            time.sleep(0.01)

    def setDutyCycle(self, dutyCycle: int):
        # Direct duty cycle (0-100%)
        if self.motor:
            self.motor.value = self.clamp(dutyCycle / 100.0, 0.0, 1.0)
