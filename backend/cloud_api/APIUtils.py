import requests
import json
from logs.logger_config import get_logger

logger = get_logger(__name__)


class APIUtils:
    def make_get_request(url, url_params=None, json_data=None):
        """Make a GET request to the specified URL.

        Optional url_params can be passed in to add to the URL.
        Optional json_data can be provided as a JSON body (some APIs expect this even for GET).

        Args:
            url (str): The URL to make the request to
            url_params (dict): The URL parameters to add to the URL
            json_data (dict): The JSON body to send with the request

        Returns:
            dict: Response data or error information
        """
        logger.debug(f"Making GET request to: {url}")
        
        try:
            # Make the GET request
            if url_params is not None and json_data is not None:
                response = requests.get(url, params=url_params, json=json_data, timeout=7)
            elif url_params is not None:
                response = requests.get(url, params=url_params, timeout=7)
            elif json_data is not None:
                response = requests.get(url, json=json_data, timeout=7)
            else:
                response = requests.get(url, timeout=7)

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
                
            logger.info(f"Successfully retrieved data from {url}{' with url params: ' + str(url_params) if url_params else ''}{' with JSON body' if json_data else ''}")
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
    
    # def make_post_request_with_body(url, body):
    #     """
    #     Make a GET request to the specified URL with a body
        
    #     Args:
    #         url (str): The URL to make the request to
    #         body (dict): The body to send in the request
    #     """
    #     logger.debug(f"Making GET request to: {url} with body: {body}")
    #     try:
    #         # Make the GET request
    #         response = requests.post(url, json=body)
    #         logger.debug(f"Response status code: {response.status_code}")
    #         # Check if the request was successful
    #         response.raise_for_status()
    #         # Try to parse JSON response, fallback to text if not JSON
    #         try:
    #             data = response.json()
    #             logger.debug("Successfully parsed JSON response")
    #         except json.JSONDecodeError:
    #             data = response.text
    #             logger.debug("Response is not JSON, using text format")
    #         logger.info(f"Successfully retrieved data from {url}")
    #         return {
    #             'status_code': response.status_code,
    #             'data': data,
    #             'headers': dict(response.headers)
    #         }
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"Request failed for {url}: {str(e)}")
    #         return {
    #             'error': str(e),
    #             'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
    #         }


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
            response = requests.post(url, json=data, timeout=7)    
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