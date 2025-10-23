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