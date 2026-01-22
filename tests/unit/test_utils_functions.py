import pytest
from unittest.mock import patch, mock_open
from utils import is_raspberry_pi, is_raspberry_pi_5


# ============================================================================
# UTILITY FUNCTION TESTS (utils.py)
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
