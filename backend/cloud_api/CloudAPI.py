import requests
import json
from logs.logger_config import get_logger
from .iCloud import iCloud
# Get logger for this module
logger = get_logger(__name__)
import datetime as dt
from backend.models.SessionData import SessionData
from backend.models.DiagnosticScriptData import DiagnosticScriptData

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
            print(f"Data: {result['data']}")
            return result['status_code'], result['data']

    def post_session_data(self, session_data):
        """
        Submit session data to the cloud API.
        
        Args:
            session_data: SessionData instance
        """
        logger.info("post_session_data called - stub implementation")
        url = "https://api.revmetrix.io/api/posts/PostPiSessions"
        result = APIUtils.make_post_request(url, session_data)
        return result
    

    def get_sessions_in_time_range(self, start_time, end_time):
        """
        Get sessions in a time range. (0,0) means all sessions
        
        Args:
            start_time: Start time
            end_time: End time
        """
        logger.info("get_sessions_in_time_range called - stub implementation")
        url = "https://api.revmetrix.io/api/gets/GetAllPiSessions"
        result = APIUtils.make_post_request(url, {"start_time": start_time, "end_time": end_time})
        return result

    def get_all_diagnostic_script_data_by_session(self, session_id):
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
        pass

    def get_shot_script_data_by_session(self, session_id):
        """
        Get shot script data by session.
        
        Args:
            session_id: Session ID
        """
        pass

    def post_shot_script_data(self, shot_script_data, session_id):
        """
        Post shot script data to the cloud API.
        
        Args:
            shot_script_data: ShotScriptData instance
            session_id: Session ID
        """
        pass

    def submit_shot_mode_data(self, session_data, smartdot_data, shot_script_data, encoder_data):
            """
            Submit shot mode data to the cloud API.
            
            Args:
                session_data: SessionData instance
                smartdot_data: SmartDotData instance
                shot_script_data: ShotScriptData instance
                encoder_data: EncoderData instance
            """
            logger.info("submit_shot_mode_data called - stub implementation")
            # TODO: Implement shot mode data submission
            pass
        
    def submit_diagnostic_mode_data(self, session_data, smartdot_data, diagnostic_script_data, encoder_data):
        """
        Submit diagnostic mode data to the cloud API.
        
        Args:
            session_data: SessionData instance
            smartdot_data: SmartDotData instance
            diagnostic_script_data: DiagnosticScriptData instance
            encoder_data: EncoderData instance
        """
        logger.info("submit_diagnostic_mode_data called - stub implementation")
        # TODO: Implement diagnostic mode data submission
        pass




if __name__ == "__main__":
    

    print(dt.datetime.now().isoformat())
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
    print(result)