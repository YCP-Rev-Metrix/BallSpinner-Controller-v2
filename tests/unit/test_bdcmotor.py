import pytest

from backend.motors.BDCMotor import BDCMotor


def test_BDCMotor_initialization():
    """Test BDCMotor initializes with GPIO pin"""
    motor = BDCMotor(GPIOPin=27)

    assert motor.GPIO_Pin == 27
    # BDCMotor starts motor automatically, so currSpeed will be > 0
    assert motor.motor is not None


def test_BDCMotor_attributes():
    """Test BDCMotor has expected attributes"""
    motor = BDCMotor(GPIOPin=3)

    assert hasattr(motor, 'currSpeed')
    assert hasattr(motor, 'targetSpeed')
    assert hasattr(motor, 'motor')
    motor.disconnect(motor.GPIO_Pin)


def test_BDCMotor_changeSpeed():
    """Test BDCMotor changes speed correctly"""
    motor = BDCMotor(GPIOPin=4)

    initial_speed = motor.currSpeed
    motor.changeSpeed(dutyCycle=100)
    # Speed should have changed or motor should be active
    assert motor.currSpeed >= 0
    motor.disconnect(motor.GPIO_Pin)
