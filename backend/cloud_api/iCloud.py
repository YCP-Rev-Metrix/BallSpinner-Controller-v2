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


    @abstractmethod
    def get_sessions_in_time_range(self, start_time, end_time):
        """
        Get sessions in a time range.
        
        Args:
            start_time: Start time
            end_time: End time
        """
        pass

    @abstractmethod
    def get_all_diagnostic_script_data_by_session(self, session_id):
        """
        Get all diagnostic script data by session.
        
        Args:
            session_id: Session ID
        """
        pass


    @abstractmethod
    def post_diagnostic_script_data(self, diagnostic_script_data, session_id):
        """
        Post diagnostic data to the cloud API.
        
        Args:
            diagnostic_script_data: DiagnosticScriptData instance
            session_id: Session ID
        """
        pass

    @abstractmethod 
    def post_shot_script_data(self, shot_script_data, session_id):
        """
        Post shot script data to the cloud API.
        
        Args:
            shot_script_data: ShotScriptData instance
            session_id: Session ID
        """
        pass
    @abstractmethod
    def get_shot_script_data_by_session(self, session_id):
        """
        Get shot script data by session.
        
        Args:
            session_id: Session ID
        """
        pass
    # @abstractmethod
    # def get_all_encoder_data_by_session(self, session_id):
    #     """
    #     Get all encoder data by session.
        
    #     Args:
    #         session_id: Session ID
    #     """
    #     pass