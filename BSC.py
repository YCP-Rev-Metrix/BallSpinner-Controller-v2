from backend.smartdot.SmartDotConnectionManager import SmartDotConnectionManager
# from backend.models.DataController import DataController
from backend.cloud_api.CloudAPI import CloudAPI
# from backend.models.SessionData import SessionData
import utils
import random

try:
    from backend.motors.SimMotor import SimMotor
except ModuleNotFoundError:
    class SimMotor:
        def __init__(self, GPIOPin: int):
            self.currSpeed = 0.0
            self.targetSpeed = 0.0
            self.targetPower = 0.0

        def connect(self, GPIOPin: int):
            pass

        def disconnect(self, GPIOPin: int = None):
            pass

        def start(self, dutyCycle=100):
            self.currSpeed = float(dutyCycle)

        def stop(self):
            self.currSpeed = 0.0

        def changeSpeed(self, dutyCycle: int, isShotMode: bool):
            self.currSpeed = float(dutyCycle)

        def rampUp(self):
            pass

        def setTargetSpeed(self, targetSpeed: float):
            self.targetSpeed = targetSpeed

        def setTargetPower(self, targetPower: float):
            self.targetPower = targetPower

        def getCurrentSpeed(self):
            return self.currSpeed + random.uniform(-20, 20)

        def getTargetSpeed(self):
            return self.targetSpeed

        def getTargetPower(self):
            return self.targetPower
if utils.is_raspberry_pi_5():
    from backend.motors.USBBDCMotor import USBBDCMotor #UNCOMMENT AFTER STEPPER
    import lgpio
if utils.is_raspberry_pi_5():
    from backend.motors.StepMotor import StepMotor #uncomment when stepper works
    import lgpio


class MotorData:
    def __init__(self, dt, length, spin, tilt, angle):
        self.spin = spin
        self.tilt = tilt
        self.angle = angle
        self.dt = dt
        self.length = length
        self.connected = True

        
class BSC:
    def __init__(self):
        self.smartdotConnectionManager = SmartDotConnectionManager()
        self.cloud_api = CloudAPI()
        self.session = None
        self.data_controller = None
        # Diagnostic sampling interval (milliseconds) used by UI pages
        self.diagnostic_sample_interval_ms = 30
        

        if utils.is_raspberry_pi_5():
            self.h = lgpio.gpiochip_open(0)
            # motor1 = spin/RPM motor (BLDC via USB)
            self.motor1 = USBBDCMotor() # UNCOMMENT AFTER STEPPER
            #self.motor1 = SimMotor(1)
            # motor2 = tilt-angle stepper (now using earlier motor3 pins)
            # motor3 = assembly-angle stepper (now using earlier motor2 pins)
            self.motor2 = StepMotor(27, 17, self.h,5, False) 
            self.motor3 = StepMotor(23, 24, self.h,6, False) 
            #self.motor2 = SimMotor(2)
        else:
            # when simulating all three motors are mocks; names are logical
            self.motor1 = SimMotor(2)
            self.motor2 = SimMotor(2)
            self.motor3 = SimMotor(2) #222 fun haha

    def get_smartdotConnectionManager(self):
        return self.smartdotConnectionManager

    def get_cloud_api(self):
        return self.cloud_api

    def get_session(self):
        return self.session

    def set_session(self, session):
        self.session = session

    def get_data_controller(self):
        return self.data_controller
        
    def set_data_controller(self, data_controller):
        self.data_controller = data_controller

    def disconnect_all_motors(self):
        self.motor1.disconnect()
        self.motor2.disconnect()
        self.motor3.disconnect()
        if utils.is_raspberry_pi_5():
            lgpio.gpiochip_close(self.h)
        self.connected = False
        print("All motors disconnected!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


bsc = BSC()
