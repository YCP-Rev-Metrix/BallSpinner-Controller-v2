import requests
import json
from logs.logger_config import get_logger

logger = get_logger(__name__)


class APIUtils:
    def make_get_request(url):
        """
        Make a GET request to the specified URL
        
        Args:
            url (str): The URL to make the request to
            
        Returns:
            dict: Response data or error information
        """
        logger.debug(f"Making GET request to: {url}")
        
        try:
            # Make the GET request
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