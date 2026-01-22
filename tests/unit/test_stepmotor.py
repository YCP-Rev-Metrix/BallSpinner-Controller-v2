import pytest


def test_StepMotor_initialization_template():
    """StepMotor requires lgpio which is not available in test environment"""
    pytest.skip("StepMotor requires lgpio module - only available on Raspberry Pi")


def test_StepMotor_step_control_template():
    """StepMotor requires lgpio which is not available in test environment"""
    pytest.skip("StepMotor requires lgpio module - only available on Raspberry Pi")
