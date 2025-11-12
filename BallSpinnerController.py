#from backend.motors.BDCMotor import BDCMotor
#from backend.motors.SimMotor import SimMotor
from backend.motors.iMotor import iMotor
from backend.smartdot.iSmartDot import iSmartDot
from backend.cloud_api.iCloud import iCloud
from logs.logger_config import get_logger

logger = get_logger(__name__)



class BallSpinnerController():


    motor = [] #TODO: the conditional import, and then instantiate the correct motor once merged
               #with main branch
    #iAuxSensor[int] sensor
    #SD = iSmartDot() #TODO: the conditional import, and then instantiate the correct smartdot
                      #once merged with main branch
    #cloud = iCloud() #TODO: same as above
    
    def __init__(self):
        # put startup code here rather than in frontend. once refactor is complete,
        # remove the two lines below.
        self.isModeShot = False
        self.mode = "diagnostic"

    def openMode(self, mode: int):
        #print(f"Switching page to {mode}")
        if mode == 1: # DIAGNOSTIC
            self.isModeShot = False
            print("Diagnostic mode opened")
        elif mode == 2: # SHOT
            self.isModeShot = True
            print("Shot mode opened")
        elif mode == 3: # ANALYSIS
            self.isModeShot = False
            print("Analysis mode opened")
            # ALSO OPEN ANALYSIS MODE HERE WHEN IMPLEMENTED
    