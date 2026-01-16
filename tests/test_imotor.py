import pytest

# from backend.motors.iMotor import iMotor


def test_iMotor_is_abstract_template():
    pytest.skip("template")
    # Steps:
    # 1) Attempt to instantiate iMotor and assert it raises TypeError (abstract).
    # 2) Optionally create a minimal subclass implementing abstract methods and ensure it instantiates.


def test_iMotor_required_methods_template():
    pytest.skip("template")
    # Steps:
    # 1) Inspect iMotor.__abstractmethods__ for expected method names (connect, disconnect, start, stop, changeSpeed, getCurrentSpeed, rampUp).
    # 2) Assert the set matches expectations.
