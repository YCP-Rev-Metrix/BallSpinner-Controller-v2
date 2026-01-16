import pytest
from unittest.mock import patch, mock_open, MagicMock
from utils import is_raspberry_pi, is_raspberry_pi_5
from backend.models.SessionData import SessionData
from backend.models.EncoderData import EncoderData, EncoderDataInstance
from backend.models.HeatData import HeatData, HeatDataInstance
from backend.models.DiagnosticScriptData import DiagnosticScriptData, DiagnosticScriptDataInstance
import datetime as dt


# ============================================================================
# UTILITY TESTS (utils.py)
# ============================================================================


# Test 1: File exists and contains "Raspberry Pi"
def test_is_raspberry_pi_true_on_pi():
    """Test returns True when running on actual Raspberry Pi"""
    with patch('utils.io.open', mock_open(read_data="Raspberry Pi 4")):
        result = is_raspberry_pi()
        assert result is True


# Test 2: File doesn't exist (FileNotFoundError)
def test_is_raspberry_pi_false_file_not_found():
    """Test returns False when device tree file not found"""
    with patch('utils.io.open', side_effect=FileNotFoundError):
        result = is_raspberry_pi()
        assert result is False


# Test 3: File exists but is not a Raspberry Pi
def test_is_raspberry_pi_false_not_pi():
    """Test returns False on non-Pi system"""
    with patch('utils.io.open', mock_open(read_data="Generic Linux Device")):
        result = is_raspberry_pi()
        assert result is False

# Test 4: is_raspberry_pi_5() returns True on Pi 5
def test_is_raspberry_pi_5_true_on_pi5():
    """Test returns True when running on Raspberry Pi 5"""
    with patch('utils.io.open', mock_open(read_data="Raspberry Pi 5")):
        result = is_raspberry_pi_5()
        assert result is True

# Test 5: is_raspberry_pi_5() returns False on other Pi versions
def test_is_raspberry_pi_5_false_on_other_pi():
    """Test returns False on Raspberry Pi 4 or other versions"""
    with patch('utils.io.open', mock_open(read_data="Raspberry Pi 4")):
        result = is_raspberry_pi_5()
        assert result is False


# Test 6: is_raspberry_pi_5() returns False when file not found
def test_is_raspberry_pi_5_false_file_not_found():
    """Test returns False when device tree file not found"""
    with patch('utils.io.open', side_effect=FileNotFoundError):
        result = is_raspberry_pi_5()
        assert result is False


# ============================================================================
# DATA MODEL TESTS - SessionData (backend/models/SessionData.py)
# ============================================================================

# Test 7: SessionData initialization with valid values
def test_SessionData_initialization():
    """Test SessionData accepts and stores all parameters correctly"""
    test_id = 64
    test_timestamp = dt.datetime(2025,4,4,4,4,4)
    test_name = "Unit Test Session"
    test_is_shot_mode = True

    test_session = SessionData(test_id,
                                test_timestamp,
                                test_name,
                                test_is_shot_mode
                                )
    assert test_session.get_id() == test_id
    assert test_session.get_time_stamp() == test_timestamp
    assert test_session.get_name() == test_name
    assert test_session.get_is_shot_mode() == test_is_shot_mode


# Test 8: SessionData defaults id to -1 when None is passed
def test_SessionData_initialization_none_id():
    """Test SessionData defaults id to -1 when None is passed"""
    test_session = SessionData(None,
                                dt.datetime.now(),
                                "Test Session",
                                False
                                )
    assert test_session.get_id() == -1
    

# Test 9: SessionData with isShotMode=False
def test_SessionData_initialization_diagnostic_mode():
    """Test SessionData works correctly in diagnostic mode (isShotMode=False)"""
    test_id = 100
    test_timestamp = dt.datetime(2025, 2, 20, 14, 45, 30)
    test_name = "Diagnostic Session"
    test_is_shot_mode = False
    
    session = SessionData(
        id=test_id,
        timeStamp=test_timestamp,
        name=test_name,
        isShotMode=test_is_shot_mode
    )
    
    assert session.get_is_shot_mode() is False


# Test 10: SessionData string representation
def test_SessionData_string_representation():
    """Test __str__() returns proper format"""
    test_id = 42
    test_timestamp = dt.datetime(2025, 1, 16, 10, 30, 0)
    test_name = "Test Session"
    test_is_shot_mode = True
    
    session = SessionData(
        id=test_id,
        timeStamp=test_timestamp,
        name=test_name,
        isShotMode=test_is_shot_mode
    )
    
    session_str = str(session)
    assert "SessionData" in session_str
    assert str(test_id) in session_str
    assert test_name in session_str
    assert "True" in session_str  # isShotMode=True


# ============================================================================
# DATA MODEL TESTS - EncoderData (backend/models/EncoderData.py)
# ============================================================================

# Test 11: EncoderDataInstance initialization
def test_EncoderDataInstance_initialization():
    """Test EncoderDataInstance accepts and stores all parameters correctly"""
    test_time = 1.5
    test_pulses = 250.0
    test_motor_id = 2
    
    encoder_data = EncoderDataInstance(
        time=test_time,
        pulses=test_pulses,
        motor_id=test_motor_id
    )
    
    assert encoder_data.time == test_time
    assert encoder_data.pulses == test_pulses
    assert encoder_data.motor_id == test_motor_id


# Test 12: EncoderDataInstance string representation
def test_EncoderDataInstance_string_representation():
    """Test EncoderDataInstance __str__() returns proper format"""
    test_time = 2.5
    test_pulses = 500.0
    test_motor_id = 1
    
    encoder_data = EncoderDataInstance(
        time=test_time,
        pulses=test_pulses,
        motor_id=test_motor_id
    )
    
    encoder_str = str(encoder_data)
    assert "EncoderDataInstance" in encoder_str
    assert str(test_time) in encoder_str
    assert str(test_pulses) in encoder_str
    assert str(test_motor_id) in encoder_str


# Test 13: EncoderData add_encoder_data single entry
def test_EncoderData_add_single_entry():
    """Test adding a single encoder data instance"""
    encoder_data_container = EncoderData()
    encoder_instance = EncoderDataInstance(time=1.0, pulses=100.0, motor_id=1)
    
    encoder_data_container.add_encoder_data(encoder_instance)
    
    entries = encoder_data_container.get_encoder_data_entries()
    assert len(entries) == 1
    assert entries[0] == encoder_instance


# Test 14: EncoderData add_encoder_data multiple entries
def test_EncoderData_add_multiple_entries():
    """Test adding multiple encoder data instances"""
    encoder_data_container = EncoderData()
    instances = [
        EncoderDataInstance(time=1.0, pulses=100.0, motor_id=1),
        EncoderDataInstance(time=2.0, pulses=200.0, motor_id=2),
        EncoderDataInstance(time=3.0, pulses=300.0, motor_id=3)
    ]
    
    for instance in instances:
        encoder_data_container.add_encoder_data(instance)
    
    entries = encoder_data_container.get_encoder_data_entries()
    assert len(entries) == 3
    assert entries[0] == instances[0]
    assert entries[1] == instances[1]
    assert entries[2] == instances[2]


# Test 15: EncoderData get_encoder_data_entries
def test_EncoderData_get_entries():
    """Test getting encoder data entries"""
    encoder_data_container = EncoderData()
    instance1 = EncoderDataInstance(time=1.5, pulses=150.0, motor_id=1)
    instance2 = EncoderDataInstance(time=2.5, pulses=250.0, motor_id=2)
    
    encoder_data_container.add_encoder_data(instance1)
    encoder_data_container.add_encoder_data(instance2)
    
    entries = encoder_data_container.get_encoder_data_entries()
    assert len(entries) == 2
    assert entries[0].get_time() == 1.5
    assert entries[1].get_pulses() == 250.0


# Test 16: EncoderData empty state
def test_EncoderData_empty():
    """Test EncoderData when no entries added"""
    encoder_data_container = EncoderData()
    
    entries = encoder_data_container.get_encoder_data_entries()
    assert entries == []
    assert len(entries) == 0


# Test 17: EncoderData string representation
def test_EncoderData_string_representation():
    """Test EncoderData __str__() returns proper format"""
    encoder_data_container = EncoderData()
    instance = EncoderDataInstance(time=1.0, pulses=100.0, motor_id=1)
    encoder_data_container.add_encoder_data(instance)
    
    encoder_str = str(encoder_data_container)
    assert "EncoderData" in encoder_str
    assert "encoder_data_entries" in encoder_str


# ============================================================================
# DATA MODEL TESTS - HeatData (backend/models/HeatData.py)
# ============================================================================

# Test 18: HeatDataInstance initialization
def test_HeatDataInstance_initialization():
    """Test HeatDataInstance accepts and stores all parameters correctly"""
    test_time = 3.5
    test_motor_id = 1
    test_value = 85.5
    
    heat_data = HeatDataInstance(
        time=test_time,
        motor_id=test_motor_id,
        value=test_value
    )
    
    assert heat_data.time == test_time
    assert heat_data.motor_id == test_motor_id
    assert heat_data.value == test_value


# Test 19: HeatDataInstance string representation
def test_HeatDataInstance_string_representation():
    """Test HeatDataInstance __str__() returns proper format"""
    test_time = 4.5
    test_motor_id = 2
    test_value = 92.3
    
    heat_data = HeatDataInstance(
        time=test_time,
        motor_id=test_motor_id,
        value=test_value
    )
    
    heat_str = str(heat_data)
    assert "HeatDataInstance" in heat_str
    assert str(test_time) in heat_str
    assert str(test_motor_id) in heat_str
    assert str(test_value) in heat_str


# Test 20: HeatData add_heat_data single entry
def test_HeatData_add_single_entry():
    """Test adding a single heat data instance"""
    heat_data_container = HeatData()
    heat_instance = HeatDataInstance(time=1.0, motor_id=1, value=75.0)
    
    heat_data_container.add_heat_data(heat_instance)
    
    entries = heat_data_container.get_heat_data_entries()
    assert len(entries) == 1
    assert entries[0] == heat_instance


# Test 21: HeatData add_heat_data multiple entries
def test_HeatData_add_multiple_entries():
    """Test adding multiple heat data instances"""
    heat_data_container = HeatData()
    instances = [
        HeatDataInstance(time=1.0, motor_id=1, value=75.0),
        HeatDataInstance(time=2.0, motor_id=2, value=80.5),
        HeatDataInstance(time=3.0, motor_id=3, value=88.2)
    ]
    
    for instance in instances:
        heat_data_container.add_heat_data(instance)
    
    entries = heat_data_container.get_heat_data_entries()
    assert len(entries) == 3
    assert entries[0] == instances[0]
    assert entries[1] == instances[1]
    assert entries[2] == instances[2]


# Test 22: HeatData get_heat_data_entries
def test_HeatData_get_entries():
    """Test getting heat data entries"""
    heat_data_container = HeatData()
    instance1 = HeatDataInstance(time=1.5, motor_id=1, value=76.5)
    instance2 = HeatDataInstance(time=2.5, motor_id=2, value=82.3)
    
    heat_data_container.add_heat_data(instance1)
    heat_data_container.add_heat_data(instance2)
    
    entries = heat_data_container.get_heat_data_entries()
    assert len(entries) == 2
    assert entries[0].get_time() == 1.5
    assert entries[1].get_value() == 82.3


# Test 23: HeatData empty state
def test_HeatData_empty():
    """Test HeatData when no entries added"""
    heat_data_container = HeatData()
    
    entries = heat_data_container.get_heat_data_entries()
    assert entries == []
    assert len(entries) == 0


# Test 24: HeatData string representation
def test_HeatData_string_representation():
    """Test HeatData __str__() returns proper format"""
    heat_data_container = HeatData()
    instance = HeatDataInstance(time=1.0, motor_id=1, value=75.0)
    heat_data_container.add_heat_data(instance)
    
    heat_str = str(heat_data_container)
    assert "HeatData" in heat_str


# ============================================================================
# DATA MODEL TESTS - DiagnosticScriptData (backend/models/DiagnosticScriptData.py)
# ============================================================================

# Test 25: DiagnosticScriptDataInstance initialization
def test_DiagnosticScriptDataInstance_initialization():
    """Test DiagnosticScriptDataInstance accepts and stores all parameters correctly"""
    test_time = 2.5
    test_motor_id = 1
    test_instruction = 50.0
    
    diagnostic_data = DiagnosticScriptDataInstance(
        time=test_time,
        motor_id=test_motor_id,
        instruction=test_instruction
    )
    
    assert diagnostic_data.time == test_time
    assert diagnostic_data.motor_id == test_motor_id
    assert diagnostic_data.instruction == test_instruction


# Test 26: DiagnosticScriptDataInstance string representation
def test_DiagnosticScriptDataInstance_string_representation():
    """Test DiagnosticScriptDataInstance __str__() returns proper format"""
    test_time = 3.5
    test_motor_id = 2
    test_instruction = 75.0
    
    diagnostic_data = DiagnosticScriptDataInstance(
        time=test_time,
        motor_id=test_motor_id,
        instruction=test_instruction
    )
    
    diagnostic_str = str(diagnostic_data)
    assert "DiagnosticScriptDataInstance" in diagnostic_str
    assert str(test_time) in diagnostic_str
    assert str(test_motor_id) in diagnostic_str
    assert str(test_instruction) in diagnostic_str


# Test 27: DiagnosticScriptData add_diagnostic_script_data single entry
def test_DiagnosticScriptData_add_single_entry():
    """Test adding a single diagnostic script data instance"""
    diagnostic_container = DiagnosticScriptData()
    diagnostic_instance = DiagnosticScriptDataInstance(time=1.0, motor_id=1, instruction=25.0)
    
    diagnostic_container.add_diagnostic_script_data(diagnostic_instance)
    
    entries = diagnostic_container.get_diagnostic_script_data()
    assert len(entries) == 1
    assert entries[0] == diagnostic_instance


# Test 28: DiagnosticScriptData add_diagnostic_script_data multiple entries
def test_DiagnosticScriptData_add_multiple_entries():
    """Test adding multiple diagnostic script data instances"""
    diagnostic_container = DiagnosticScriptData()
    instances = [
        DiagnosticScriptDataInstance(time=1.0, motor_id=1, instruction=25.0),
        DiagnosticScriptDataInstance(time=2.0, motor_id=2, instruction=50.0),
        DiagnosticScriptDataInstance(time=3.0, motor_id=3, instruction=75.0)
    ]
    
    for instance in instances:
        diagnostic_container.add_diagnostic_script_data(instance)
    
    entries = diagnostic_container.get_diagnostic_script_data()
    assert len(entries) == 3
    assert entries[0] == instances[0]
    assert entries[1] == instances[1]
    assert entries[2] == instances[2]


# Test 29: DiagnosticScriptData get_diagnostic_script_data
def test_DiagnosticScriptData_get_entries():
    """Test getting diagnostic script data entries"""
    diagnostic_container = DiagnosticScriptData()
    instance1 = DiagnosticScriptDataInstance(time=1.5, motor_id=1, instruction=30.0)
    instance2 = DiagnosticScriptDataInstance(time=2.5, motor_id=2, instruction=60.0)
    
    diagnostic_container.add_diagnostic_script_data(instance1)
    diagnostic_container.add_diagnostic_script_data(instance2)
    
    entries = diagnostic_container.get_diagnostic_script_data()
    assert len(entries) == 2
    assert entries[0].time == 1.5
    assert entries[1].instruction == 60.0


# Test 30: DiagnosticScriptData empty state
def test_DiagnosticScriptData_empty():
    """Test DiagnosticScriptData when no entries added"""
    diagnostic_container = DiagnosticScriptData()
    
    entries = diagnostic_container.get_diagnostic_script_data()
    assert entries == []
    assert len(entries) == 0


# Test 31: DiagnosticScriptData string representation
def test_DiagnosticScriptData_string_representation():
    """Test DiagnosticScriptData __str__() returns proper format"""
    diagnostic_container = DiagnosticScriptData()
    instance = DiagnosticScriptDataInstance(time=1.0, motor_id=1, instruction=25.0)
    diagnostic_container.add_diagnostic_script_data(instance)
    
    diagnostic_str = str(diagnostic_container)
    assert "DiagnosticScriptData" in diagnostic_str
