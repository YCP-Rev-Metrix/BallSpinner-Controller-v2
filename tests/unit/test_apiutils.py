import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import json

from backend.cloud_api.APIUtils import APIUtils


class TestAPIUtilsMakeGetRequest:
    """Test APIUtils.make_get_request() method"""

    @patch('backend.cloud_api.APIUtils.requests.get')
    def test_make_get_request_success(self, mock_get):
        """Test successful GET request without parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_get.return_value = mock_response

        result = APIUtils.make_get_request("https://api.example.com/data")

        assert result['status_code'] == 200
        assert result['data'] == {"key": "value"}
        assert 'headers' in result
        mock_get.assert_called_once()

    @patch('backend.cloud_api.APIUtils.requests.get')
    def test_make_get_request_with_params(self, mock_get):
        """Test GET request with URL parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [1, 2, 3]}
        mock_response.headers = {}
        mock_get.return_value = mock_response

        params = {"id": 123, "filter": "active"}
        result = APIUtils.make_get_request("https://api.example.com/data", url_params=params)

        assert result['status_code'] == 200
        assert result['data'] == {"results": [1, 2, 3]}
        mock_get.assert_called_once_with("https://api.example.com/data", params=params, timeout=7)

    @patch('backend.cloud_api.APIUtils.requests.get')
    def test_make_get_request_text_response(self, mock_get):
        """Test GET request when response is not JSON"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
        mock_response.text = "Plain text response"
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = APIUtils.make_get_request("https://api.example.com/data")

        assert result['status_code'] == 200
        assert result['data'] == "Plain text response"

    @patch('backend.cloud_api.APIUtils.requests.get')
    def test_make_get_request_http_error(self, mock_get):
        """Test GET request with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 404
        error = requests.exceptions.HTTPError("404 Not Found")
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error
        mock_get.return_value = mock_response

        result = APIUtils.make_get_request("https://api.example.com/notfound")

        assert 'error' in result
        assert result['status_code'] == 404

    @patch('backend.cloud_api.APIUtils.requests.get')
    def test_make_get_request_timeout(self, mock_get):
        """Test GET request with timeout"""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = APIUtils.make_get_request("https://api.example.com/slow")

        assert 'error' in result
        assert 'timed out' in result['error'].lower() or 'timeout' in result['error'].lower()

    @patch('backend.cloud_api.APIUtils.requests.get')
    def test_make_get_request_connection_error(self, mock_get):
        """Test GET request with connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        result = APIUtils.make_get_request("https://invalid.example.com")

        assert 'error' in result
        assert 'connect' in result['error'].lower()


class TestAPIUtilsMakePostRequest:
    """Test APIUtils.make_post_request() method"""

    @patch('backend.cloud_api.APIUtils.requests.post')
    def test_make_post_request_success(self, mock_post):
        """Test successful POST request"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123, "status": "created"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_post.return_value = mock_response

        data = {"name": "test", "value": 42}
        result = APIUtils.make_post_request("https://api.example.com/create", data)

        assert result['status_code'] == 201
        assert result['data'] == {"id": 123, "status": "created"}
        assert 'headers' in result
        mock_post.assert_called_once_with("https://api.example.com/create", json=data, timeout=7)

    @patch('backend.cloud_api.APIUtils.requests.post')
    def test_make_post_request_with_json_list(self, mock_post):
        """Test POST request with list of JSON data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "count": 2}
        mock_response.headers = {}
        mock_post.return_value = mock_response

        data = [{"id": 1}, {"id": 2}]
        result = APIUtils.make_post_request("https://api.example.com/batch", data)

        assert result['status_code'] == 200
        assert result['data']['count'] == 2
        mock_post.assert_called_once_with("https://api.example.com/batch", json=data, timeout=7)

    @patch('backend.cloud_api.APIUtils.requests.post')
    def test_make_post_request_text_response(self, mock_post):
        """Test POST request when response is not JSON"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
        mock_response.text = "OK"
        mock_response.headers = {}
        mock_post.return_value = mock_response

        result = APIUtils.make_post_request("https://api.example.com/submit", {})

        assert result['status_code'] == 200
        assert result['data'] == "OK"

    @patch('backend.cloud_api.APIUtils.requests.post')
    def test_make_post_request_validation_error(self, mock_post):
        """Test POST request with validation error (400)"""
        mock_response = Mock()
        mock_response.status_code = 400
        error = requests.exceptions.HTTPError("400 Bad Request")
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error
        mock_post.return_value = mock_response

        result = APIUtils.make_post_request("https://api.example.com/submit", {})

        assert 'error' in result
        assert result['status_code'] == 400

    @patch('backend.cloud_api.APIUtils.requests.post')
    def test_make_post_request_server_error(self, mock_post):
        """Test POST request with server error (500)"""
        mock_response = Mock()
        mock_response.status_code = 500
        error = requests.exceptions.HTTPError("500 Server Error")
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error
        mock_post.return_value = mock_response

        result = APIUtils.make_post_request("https://api.example.com/submit", {})

        assert 'error' in result
        assert result['status_code'] == 500

    @patch('backend.cloud_api.APIUtils.requests.post')
    def test_make_post_request_timeout(self, mock_post):
        """Test POST request with timeout"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        result = APIUtils.make_post_request("https://api.example.com/slow", {"data": "test"})

        assert 'error' in result

    @patch('backend.cloud_api.APIUtils.requests.post')
    def test_make_post_request_connection_error(self, mock_post):
        """Test POST request with connection error"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        result = APIUtils.make_post_request("https://invalid.example.com", {"data": "test"})

        assert 'error' in result
