import pytest
from unittest.mock import Mock, patch, MagicMock
import datetime as dt

from backend.cloud_api.CloudAPI import CloudAPI
from backend.models.SessionData import SessionData
from backend.models.DiagnosticScriptData import DiagnosticScriptData, DiagnosticScriptDataInstance
from backend.models.ShotScriptData import ShotScriptData, ShotScriptDataInstance
from backend.models.SmartDotData import SmartDotData, SmartDotDataInstance
from backend.models.EncoderData import EncoderData, EncoderDataInstance
from backend.models.HeatData import HeatData, HeatDataInstance


class TestCloudAPIInitialization:
    """Test CloudAPI initialization"""

    def test_cloudapi_initialization(self):
        """Test CloudAPI initializes correctly"""
        api = CloudAPI()
        assert api is not None


class TestCloudAPIGetTestData:
    """Test CloudAPI.get_test_data() method"""

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_test_data_success(self, mock_get):
        """Test successful test data retrieval"""
        mock_get.return_value = {
            'status_code': 200,
            'data': {"test": "data"},
            'headers': {}
        }

        api = CloudAPI()
        status_code, data = api.get_test_data()

        assert status_code == 200
        assert data == {"test": "data"}
        mock_get.assert_called_once()

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_test_data_error(self, mock_get):
        """Test test data retrieval with error"""
        mock_get.return_value = {
            'error': 'Connection failed',
            'status_code': 500
        }

        api = CloudAPI()
        status_code, data = api.get_test_data()

        assert status_code == 500
        assert data == 'Connection failed'


class TestCloudAPIPostSessionData:
    """Test CloudAPI.post_session_data() method"""

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_post_request')
    def test_post_session_data_success(self, mock_post):
        """Test successful session data posting"""
        mock_post.return_value = {
            'status_code': 201,
            'data': {"sessionId": 123},
            'headers': {}
        }

        session_data = SessionData(id=1, timeStamp=dt.datetime.now(), name="Test Session", isShotMode=True)
        api = CloudAPI()
        result = api.post_session_data(session_data)

        assert result['status_code'] == 201
        assert 'sessionId' in result['data']
        mock_post.assert_called_once()

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_post_request')
    def test_post_session_data_formatting(self, mock_post):
        """Test that session data is formatted correctly for API"""
        mock_post.return_value = {'status_code': 201, 'data': {}}

        session_data = SessionData(
            id=42,
            timeStamp=dt.datetime(2026, 1, 22, 12, 0),
            name="Test",
            isShotMode=False,
            Spin_Instruction_Points=[(0.0, 0.0), (1.0, 100.0)],
            Tilt_Instruction_Points=[(0.0, -30.0), (1.0, 30.0)],
            Angle_Instruction_Points=[(0.0, 0.0), (1.0, 90.0)],
        )
        api = CloudAPI()
        api.post_session_data(session_data)

        # Verify the data passed to make_post_request
        call_args = mock_post.call_args
        # Data is passed as keyword argument
        data = call_args[1]['data']
        assert len(data) == 1
        assert data[0]['id'] == 42
        assert data[0]['name'] == "Test"
        assert data[0]['isShotMode'] == False

        # Confirm that instruction points were serialized into strings
        assert data[0]['Spin_Instruction_Points'] == "0:0,1:100"
        assert data[0]['Tilt_Instruction_Points'] == "0:-30,1:30"
        assert data[0]['Angle_Instruction_Points'] == "0:0,1:90"


class TestCloudAPIGetSessionsInTimeRange:
    """Test CloudAPI.get_sessions_in_time_range() method"""

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_sessions_in_time_range_success(self, mock_get):
        """Test successful retrieval of sessions in time range"""
        mock_get.return_value = {
            'status_code': 200,
            'data': [{"id": 1}, {"id": 2}],
            'headers': {}
        }

        api = CloudAPI()
        result = api.get_sessions_in_time_range(0, 1000)

        assert result['status_code'] == 200
        assert len(result['data']) == 2

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_sessions_all_sessions(self, mock_get):
        """Test retrieval of all sessions using (0,0) parameters"""
        mock_get.return_value = {
            'status_code': 200,
            'data': [{"id": 1}, {"id": 2}, {"id": 3}],
            'headers': {}
        }

        api = CloudAPI()
        result = api.get_sessions_in_time_range(0, 0)

        assert result['status_code'] == 200
        # Verify API was called with range parameters
        call_args = mock_get.call_args
        params = call_args[1]['json_data']
        assert params['RangeStart'] == 0
        assert params['RangeEnd'] == 0


class TestCloudAPIGetDiagnosticScriptData:
    """Test CloudAPI.get_diagnostic_script_data_by_session() method"""

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_diagnostic_script_data_success(self, mock_get):
        """Test successful retrieval of diagnostic script data"""
        mock_get.return_value = {
            'status_code': 200,
            'data': [
                {"time": 0.0, "motorID": 1, "instruction": 100},
                {"time": 0.5, "motorID": 1, "instruction": 150}
            ],
            'headers': {}
        }

        api = CloudAPI()
        result = api.get_diagnostic_script_data_by_session(123)

        assert result['status_code'] == 200
        assert len(result['data']) == 2
        mock_get.assert_called_once()

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_diagnostic_script_data_with_session_id(self, mock_get):
        """Test that session ID is passed correctly"""
        mock_get.return_value = {
            'status_code': 200,
            'data': [],
            'headers': {}
        }

        api = CloudAPI()
        api.get_diagnostic_script_data_by_session(456)

        # Verify session ID was passed in params
        call_args = mock_get.call_args
        params = call_args[1]['url_params']
        assert params['sessionId'] == 456


class TestCloudAPIPostDiagnosticScriptData:
    """Test CloudAPI.post_diagnostic_script_data() method"""

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_post_request')
    def test_post_diagnostic_script_data_success(self, mock_post):
        """Test successful posting of diagnostic script data"""
        mock_post.return_value = {
            'status_code': 201,
            'data': {"success": True},
            'headers': {}
        }

        # Create diagnostic script data
        diagnostic_data = DiagnosticScriptData()
        diagnostic_data.add_diagnostic_script_data(DiagnosticScriptDataInstance(time=0.0, motor_id=1, instruction=100))
        diagnostic_data.add_diagnostic_script_data(DiagnosticScriptDataInstance(time=0.5, motor_id=1, instruction=150))

        api = CloudAPI()
        result = api.post_diagnostic_script_data(diagnostic_data.get_diagnostic_script_data(), session_id=123)

        assert result['status_code'] == 201
        mock_post.assert_called_once()

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_post_request')
    def test_post_diagnostic_script_data_formatting(self, mock_post):
        """Test that diagnostic data is formatted correctly"""
        mock_post.return_value = {'status_code': 201, 'data': {}}

        diagnostic_data = DiagnosticScriptData()
        diagnostic_data.add_diagnostic_script_data(DiagnosticScriptDataInstance(time=1.0, motor_id=2, instruction=200))

        api = CloudAPI()
        api.post_diagnostic_script_data(diagnostic_data.get_diagnostic_script_data(), session_id=42)

        # Verify formatting
        call_args = mock_post.call_args
        data = call_args[1]['data']
        assert len(data) == 1
        assert data[0]['sessionId'] == 42
        assert data[0]['time'] == 1.0
        assert data[0]['motorID'] == 2
        assert data[0]['instruction'] == 200


class TestCloudAPIGetShotScriptData:
    """Test CloudAPI.get_shot_script_data_by_session() method"""

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_shot_script_data_success(self, mock_get):
        """Test successful retrieval of shot script data"""
        mock_get.return_value = {
            'status_code': 200,
            'data': [
                {"time": 0.0, "rpm": 1000, "angleDegrees": 0, "tiltDegrees": 0},
                {"time": 0.1, "rpm": 1500, "angleDegrees": 45, "tiltDegrees": 10}
            ],
            'headers': {}
        }

        api = CloudAPI()
        result = api.get_shot_script_data_by_session(789)

        assert result['status_code'] == 200
        assert len(result['data']) == 2

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_get_request')
    def test_get_shot_script_data_with_session_id(self, mock_get):
        """Test that session ID is passed correctly"""
        mock_get.return_value = {
            'status_code': 200,
            'data': [],
            'headers': {}
        }

        api = CloudAPI()
        api.get_shot_script_data_by_session(999)

        # Verify session ID was passed in params
        call_args = mock_get.call_args
        params = call_args[1]['url_params']
        assert params['sessionId'] == 999


class TestCloudAPIPostShotScriptData:
    """Test CloudAPI.post_shot_script_data() method"""

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_post_request')
    def test_post_shot_script_data_success(self, mock_post):
        """Test successful posting of shot script data"""
        mock_post.return_value = {
            'status_code': 201,
            'data': {"success": True},
            'headers': {}
        }

        # Create shot script data
        shot_data = ShotScriptData()
        shot_data.add_shot_script_data(ShotScriptDataInstance(time=0.0, rpm=1000, angleDeg=0, tiltDeg=0))
        shot_data.add_shot_script_data(ShotScriptDataInstance(time=0.1, rpm=1500, angleDeg=45, tiltDeg=10))

        api = CloudAPI()
        result = api.post_shot_script_data(shot_data.shot_script_data_entries, session_id=123)

        assert result['status_code'] == 201
        mock_post.assert_called_once()

    @patch('backend.cloud_api.CloudAPI.APIUtils.make_post_request')
    def test_post_shot_script_data_formatting(self, mock_post):
        """Test that shot data is formatted correctly"""
        mock_post.return_value = {'status_code': 201, 'data': {}}

        shot_data = ShotScriptData()
        shot_data.add_shot_script_data(ShotScriptDataInstance(time=0.5, rpm=1200, angleDeg=30, tiltDeg=5))

        api = CloudAPI()
        api.post_shot_script_data(shot_data.shot_script_data_entries, session_id=55)

        # Verify formatting
        call_args = mock_post.call_args
        data = call_args[1]['data']
        assert len(data) == 1
        assert data[0]['sessionId'] == 55
        assert data[0]['time'] == 0.5
        assert data[0]['rpm'] == 1200
        assert data[0]['angleDegrees'] == 30
        assert data[0]['tiltDegrees'] == 5
