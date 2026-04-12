from .iMotor import iMotor
from gpiozero import PWMOutputDevice
import time

MIN_THR = 1050
MID_THR = 1500
MAX_THR = 2000
STEP = 2   # ~2 per-mille
FREQ = 50
#ARM_TIME_S = 0.15
#pi = pigpio.pi()
ARM_TIME_S = 3.0


class BDCMotor(iMotor):
    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 26
    motor = None

    DEFAULT_KP = 0.1
    DEFAULT_DUTY_CYCLE_SCALE = 0.000043333333

    def __init__(self, GPIOPin: int):
        self.GPIO_Pin = GPIOPin
        self._Kp = self.DEFAULT_KP
        self._duty_cycle_scale = self.DEFAULT_DUTY_CYCLE_SCALE

        #print(f"pin: {self.GPIO_Pin}")
        # Initialize software PWM using gpiozero.  On non‑Raspberry Pi
        # environments (unit tests or desktop development) gpiozero will
        # complain about missing pin factories.  Rather than forcing the
        # caller to mock out ``PWMOutputDevice`` we provide a lightweight
        # fallback that mimics enough of the real API so that the rest of
        # the class can operate without hardware.
        try:
            self.motor = PWMOutputDevice(GPIOPin, frequency=FREQ)
        except Exception as exc:  # covers BadPinFactory and others
            # log so tests (and developers) can understand why we chose the
            # dummy implementation.
            print(f"BDCMotor: could not create real PWM device ({exc}); using dummy")
            class _DummyPWM:
                def __init__(self, pin, frequency=None):
                    self.pin = pin
                    self.frequency = frequency
                    self.value = 0.0
                def close(self):
                    pass
            self.motor = _DummyPWM(GPIOPin, frequency=FREQ)
        time.sleep(1)
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
        # return lo if x < lo else hi if x > hi else x
        return max(lo, min(x, hi))
    # ---------------- PULSE CONTROL ----------------

    def set_pulse(self):
        if self.motor:
            # ESC expects 1050–2000 µs, 50 Hz => duty 0.0525–0.1
            duty = (self.currSpeed - MIN_THR) / (MAX_THR - MIN_THR)  # 0..1
            v1 = duty
            duty = duty * (0.1 - 0.05) + 0.05  # Map to ESC duty range
            v2 = duty
            clamp_val = self.clamp(duty, 0.051, 0.1)
            print(f"clamp value: {clamp_val}")
            self.motor.value = float(clamp_val)
            print(f"clamp: {self.clamp(duty, 0.05, 0.1)}")
            print(f"v1 {v1} v2 {v2} self.motor duty value: {self.motor.value}")


    # ---------------- ARM / DISARM ----------------
    def arm(self):
        print(f"this is motor. :{self.motor}")
        self.currSpeed = MIN_THR

        #self.motor.value = 0.0
        #time.sleep(1)

        #print("Full speed")
        #self.motor.value = 0.1
        #time.sleep(2)

        print("Low speed")
        #self.motor.value = 0.05
        #time.sleep(2)

        #print("Half speed")
        #self.motor.value = .075
        #time.sleep(4)
        self.set_pulse()
        #self.motor.value = 0.075
        self.motor.value = 0.06
        print(f"THIS IS MOTOR IN ARMs.: {self.motor.value}")
        time.sleep(.25)
        #self.motor.value = 0.05
        print("armed")

    def disarm(self):
        self.targetSpeed = MIN_THR
        self.rampDown()
        self.currSpeed = 0
        self.set_pulse()
        print("disarmed")

    # ---------------- MOTOR CONTROL ----------------
    def start(self, rpm=1):
        ''' #COMMENTED OUT FOR NOW, RESOLVE LATER WHEN BLDC MOTOR SPINNING (WAIT FOR GABE)
        if not self.pi.connected:
            sys.stderr.write(
                "pigpio daemon not running.\n"
                "Start it with:  sudo systemctl start pigpiod\n"
                "Or enable it:  sudo systemctl enable --now pigpiod\n"
            )
            sys.exit(1)
        else :
            self.arm(self)
            #time.sleep(2)        #test with no sleep
        '''
        self.arm()
        time.sleep(.5)

    def stop(self):
        self.disarm()
        self.disconnect(self.GPIO_Pin)

    def returnToZero(self):
        # Treat zero as minimum throttle for ESC-style PWM control.
        self.targetSpeed = MIN_THR
        if self.currSpeed > self.targetSpeed:
            self.rampDown()
        else:
            self.currSpeed = self.targetSpeed
            try:
                self.set_pulse()
            except Exception:
                pass

    def setCurrentPositionZero(self):
        # No position encoder; align internal state to the zero-throttle baseline.
        self.currSpeed = MIN_THR
        self.targetSpeed = MIN_THR
        try:
            self.set_pulse()
        except Exception:
            pass

    def changeSpeed(self, dutyCycle: float):
        self.targetSpeed = self.clamp(dutyCycle / 12.0 + 1119.5, MIN_THR, MAX_THR)
        if self.targetSpeed >= 1120.0:
            self.targetSpeed += 5.0
        #print(f"new target speed: {self.targetSpeed}")
        if self.targetSpeed > self.currSpeed:
            self.rampUp()
        else:
            self.rampDown()

    def getCurrentSpeed(self):
        return self.currSpeed

    def rampUp(self):
        # print("ramping up to speed")
        while self.currSpeed < self.targetSpeed:
            self.currSpeed += STEP
            if self.currSpeed > self.targetSpeed:
                self.currSpeed = self.targetSpeed
            self.set_pulse()
            time.sleep(0.05)
        # print(f"current speed: {self.currSpeed}")


    def rampDown(self):
        # print("ramping down to speed")
        while self.currSpeed > self.targetSpeed:
            self.currSpeed -= STEP
            if self.currSpeed < self.targetSpeed:
                self.currSpeed = self.targetSpeed
            self.set_pulse()
            time.sleep(0.05)
        # print(f"current speed: {self.currSpeed}")

    def setDutyCycle(self, dutyCycle: int):
        # Direct duty cycle (0-100%)
        #if self.motor:
         #   self.motor.value = self.clamp(dutyCycle / 100.0, 0.0, 1.0)
        pass