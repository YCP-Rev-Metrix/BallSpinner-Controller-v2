
import requests
import json
from logs.logger_config import get_logger
from .iCloud import iCloud
# Get logger for this module
logger = get_logger(__name__)

class CloudAPI(iCloud):
    def get_test_data(self):
        logger.info("Starting API test data request")
        url = "https://api.revmetrix.io/api/gets/Test"
        result = make_get_request(url)
        
        if 'error' in result:
            logger.error(f"API request failed: {result['error']}")
            return result['status_code'], result['error']
        else:
            logger.info("API request successful")
            logger.debug(f"Retrieved data: {result['data']}")
            print(f"Data: {result['data']}")
            return result['status_code'], result['data']

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

def api_get_test_data():
    logger.info("Starting API test data request")
    url = "https://api.revmetrix.io/api/gets/Test"
    result = make_get_request(url)
    
    if 'error' in result:
        logger.error(f"API request failed: {result['error']}")
        return result['status_code'], result['error']
    else:
        logger.info("API request successful")
        logger.debug(f"Retrieved data: {result['data']}")
        print(f"Data: {result['data']}")
        return result['status_code'], result['data']


