import pytest
from abc import ABC

from backend.motors.iMotor import iMotor


def test_iMotor_is_abstract():
    """Test iMotor cannot be instantiated directly"""
    with pytest.raises(TypeError):
        motor = iMotor()


def test_iMotor_has_abstract_methods():
    """Test iMotor defines required abstract methods"""
    abstract_methods = iMotor.__abstractmethods__
    
    # Should have core methods
    assert 'start' in abstract_methods
    assert 'stop' in abstract_methods
    assert 'changeSpeed' in abstract_methods
    assert 'getCurrentSpeed' in abstract_methods
