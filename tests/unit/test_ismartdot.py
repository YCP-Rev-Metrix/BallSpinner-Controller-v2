import pytest

from backend.smartdot.iSmartDot import iSmartDot


def test_iSmartDot_is_abstract():
    """Test iSmartDot cannot be instantiated directly"""
    with pytest.raises(TypeError):
        smartdot = iSmartDot()


def test_iSmartDot_data_structure():
    """Test iSmartDot subclass has required data structures"""
    from backend.smartdot.SimSmartDot import SimSmartDot

    smartdot = SimSmartDot(MAC_Address="00:11:22:33:44:55")

    # Should have sensor arrays
    assert hasattr(smartdot, 'xl_x')
    assert hasattr(smartdot, 'gy_x')
    assert hasattr(smartdot, 'mg_x')
    assert hasattr(smartdot, 'lt_value')
    
    # Should have locks for thread safety
    assert hasattr(smartdot, '_xl_lock')
    assert hasattr(smartdot, '_gy_lock')
    assert hasattr(smartdot, '_mg_lock')
    assert hasattr(smartdot, '_lt_lock')
