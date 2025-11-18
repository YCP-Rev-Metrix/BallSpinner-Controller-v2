from abc import ABC, abstractmethod
import requests
import json
from logs.logger_config import get_logger

# Get logger for this module
logger = get_logger(__name__)
#Turn into an API interface with a bunch of abstract methods

#Make cloudAPI implement iCloud
class iCloud(ABC):
    @abstractmethod
    def get_test_data(self):
        pass
    
    @abstractmethod
    def post_session_data(self, session_data):
        """
        Submit session data to the cloud API.
        
        Args:
            session_data: SessionData instance
        """
        pass    
    # @abstractmethod
    # def get_session_data(self):
    #     pass
    # @abstractmethod
    # def get_smartdot_data(self, session_id):
    #     pass
    # @abstractmethod
    # def get_shot_script_data(self, session_id):
    #     pass
    # @abstractmethod
    # def get_encoder_data(self, session_id):
    #     pass
    # @abstractmethod
    # def post_smartdot_data(self, session_id, smartdot_data):
    #     """
    #     Submit smartdot data to the cloud API.
        
    #     Args:
    #         smartdot_data: SmartDotData instance
    #     """
    #     pass

    # @abstractmethod
    # def post_shot_script_data(self, session_id, shot_script_data):
    #     """
    #     Submit shot script data to the cloud API.
        
    #     Args:
    #         shot_script_data: ShotScriptData instance
    #     """
    #     pass
    # @abstractmethod
    # def post_encoder_data(self, session_id, encoder_data):
    #     """
    #     Submit encoder data to the cloud API.
        
    #     Args:
    #         encoder_data: EncoderData instance
    #     """
    #     pass

    # @abstractmethod
    # def post_diagnostic_script_data(self, session_id, diagnostic_script_data):
    #     """
    #     Submit diagnostic script data to the cloud API.
        
    #     Args:
    #         diagnostic_script_data: DiagnosticScriptData instance
    #     """
    #     pass
    # @abstractmethod
    # def submit_shot_mode_data(self, session_id, smartdot_data, shot_script_data, encoder_data):
    #     """
    #     Submit shot mode data to the cloud API.
        
    #     Args:
    #         session_data: SessionData instance
    #         smartdot_data: SmartDotData instance
    #         shot_script_data: ShotScriptData instance
    #         encoder_data: EncoderData instance
    #     """
    #     pass
    # @abstractmethod
    # def submit_diagnostic_mode_data(self, session_id, smartdot_data, diagnostic_script_data, encoder_data):
    #     """
    #     Submit diagnostic mode data to the cloud API.
        
    #     Args:
    #         session_data: SessionData instance
    #         smartdot_data: SmartDotData instance
    #         diagnostic_script_data: DiagnosticScriptData instance
    #         encoder_data: EncoderData instance
    #     """
    #     pass
