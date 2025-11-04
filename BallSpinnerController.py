from backend.motors.BDCMotor import BDCMotor
from backend.motors.SimMotor import SimMotor
from backend.motors.iMotor import iMotor
from backend.smartdot.iSmartDot import iSmartDot
from backend.cloud_api.iCloud import iCloud

class BallSpinnerController():
    motor[] = iMotor[3]
    #iAuxSensor[int] sensor
    #SD = iSmartDot()
    cloud = iCloud()