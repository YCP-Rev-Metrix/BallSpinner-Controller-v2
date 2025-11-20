import requests
import json
from logs.logger_config import get_logger
from PyQt6.QtCore import QThread, pyqtSignal
import time
logger = get_logger(__name__)


class APIWorker(QThread):
    """
    QThread worker class for making asynchronous GET and POST requests.
    """
    finished = pyqtSignal(dict)  # Emitted when request completes successfully
    error = pyqtSignal(dict)     # Emitted when request fails
    
    def __init__(self, request_type, url, url_params=None, data=None):
        """
        Initialize the API worker.
        
        Args:
            request_type (str): 'GET' or 'POST'
            url (str): The URL to make the request to
            url_params (dict, optional): URL parameters for GET requests
            data (dict, optional): Data to send for POST requests
        """
        super().__init__()
        self.request_type = request_type.upper()
        self.url = url
        self.url_params = url_params
        self.data = data
    
    def run(self):
        """
        Execute the HTTP request in a separate thread.
        """
        try:
            # time.sleep(1)
            if self.request_type == 'GET':
                result = self._make_get_request()
            elif self.request_type == 'POST':
                result = self._make_post_request()
            else:
                raise ValueError(f"Invalid request type: {self.request_type}")
            
            # Check if result contains an error
            if 'error' in result:
                self.error.emit(result)
            else:
                self.finished.emit(result)
                
        except Exception as e:
            logger.error(f"Unexpected error in APIWorker: {str(e)}")
            self.error.emit({
                'error': str(e),
                'status_code': None
            })
    
    def _make_get_request(self):
        """
        Make a GET request (internal method, same logic as APIUtils.make_get_request).
        """
        logger.debug(f"Making GET request to: {self.url}")
        
        try:
            # Make the GET request
            if self.url_params is not None:
                response = requests.get(self.url, params=self.url_params)
                logger.debug(f"Response status code: {response.status_code}")
            else:
                response = requests.get(self.url)
                logger.debug(f"Response status code: {response.status_code}")
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Try to parse JSON response, fallback to text if not JSON
            try:
                data = response.json()
                logger.debug("Successfully parsed JSON response")
            except json.JSONDecodeError:
                data = response.text
                logger.debug("Response is not JSON, using text format")
                
            logger.info(f"Successfully retrieved data from {self.url}{f' with url params: {self.url_params}' if self.url_params else ''}")
            return {
                'status_code': response.status_code,
                'data': data,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {self.url}: {str(e)}")
            return {
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def _make_post_request(self):
        """
        Make a POST request (internal method, same logic as APIUtils.make_post_request).
        """
        logger.debug(f"Making POST request to: {self.url}")
        try:
            # Make the POST request
            response = requests.post(self.url, json=self.data)    
            logger.debug(f"Response status code: {response.status_code}")
            # Check if the request was successful
            response.raise_for_status()
            # Try to parse JSON response, fallback to text if not JSON
            try:
                data = response.json()
                logger.debug("Successfully parsed JSON response")
            except json.JSONDecodeError:
                data = response.text
                logger.debug("Response is not JSON, using text format")
            logger.info(f"Successfully retrieved data from {self.url}")
            return {
                'status_code': response.status_code,
                'data': data,
                'headers': dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {self.url}: {str(e)}")
            return {
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }


class APIUtils:
    def make_get_request(url, url_params=None):
        """
        Make a GET request to the specified URL
        Optional url_params can be passed in to add to the URL
        Args:
            url (str): The URL to make the request to
            url_params (dict): The URL parameters to add to the URL
        Returns:
            dict: Response data or error information
        """
        logger.debug(f"Making GET request to: {url}")
        
        try:
            # Make the GET request
            if url_params is not None:
                response = requests.get(url, params=url_params)
                logger.debug(f"Response status code: {response.status_code}")
            else:
                response = requests.get(url)
                logger.debug(f"Response status code: {response.status_code}")
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Try to parse JSON response, fallback to text if not JSON
            try:
                data = response.json()
                logger.debug("Successfully parsed JSON response")
            except json.JSONDecodeError:
                data = response.text
                logger.debug("Response is not JSON, using text format")
                
            logger.info(f"Successfully retrieved data from {url}{f"with url params: {url_params}" if url_params else ""}")
            return {
                'status_code': response.status_code,
                'data': data,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return {
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    

    def make_post_request(url, data):
        """
        Make a POST request to the specified URL
        
        Args:
            url (str): The URL to make the request to
            data (dict): The data to send in the request

        Returns:
            dict: Response data or error information
        """
        logger.debug(f"Making POST request to: {url}")
        try:
            # Make the POST request
            response = requests.post(url, json=data)    
            logger.debug(f"Response status code: {response.status_code}")
            # Check if the request was successful
            response.raise_for_status()
            # Try to parse JSON response, fallback to text if not JSON
            try:
                data = response.json()
                logger.debug("Successfully parsed JSON response")
            except json.JSONDecodeError:
                data = response.text
                logger.debug("Response is not JSON, using text format")
            logger.info(f"Successfully retrieved data from {url}")
            return {
                'status_code': response.status_code,
                'data': data,
                'headers': dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return {
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    @staticmethod
    def make_get_request_async(url, url_params=None):
        """
        Make an asynchronous GET request using QThread.
        
        Args:
            url (str): The URL to make the request to
            url_params (dict, optional): The URL parameters to add to the URL
            
        Returns:
            APIWorker: The worker thread instance. Connect to its 'finished' and 'error' signals
                       to handle the response.
        """
        worker = APIWorker('GET', url, url_params=url_params)
        worker.start()
        return worker
    
    @staticmethod
    def make_post_request_async(url, data):
        """
        Make an asynchronous POST request using QThread.
        
        Args:
            url (str): The URL to make the request to
            data (dict): The data to send in the request
            
        Returns:
            APIWorker: The worker thread instance. Connect to its 'finished' and 'error' signals
                       to handle the response.
        """
        worker = APIWorker('POST', url, data=data)
        worker.start()
        return worker