from backend.smartdot.SmartDotConnectionManager import SmartDotConnectionManager
# from backend.models.DataController import DataController
from backend.cloud_api.CloudAPI import CloudAPI
# from backend.models.SessionData import SessionData
import utils
from backend.motors.SimMotor import SimMotor
if utils.is_raspberry_pi_5():
    from backend.motors.USBBDCMotor import USBBDCMotor #UNCOMMENT AFTER STEPPER
if utils.is_raspberry_pi_5():
    from backend.motors.StepMotor import StepMotor #uncomment when stepper works


class MotorData:
    def __init__(self, dt, length, spin, tilt, angle):
        self.spin = spin
        self.tilt = tilt
        self.angle = angle
        self.dt = dt
        self.length = length

        
class BSC:
    def __init__(self):
        self.smartdotConnectionManager = SmartDotConnectionManager()
        self.cloud_api = CloudAPI()
        self.session = None
        self.data_controller = None
        if utils.is_raspberry_pi_5():
            self.motor1 = USBBDCMotor() # UNCOMMENT AFTER STEPPER
            #self.motor1 = SimMotor(1)
            self.motor2 = StepMotor(26) #Uncomment when step working
            #self.motor2 = SimMotor(2)
        else:
            self.motor1 = SimMotor(2)
            self.motor2 = SimMotor(2)
        self.motor3 = SimMotor(3)

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


bsc = BSC()
