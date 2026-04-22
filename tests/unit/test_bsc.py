import pytest
from unittest.mock import MagicMock

import BSC as BSC_module


def test_BSC_initializes_simulated_when_not_pi(monkeypatch):
    """BSC should initialize in simulated mode on non-Pi hardware."""
    monkeypatch.setattr(BSC_module.utils, 'is_raspberry_pi_5', lambda: False)

    bsc = BSC_module.BSC()

    assert bsc.motor_mode == 'simulated'
    assert bsc.motor_mode_locked is True
    assert bsc.motor_mode_locked_reason == 'Simulated motors locked.'
    assert bsc.motor1 is not None
    assert bsc.motor2 is not None
    assert bsc.motor3 is not None


def test_BSC_falls_back_to_simulation_when_real_initialization_fails(monkeypatch):
    """BSC should fall back to simulated motors if real motor startup fails."""
    monkeypatch.setattr(BSC_module.utils, 'is_raspberry_pi_5', lambda: True)
    monkeypatch.setattr(BSC_module, 'USBBDCMotor', None)
    monkeypatch.setattr(BSC_module, 'StepMotor', None)
    monkeypatch.setattr(BSC_module, 'lgpio', MagicMock())

    bsc = BSC_module.BSC()

    assert bsc.motor_mode == 'simulated'
    assert bsc.motor_mode_locked is True
    assert bsc.motor_mode_locked_reason == 'Simulated motors locked.'


def test_BSC_set_motor_mode_real_fails_when_unavailable(monkeypatch):
    """set_motor_mode('real') should fail and keep simulated mode when real motors are unavailable."""
    monkeypatch.setattr(BSC_module.utils, 'is_raspberry_pi_5', lambda: False)

    bsc = BSC_module.BSC()
    assert bsc.motor_mode == 'simulated'

    result = bsc.set_motor_mode('real')

    assert result is False
    assert bsc.motor_mode == 'simulated'
    assert bsc.motor_mode_locked is True
    assert bsc.motor_mode_locked_reason == 'Simulated motors locked.'


def test_BSC_set_motor_mode_simulated_on_pi_assigns_all_simulated(monkeypatch):
    """All three motors should be simulated when simulated mode is selected on Raspberry Pi."""
    monkeypatch.setattr(BSC_module.utils, 'is_raspberry_pi_5', lambda: True)

    class DummyUSBBDCMotor:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyStepMotor:
        def __init__(
            self,
            gpio_a,
            gpio_b,
            h,
            channel,
            inverted,
            current_sensor=None,
            current_sensor_channel=None,
            positive_limit_pin=None,
            negative_limit_pin=None,
        ):
            self.gpio_a = gpio_a
            self.gpio_b = gpio_b
            self.h = h
            self.channel = channel
            self.inverted = inverted
            self.current_sensor = current_sensor
            self.current_sensor_channel = current_sensor_channel
            self.positive_limit_pin = positive_limit_pin
            self.negative_limit_pin = negative_limit_pin

    dummy_lgpio = MagicMock()
    dummy_lgpio.gpiochip_open.return_value = 'dummy-handle'
    dummy_lgpio.gpiochip_close.return_value = None

    monkeypatch.setattr(BSC_module, 'USBBDCMotor', DummyUSBBDCMotor)
    monkeypatch.setattr(BSC_module, 'StepMotor', DummyStepMotor)
    monkeypatch.setattr(BSC_module, 'lgpio', dummy_lgpio)

    bsc = BSC_module.BSC()
    assert bsc.motor_mode == 'real'
    assert not isinstance(bsc.motor1, BSC_module.SimMotor)

    result = bsc.set_motor_mode('simulated')

    assert result is True
    assert bsc.motor_mode == 'simulated'
    assert isinstance(bsc.motor1, BSC_module.SimMotor)
    assert isinstance(bsc.motor2, BSC_module.SimMotor)
    assert isinstance(bsc.motor3, BSC_module.SimMotor)


def test_BSC_passes_limit_pins_to_stepper(monkeypatch):
    monkeypatch.setattr(BSC_module.utils, 'is_raspberry_pi_5', lambda: True)

    class DummyUSBBDCMotor:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyStepMotor:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

    dummy_lgpio = MagicMock()
    dummy_lgpio.gpiochip_open.return_value = 'dummy-handle'
    dummy_lgpio.gpiochip_close.return_value = None

    monkeypatch.setattr(BSC_module, 'USBBDCMotor', DummyUSBBDCMotor)
    monkeypatch.setattr(BSC_module, 'StepMotor', DummyStepMotor)
    monkeypatch.setattr(BSC_module, 'lgpio', dummy_lgpio)

    bsc = BSC_module.BSC()

    assert bsc.motor2.kwargs["positive_limit_pin"] == BSC_module.BSC.POSITIVE_LIMIT_PIN
    assert bsc.motor2.kwargs["negative_limit_pin"] == BSC_module.BSC.NEGATIVE_LIMIT_PIN
    assert bsc.motor3.kwargs["positive_limit_pin"] == BSC_module.BSC.POSITIVE_LIMIT_PIN
    assert bsc.motor3.kwargs["negative_limit_pin"] == BSC_module.BSC.NEGATIVE_LIMIT_PIN


def test_BSC_home_calls_motor2_and_motor3(monkeypatch):
    monkeypatch.setattr(BSC_module.utils, 'is_raspberry_pi_5', lambda: False)
    bsc = BSC_module.BSC()

    bsc.motor2 = MagicMock()
    bsc.motor3 = MagicMock()

    bsc.home()

    bsc.motor2.home.assert_called_once()
    bsc.motor3.home.assert_called_once()
