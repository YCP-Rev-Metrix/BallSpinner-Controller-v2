
import requests
import json


def make_get_request(url):
    """
    Make a GET request to the specified URL
    
    Args:
        url (str): The URL to make the request to
        
    Returns:
        dict: Response data or error information
    """
    try:
        # Make the GET request
        response = requests.get(url)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Try to parse JSON response, fallback to text if not JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = response.text
            
        return {
            'status_code': response.status_code,
            'data': data,
            'headers': dict(response.headers)
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'error': str(e),
            'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }

def api_get_test_data():
    url = "https://api.revmetrix.io/api/gets/Test"
    result = make_get_request(url)
    print(result)
    if 'error' in result:
        return result['status_code'], result['error']
    else:
        print(f"Data: {result['data']}")
        return result['status_code'], result['data']


