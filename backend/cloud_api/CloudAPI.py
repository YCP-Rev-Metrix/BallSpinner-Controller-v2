import requests
import json
from backend.models.ShotScriptData import ShotScriptData
from logs.logger_config import get_logger
from .iCloud import iCloud
# Get logger for this module
logger = get_logger(__name__)
import datetime as dt
from backend.models.SessionData import SessionData
from backend.models.DiagnosticScriptData import DiagnosticScriptData
from backend.models.ShotScriptData import ShotScriptData
from backend.models.SmartDotData import SmartDotData
from backend.models.EncoderData import EncoderData
from backend.models.HeatData import HeatData

from .APIUtils import APIUtils

class CloudAPI(iCloud):
    def __init__(self) -> None:
         super().__init__()
         
    def get_test_data(self):
        logger.info("Starting API test data request")
        url = "https://api.revmetrix.io/api/gets/Test"
        result = APIUtils.make_get_request(url)
        
        if 'error' in result:
            logger.error(f"API request failed: {result['error']}")
            return result['status_code'], result['error']
        else:
            logger.info("API request successful")
            logger.debug(f"Retrieved data: {result['data']}")
            #print(f"Data: {result['data']}")
            return result['status_code'], result['data']

    def post_session_data(self, session_data: SessionData):
        """
        Submit session data to the cloud API.
        
        Args:
            session_data: SessionData instance
        """
        logger.info("post_session_data called")
        #print(session_data.get_id())
        data = []
        data.append({
            "id": session_data.get_id(),
            "timeStamp": session_data.timeStamp,
            "name": session_data.name,
            "isShotMode": session_data.isShotMode
        })
        url = "https://api.revmetrix.io/api/posts/PostPiSessions"
        result = APIUtils.make_post_request(url, data=data)
        return result
    

    def get_sessions_in_time_range(self, start_time, end_time):
        """
        Get sessions in a time range. (0,0) means all sessions
        
        Args:
            start_time: Start time
            end_time: End time
        """
        logger.info("get_sessions_in_time_range called")
        url = "https://api.revmetrix.io/api/gets/GetAllPiSessions"
        #print(f"Getting sessions in time range: {start_time} to {end_time}")
        result = APIUtils.make_post_request(url, {"rangeStart": start_time, "rangeEnd": end_time})
        return result

    def get_diagnostic_script_data_by_session(self, session_id):
        """
        Get all diagnostic script data by session.
        
        Args:
            session_id: Session ID
        """
        logger.info(f"Getting all Diagnostic Script Data by sessionID: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiDiagnosticScriptBySession"
        result = APIUtils.make_get_request(url, url_params={"sessionId": session_id})
        return result

    def post_diagnostic_script_data(self, diagnostic_script_data_list: DiagnosticScriptData, session_id):
        """
        Post diagnostic script data to the cloud API.
        
        Args:
            diagnostic_script_data: DiagnosticScriptData instance
            session_id: Session ID
        """
        logger.info(f"Posting Diagnostic Script Data by sessionID: {session_id}")
        url = "https://api.revmetrix.io/api/posts/PostPiDiagnosticScripts"
        #Check the formatting of the diagnostic script data list
        #Expected format is [{},{},{"id": 0, "sessionId": 0, "time", "motorID", "instruction"}]
        data = []
        for i in diagnostic_script_data_list:
            data.append({
                "id": 0,
                "sessionId": session_id,
                "time": i.time,
                "motorID": i.motor_id,
                "instruction": i.instruction
            })
        
        result = APIUtils.make_post_request(url, data=data)
        return result

    def get_shot_script_data_by_session(self, session_id):
        """
        Get shot script data by session.
        
        Args:
            session_id: Session ID
        """
        logger.info(f"Getting Shot Script data for sesionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiShotsBySession"
        result = APIUtils.make_get_request(url=url, url_params={"sessionId": session_id})
        #print(result)
        return result

    def post_shot_script_data(self, shot_script_data: ShotScriptData, session_id):
        """
        Post shot script data to the cloud API.
        
        Args:
            shot_script_data: ShotScriptData instance
            session_id: Session ID
        """

        logger.info(f"Posting shot script data for the current session: {session_id}")

        #Convert the list into dictionary format for the api
        data = []
        for i in shot_script_data:
            data.append({
                "id": 0,
                "sessionId": session_id,
                "time": i.time,
                "rpm": i.rpm,
                "angleDegrees": i.angleDeg,
                "tiltDegrees": i.tiltDeg
            })
        url = "https://api.revmetrix.io/api/posts/PostPiShot"
        result = APIUtils.make_post_request(url=url, data=data)
        #print(result)
        return result


  

    def get_smartdot_data(self, session_id):   
        """
        Get smartdot data by session.
        
        Args:
            session_id: Session ID
        
        """
        logger.info(f"Getting Smartdot data for sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiSmartDotDataBySession"
        result = APIUtils.make_get_request(url, url_params={"sessionId": session_id})
        #print(result)
        return result

    def post_smartdot_data(self, smart_dot_data: SmartDotData, session_id):
        """
        Post smartdot data to the cloud API.
        
        Args:
            session_id: Session ID
        """
        logger.info(f"Posting Smartdot data for sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/posts/PostPiSmartDotData"

        #Gather the smartdot data from the data controller.
        data = []
        # #print(f"Smartdot data: {smart_dot_data}")
        for i in smart_dot_data:
            data.append(
                  {
                    "id": 0,
                    "sessionId": session_id,
                    "time": i.time,
                    "dataSelector": i.data_selector,
                    "xL_X": i.accelerometer_x,
                    "xL_Y": i.accelerometer_y,
                    "xL_Z": i.accelerometer_z,
                    "gY_X": i.gyroscope_x,
                    "gY_Y": i.gyroscope_y,
                    "gY_Z": i.gyroscope_z,
                    "mG_X": i.magnetometer_x,
                    "mG_Y": i.magnetometer_y,
                    "mG_Z": i.magnetometer_z,
                    "lt": i.light
                }
            )
        result = APIUtils.make_post_request(url=url, data=data)
        #print(result)
        return result

    def get_encoder_data(self, session_id):
        logger.info(f"Getting encoder data by sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiEncoderDataBySession"
        result = APIUtils.make_get_request(url=url, url_params={"sessionId": session_id})
        #print(result)
        return result
    def post_encoder_data(self, encoder_data: EncoderData, session_id):
        logger.info(f"Posting encoder data by sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/posts/PostPiEncoderData"

        data = []
        for i in encoder_data:
            data.append({
                "id": 0,
                "sessionId": session_id,
                "time": i.time,
                "pulses": i.pulses,
                "motorId": i.motor_id
            })
        result = APIUtils.make_post_request(url=url, data=data)
        #print(result)
        return result
    def get_heat_data(self, session_id):
        logger.info(f"Getting Heat data by sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiHeatDataBySession"
        result = APIUtils.make_get_request(url=url, url_params={"sessionId": session_id})
        #print(result)
        return result
    def post_heat_data(self, heat_data: HeatData, session_id):
        logger.info(f"Posting heat data by sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/posts/PostPiHeatData"
        data = []
        for i in heat_data:
            data.append({
                "id": 0,
                "sessionId": session_id,
                "time": i.time,
                "value": i.value,
                "motorId": i.motor_id
            })
        result = APIUtils.make_post_request(url=url, data=data)
        #print(result)
        return result
if __name__ == "__main__":
    

    #print(dt.datetime.now().isoformat())
    cloud_api = CloudAPI()
    # session_data = SessionData(id=-1, timeStamp=datetime.now(), name="Test Session", isShotMode=True)
    data = [
        {"id": -1,
        "timeStamp": dt.datetime.now().isoformat(),
        "name": "Test Session",
        "isShotMode": True,
        }
    ]

    result = cloud_api.post_session_data(data)
    #print(result)