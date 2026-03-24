import pytest
import time

from backend.motors.SimMotor import SimMotor


def test_SimMotor_initialization():
    """Test SimMotor initializes with correct defaults"""
    motor = SimMotor(GPIOPin=17, mode='instant', noise_std=0.0)
    assert motor.currSpeed == 0.0


def test_SimMotor_start_stop():
    """Test SimMotor can start and stop"""
    motor = SimMotor(GPIOPin=17, mode='instant')

    motor.start()

    motor.stop()
    # Motor simulates stop behavior
    assert motor.currSpeed >= 0


def test_SimMotor_changeSpeed(monkeypatch):
    """Test SimMotor changes speed correctly"""
    # eliminate noise by patching random.uniform to zero
    import random
    monkeypatch.setattr(random, 'uniform', lambda a, b: 0)

    motor = SimMotor(GPIOPin=17, mode='instant', noise_std=0.0)

    motor.changeSpeed(dutyCycle=50, isShotMode=False)
    assert motor.getCurrentSpeed() == 50

    motor.changeSpeed(dutyCycle=75, isShotMode=False)
    assert motor.getCurrentSpeed() == 75


def test_SimMotor_getCurrentSpeed(monkeypatch):
    """Test SimMotor returns current speed"""
    import random
    monkeypatch.setattr(random, 'uniform', lambda a, b: 0)

    motor = SimMotor(GPIOPin=17, mode='instant', noise_std=0.0)

    motor.changeSpeed(dutyCycle=60, isShotMode=False)
    speed = motor.getCurrentSpeed()

    assert speed == 60

def test_SimMotor_noise_and_ramp():
    """Test SimMotor has noise and ramp behavior in vesc mode"""
    motor = SimMotor(GPIOPin=17, mode='vesc', max_speed=600, time_constant=0.2, noise_std=3.0)
    motor.start()

    motor.changeSpeed(dutyCycle=600, isShotMode=False)

    states = []
    for _ in range(20):
        time.sleep(0.02)
        states.append(motor.getCurrentSpeed())

    assert states[0] <= states[-1]
    assert any(abs(states[i] - states[i-1]) > 0 for i in range(1, len(states)))
    assert 0 <= states[-1] <= 600
