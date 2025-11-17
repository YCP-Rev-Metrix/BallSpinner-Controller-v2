
import requests
import json
from logs.logger_config import get_logger
from .iCloud import iCloud
# Get logger for this module
logger = get_logger(__name__)

from .APIUtils import APIUtils

class CloudAPI(iCloud):
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