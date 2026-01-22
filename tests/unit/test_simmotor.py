import pytest

from backend.motors.SimMotor import SimMotor


def test_SimMotor_initialization():
    """Test SimMotor initializes with correct defaults"""
    motor = SimMotor(GPIOPin=17)

    assert motor.currSpeed == 0.0


def test_SimMotor_start_stop():
    """Test SimMotor can start and stop"""
    motor = SimMotor(GPIOPin=17)

    motor.start()
    # Motor simulates start behavior

    motor.stop()
    # Motor simulates stop behavior
    assert motor.currSpeed >= 0


def test_SimMotor_changeSpeed():
    """Test SimMotor changes speed correctly"""
    motor = SimMotor(GPIOPin=17)

    motor.changeSpeed(dutyCycle=50, isShotMode=False)
    assert motor.getCurrentSpeed() == 50

    motor.changeSpeed(dutyCycle=75, isShotMode=False)
    assert motor.getCurrentSpeed() == 75


def test_SimMotor_getCurrentSpeed():
    """Test SimMotor returns current speed"""
    motor = SimMotor(GPIOPin=17)

    motor.changeSpeed(dutyCycle=60, isShotMode=False)
    speed = motor.getCurrentSpeed()

    assert speed == 60
