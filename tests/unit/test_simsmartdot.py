import pytest

from backend.smartdot.SimSmartDot import SimSmartDot


def test_SimSmartDot_initialization():
    """Test SimSmartDot initializes with correct structure"""
    smartdot = SimSmartDot(MAC_Address="00:11:22:33:44:55")

    assert hasattr(smartdot, 'xl_x')
    assert hasattr(smartdot, 'gy_x')
    assert hasattr(smartdot, 'mg_x')
    assert hasattr(smartdot, 'lt_value')


def test_SimSmartDot_connect():
    """Test SimSmartDot connect state"""
    smartdot = SimSmartDot(MAC_Address="00:11:22:33:44:55")

    assert smartdot.connected is True


def test_SimSmartDot_disconnect():
    """Test SimSmartDot disconnect state"""
    smartdot = SimSmartDot(MAC_Address="00:11:22:33:44:55")

    assert smartdot.connected is True

    smartdot.disconnect()
    assert smartdot.connected is False
