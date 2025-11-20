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
from PyQt6.QtCore import QEventLoop

from .APIUtils import APIUtils

class CloudAPI(iCloud):
    def __init__(self) -> None:
         super().__init__()
         self._active_workers = []  # Store workers to prevent garbage collection
         
    def get_test_data(self):
        logger.info("Starting API test data request")
        url = "https://api.revmetrix.io/api/gets/Test"
        
        # Create async worker
        worker = APIUtils.make_get_request_async(url)
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        if 'error' in result:
            logger.error(f"API request failed: {result['error']}")
            return result['status_code'], result['error']
        else:
            logger.info("API request successful")
            logger.debug(f"Retrieved data: {result['data']}")
            print(f"Data: {result['data']}")
            return result['status_code'], result['data']

    def post_session_data(self, session_data: SessionData):
        """
        Submit session data to the cloud API.
        
        Args:
            session_data: SessionData instance
        """
        logger.info("post_session_data called")
        print(session_data.get_id())
        data = []
        data.append({
            "id": session_data.get_id(),
            "timeStamp": session_data.timeStamp,
            "name": session_data.name,
            "isShotMode": session_data.isShotMode
        })
        url = "https://api.revmetrix.io/api/posts/PostPiSessions"
        
        # Create async worker
        worker = APIUtils.make_post_request_async(url, data=data)
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
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
        
        # Create async worker (this endpoint uses POST)
        worker = APIUtils.make_post_request_async(url, {"start_time": start_time, "end_time": end_time})
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        return result

    def get_diagnostic_script_data_by_session(self, session_id):
        """
        Get all diagnostic script data by session.
        
        Args:
            session_id: Session ID
        """
        logger.info(f"Getting all Diagnostic Script Data by sessionID: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiDiagnosticScriptBySession"
        
        # Create async worker
        worker = APIUtils.make_get_request_async(url, url_params={"sessionId": session_id})
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
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
        
        # Create async worker
        worker = APIUtils.make_post_request_async(url, data=data)
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        return result

    def get_shot_script_data_by_session(self, session_id):
        """
        Get shot script data by session.
        
        Args:
            session_id: Session ID
        """
        logger.info(f"Getting Shot Script data for sesionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiShotsBySession"
        
        # Create async worker
        worker = APIUtils.make_get_request_async(url=url, url_params={"sessionId": session_id})
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
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
        
        # Create async worker
        worker = APIUtils.make_post_request_async(url=url, data=data)
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
        return result


  

    def get_smartdot_data(self, session_id):   
        """
        Get smartdot data by session.
        
        Args:
            session_id: Session ID
        
        """
        logger.info(f"Getting Smartdot data for sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiSmartDotDataBySession"
        
        # Create async worker
        worker = APIUtils.make_get_request_async(url, url_params={"sessionId": session_id})
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
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
        
        # Create async worker
        worker = APIUtils.make_post_request_async(url=url, data=data)
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
        return result

    def get_encoder_data(self, session_id):
        logger.info(f"Getting encoder data by sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiEncoderDataBySession"
        
        # Create async worker
        worker = APIUtils.make_get_request_async(url=url, url_params={"sessionId": session_id})
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
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
        
        # Create async worker
        worker = APIUtils.make_post_request_async(url=url, data=data)
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
        return result
    def get_heat_data(self, session_id):
        logger.info(f"Getting Heat data by sessionId: {session_id}")
        url = "https://api.revmetrix.io/api/gets/GetAllPiHeatDataBySession"
        
        # Create async worker
        worker = APIUtils.make_get_request_async(url=url, url_params={"sessionId": session_id})
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
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
        
        # Create async worker
        worker = APIUtils.make_post_request_async(url=url, data=data)
        
        # Store worker reference to prevent garbage collection
        self._active_workers.append(worker)
        
        # Create event loop and result storage
        loop = QEventLoop()
        result = None
        
        def on_finished(data):
            nonlocal result
            result = data
            loop.quit()
        
        def on_error(error_data):
            nonlocal result
            result = error_data
            loop.quit()
        
        # Connect signals
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        # Wait for result
        loop.exec()
        
        # Wait for thread to finish completely
        worker.wait()
        
        # Clean up worker reference
        self._active_workers.remove(worker)
        
        print(result)
        return result
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