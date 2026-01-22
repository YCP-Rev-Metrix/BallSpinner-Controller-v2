import pytest
from unittest.mock import Mock, patch
import datetime as dt

from backend.models.DataController import DataController
from backend.models.SessionData import SessionData
from backend.models.SmartDotData import SmartDotDataInstance
from backend.models.DiagnosticScriptData import DiagnosticScriptDataInstance
from backend.models.ShotScriptData import ShotScriptDataInstance
from backend.models.EncoderData import EncoderDataInstance
from backend.models.HeatData import HeatDataInstance


# ============================================================================
# DATACONTROLLER TESTS (backend/models/DataController.py)
# ============================================================================

# Test 1: DataController initialization
def test_DataController_initialization():
    """Test DataController initializes with SessionData and creates data storage objects"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(
            id=1,
            name="Test Session",
            timeStamp=dt.datetime.now(),
            isShotMode=True
        )
        test_dc = DataController(test_session)

        assert test_dc.session_data == test_session
        assert test_dc.smartdot_data is not None
        assert test_dc.diagnostic_script_data is not None
        assert test_dc.shot_script_data is not None
        assert test_dc.encoder_data is not None
        assert test_dc.heat_data is not None
        assert test_dc.cloud_api is not None


# Test 2: DataController set_session_name
def test_DataController_set_session_name():
    """Test setting session name updates the session data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(
            id=1,
            name="Test Session",
            timeStamp=dt.datetime.now(),
            isShotMode=True
        )
        test_dc = DataController(test_session)
        new_name = "Updated Session Name"
        test_dc.set_session_name(new_name)

        assert test_dc.session_data.name == new_name


# Test 3: DataController add_smartdot_data
def test_DataController_add_smartdot_data():
    """Test adding SmartDot data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(
            id=1,
            name="Test Session",
            timeStamp=dt.datetime.now(),
            isShotMode=True
        )
        test_dc = DataController(test_session)
        smartdot_instance = SmartDotDataInstance(
            time=dt.datetime.now(),
            data_selector=0,
            accelerometer_x=0,
            accelerometer_y=0,
            accelerometer_z=0,
            gyroscope_x=0,
            gyroscope_y=0,
            gyroscope_z=0,
            magnetometer_x=0,
            magnetometer_y=0,
            magnetometer_z=0,
            light=0
        )
        test_dc.add_smartdot_data(smartdot_instance)
        retrieved_data = test_dc.get_smartdot_data()

        assert len(retrieved_data) == 1
        assert retrieved_data[0] == smartdot_instance



# Test 4: DataController add_diagnostic_script_data
def test_DataController_add_diagnostic_script_data():
    """Test adding diagnostic script data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(
            id=2,
            name="Diag Session",
            timeStamp=dt.datetime.now(),
            isShotMode=False
        )
        test_dc = DataController(test_session)

        diag_instance = DiagnosticScriptDataInstance(time=1.0, motor_id=1, instruction=42.0)
        test_dc.add_diagnostic_script_data(diag_instance)

        entries = test_dc.get_diagnostic_script_data()
        assert len(entries) == 1
        assert entries[0] == diag_instance


# Test 5: DataController add_shot_script_data
def test_DataController_add_shot_script_data():
    """Test adding shot script data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(
            id=3,
            name="Shot Session",
            timeStamp=dt.datetime.now(),
            isShotMode=True
        )
        test_dc = DataController(test_session)

        shot_instance = ShotScriptDataInstance(time=1.0, rpm=1500, angleDeg=30.0, tiltDeg=10.0)
        test_dc.add_shot_script_data(shot_instance)

        entries = test_dc.get_shot_script_data()
        assert len(entries) == 1
        assert entries[0] == shot_instance


# Test 6: DataController add_encoder_data
def test_DataController_add_encoder_data():
    """Test adding encoder data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(
            id=4,
            name="Encoder Session",
            timeStamp=dt.datetime.now(),
            isShotMode=True
        )
        test_dc = DataController(test_session)

        enc_instance = EncoderDataInstance(time=1.0, pulses=123.0, motor_id=2)
        test_dc.add_encoder_data(enc_instance)

        entries = test_dc.get_encoder_data()
        assert len(entries) == 1
        assert entries[0] == enc_instance


# Test 7: DataController add_heat_data
def test_DataController_add_heat_data():
    """Test adding heat data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(
            id=5,
            name="Heat Session",
            timeStamp=dt.datetime.now(),
            isShotMode=True
        )
        test_dc = DataController(test_session)

        heat_instance = HeatDataInstance(time=1.0, motor_id=1, value=85.0)
        test_dc.add_heat_data(heat_instance)

        entries = test_dc.get_heat_data()
        assert len(entries) == 1
        assert entries[0] == heat_instance


# Test 8: DataController get_diagnostic_script_data
def test_DataController_get_diagnostic_script_data():
    """Test getting diagnostic script data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(id=6, name="Diag", timeStamp=dt.datetime.now(), isShotMode=False)
        test_dc = DataController(test_session)
        inst = DiagnosticScriptDataInstance(time=1.0, motor_id=1, instruction=11.0)
        test_dc.add_diagnostic_script_data(inst)

        entries = test_dc.get_diagnostic_script_data()
        assert len(entries) == 1
        assert entries[0].instruction == 11.0


# Test 9: DataController get_shot_script_data
def test_DataController_get_shot_script_data():
    """Test getting shot script data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(id=7, name="Shot", timeStamp=dt.datetime.now(), isShotMode=True)
        test_dc = DataController(test_session)
        inst = ShotScriptDataInstance(time=1.0, rpm=1200, angleDeg=25.0, tiltDeg=5.0)
        test_dc.add_shot_script_data(inst)

        entries = test_dc.get_shot_script_data()
        assert len(entries) == 1
        assert entries[0].rpm == 1200


# Test 10: DataController get_encoder_data
def test_DataController_get_encoder_data():
    """Test getting encoder data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(id=8, name="Enc", timeStamp=dt.datetime.now(), isShotMode=True)
        test_dc = DataController(test_session)
        inst = EncoderDataInstance(time=1.0, pulses=222.0, motor_id=1)
        test_dc.add_encoder_data(inst)

        entries = test_dc.get_encoder_data()
        assert len(entries) == 1
        assert entries[0].pulses == 222.0


# Test 11: DataController get_heat_data
def test_DataController_get_heat_data():
    """Test getting heat data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        test_session = SessionData(id=9, name="Heat", timeStamp=dt.datetime.now(), isShotMode=True)
        test_dc = DataController(test_session)
        inst = HeatDataInstance(time=1.0, motor_id=2, value=90.0)
        test_dc.add_heat_data(inst)

        entries = test_dc.get_heat_data()
        assert len(entries) == 1
        assert entries[0].value == 90.0


# Test 12: DataController submit_session_data - Shot Mode
def test_DataController_submit_session_data_shot_mode():
    """Test submitting session data in shot mode"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.post_session_data.return_value = {'data': [123]}
        mock_bsc.get_cloud_api.return_value = cloud_api

        test_session = SessionData(id=10, name="Shot Session", timeStamp=dt.datetime.now(), isShotMode=True)
        dc = DataController(test_session)

        dc.add_shot_script_data(ShotScriptDataInstance(time=1.0, rpm=1200, angleDeg=25.0, tiltDeg=5.0))
        dc.add_encoder_data(EncoderDataInstance(time=1.1, pulses=200, motor_id=1))
        dc.add_heat_data(HeatDataInstance(time=1.2, motor_id=1, value=80.0))

        dc.submit_session_data()

        cloud_api.post_session_data.assert_called_once()
        cloud_api.post_shot_script_data.assert_called_once()
        cloud_api.post_diagnostic_script_data.assert_not_called()
        cloud_api.post_encoder_data.assert_called_once()
        cloud_api.post_heat_data.assert_called_once()



# Test 13: DataController submit_session_data - Diagnostic Mode
def test_DataController_submit_session_data_diagnostic_mode():
    """Test submitting session data in diagnostic mode"""
    # TODO: Create DataController with isShotMode=False
    # TODO: Add some diagnostic script data, encoder data, heat data
    # TODO: Mock cloud_api methods
    # TODO: Call submit_session_data()
    # TODO: Verify cloud_api.post_diagnostic_script_data was called (NOT post_shot_script_data)
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.post_session_data.return_value = {'data': [123]}
        mock_bsc.get_cloud_api.return_value = cloud_api

        test_session = SessionData(id=10, name="Diagnostic Session", timeStamp=dt.datetime.now(), isShotMode=False)
        dc = DataController(test_session)

        dc.add_diagnostic_script_data(
            DiagnosticScriptDataInstance(time=1.0, motor_id=1, instruction=42.0)
        )
        dc.add_encoder_data(EncoderDataInstance(time=1.1, pulses=200, motor_id=1))
        dc.add_heat_data(HeatDataInstance(time=1.2, motor_id=1, value=80.0))

        dc.submit_session_data()

        cloud_api.post_session_data.assert_called_once()
        cloud_api.post_diagnostic_script_data.assert_called_once()
        cloud_api.post_shot_script_data.assert_not_called()
        cloud_api.post_encoder_data.assert_called_once()
        cloud_api.post_heat_data.assert_called_once()


# Test 14: DataController submit_session_data - Missing Data
def test_DataController_submit_session_data_missing_data():
    """Test submitting session data when some data types are missing"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.post_session_data.return_value = {'data': [321]}
        mock_bsc.get_cloud_api.return_value = cloud_api

        test_session = SessionData(id=11, name="Missing Data", timeStamp=dt.datetime.now(), isShotMode=True)
        dc = DataController(test_session)

        dc.submit_session_data()

        cloud_api.post_session_data.assert_called_once()
        cloud_api.post_shot_script_data.assert_not_called()
        cloud_api.post_diagnostic_script_data.assert_not_called()
        cloud_api.post_encoder_data.assert_not_called()
        cloud_api.post_heat_data.assert_not_called()


# Test 15: DataController load_session_data_from_cloud - Shot Mode
def test_DataController_load_session_data_from_cloud_shot_mode():
    """Test loading session data from cloud in shot mode"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.get_shot_script_data_by_session.return_value = {
            'data': [{'time': 1.0, 'rpm': 1200, 'angleDegrees': 10.0, 'tiltDegrees': 2.0}]
        }
        cloud_api.get_smartdot_data.return_value = {
            'data': [{'time': 1.0, 'dataSelector': 0, 'xL_X': 0, 'xL_Y': 0, 'xL_Z': 0,
                      'gY_X': 0, 'gY_Y': 0, 'gY_Z': 0, 'mG_X': 0, 'mG_Y': 0, 'mG_Z': 0, 'lt': 0}]
        }
        cloud_api.get_encoder_data.return_value = {'data': [{'time': 1.0, 'pulses': 10, 'motorId': 1}]}
        cloud_api.get_heat_data.return_value = {'data': [{'time': 1.0, 'motorId': 1, 'value': 80.0}]}
        mock_bsc.get_cloud_api.return_value = cloud_api

        session = SessionData(id=12, name="Shot Cloud", timeStamp=dt.datetime.now(), isShotMode=True)
        dc = DataController(session)

        dc.load_session_data_from_cloud(session)

        assert len(dc.get_shot_script_data()) == 1
        assert len(dc.get_smartdot_data()) == 1
        assert len(dc.get_encoder_data()) == 1
        assert len(dc.get_heat_data()) == 1


# Test 16: DataController load_session_data_from_cloud - Diagnostic Mode
def test_DataController_load_session_data_from_cloud_diagnostic_mode():
    """Test loading session data from cloud in diagnostic mode"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.get_diagnostic_script_data_by_session.return_value = {
            'data': [{'time': 1.0, 'motorId': 1, 'instruction': 9.0}]
        }
        cloud_api.get_smartdot_data.return_value = None
        cloud_api.get_encoder_data.return_value = {'data': [{'time': 1.0, 'pulses': 5, 'motorId': 2}]}
        cloud_api.get_heat_data.return_value = None
        mock_bsc.get_cloud_api.return_value = cloud_api

        session = SessionData(id=13, name="Diag Cloud", timeStamp=dt.datetime.now(), isShotMode=False)
        dc = DataController(session)

        dc.load_session_data_from_cloud(session)

        assert len(dc.get_diagnostic_script_data()) == 1
        assert len(dc.get_shot_script_data()) == 0


# Test 17: DataController load_session_data_from_cloud - Missing Cloud Data
def test_DataController_load_session_data_from_cloud_missing_data():
    """Test loading when cloud returns no data"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.get_shot_script_data_by_session.return_value = None
        cloud_api.get_diagnostic_script_data_by_session.return_value = None
        cloud_api.get_smartdot_data.return_value = None
        cloud_api.get_encoder_data.return_value = None
        cloud_api.get_heat_data.return_value = None
        mock_bsc.get_cloud_api.return_value = cloud_api

        session = SessionData(id=14, name="No Cloud", timeStamp=dt.datetime.now(), isShotMode=True)
        dc = DataController(session)

        dc.load_session_data_from_cloud(session)

        assert len(dc.get_shot_script_data()) == 0
        assert len(dc.get_diagnostic_script_data()) == 0
        assert len(dc.get_smartdot_data()) == 0
        assert len(dc.get_encoder_data()) == 0
        assert len(dc.get_heat_data()) == 0


# Test 18: DataController __str__ representation
def test_DataController_string_representation():
    """Test DataController __str__() method"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        mock_bsc.get_cloud_api.return_value = Mock()
        session = SessionData(id=15, name="Str", timeStamp=dt.datetime.now(), isShotMode=True)
        dc = DataController(session)
        dc.add_shot_script_data(ShotScriptDataInstance(time=1.0, rpm=1000, angleDeg=5.0, tiltDeg=1.0))

        s = str(dc)

        assert "DataController" in s
        assert "ShotScriptData" in s


# Test 19: DataController submit_session_data with smartdot data
def test_DataController_submit_session_data_with_smartdot_template():
    """Template: submit session data when smartdot entries exist"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.post_session_data.return_value = {'data': [500]}
        mock_bsc.get_cloud_api.return_value = cloud_api

        session = SessionData(id=16, name="SmartDot", timeStamp=dt.datetime.now(), isShotMode=True)
        dc = DataController(session)
        dc.add_smartdot_data(
            SmartDotDataInstance(
                time=dt.datetime.now(), data_selector=0,
                accelerometer_x=1, accelerometer_y=2, accelerometer_z=3,
                gyroscope_x=4, gyroscope_y=5, gyroscope_z=6,
                magnetometer_x=7, magnetometer_y=8, magnetometer_z=9,
                light=10
            )
        )

        dc.submit_session_data()

        cloud_api.post_smartdot_data.assert_called_once()


# Test 20: DataController submit_session_data logs when no script data
def test_DataController_submit_session_data_logs_when_no_script_template(caplog):
    """Template: ensure warning logged if script data missing"""
    with patch('backend.models.DataController.bsc') as mock_bsc:
        cloud_api = Mock()
        cloud_api.post_session_data.return_value = {'data': [600]}
        mock_bsc.get_cloud_api.return_value = cloud_api

        session = SessionData(id=17, name="Warn", timeStamp=dt.datetime.now(), isShotMode=True)
        dc = DataController(session)

        with caplog.at_level("WARNING"):
            dc.submit_session_data()

        assert any("No Shot Script Data" in rec.message for rec in caplog.records)
