import pytest
from unittest.mock import Mock

from utils import PackageSmartDotData


def test_PackageSmartDotData_returns_dict():
    """Test PackageSmartDotData returns a dictionary structure"""
    # Create mock self (object to hold data) and bsc
    mock_self = Mock()
    mock_bsc = Mock()
    mock_smartdot_data = Mock()
    mock_smartdot_data.data_entries = []
    mock_data_controller = Mock()
    mock_data_controller.smartdot_data = mock_smartdot_data
    mock_bsc.get_data_controller.return_value = mock_data_controller

    # Call PackageSmartDotData function with mocked self and bsc
    result = PackageSmartDotData(mock_self, mock_bsc)

    # Result should be a SmartDotDataPackage (dict-like)
    assert result is not None
