import pytest

from frontend.MotorTest import AnalyzeMotorResponse


def test_analyze_motor_response_basic():
    target_speed = 100.0
    sample_interval = 0.1
    timestamps = [0.0, 0.1, 0.2, 0.3, 0.4]
    current_speeds = [0.0, 30.0, 80.0, 95.0, 102.0]

    analysis = AnalyzeMotorResponse(
        target_speed=target_speed,
        timestamps=timestamps,
        current_speeds=current_speeds,
        sample_interval=sample_interval,
        time_to_target=0.3,
    )

    assert analysis["min_speed"] == pytest.approx(95.0)
    assert analysis["max_speed"] == pytest.approx(102.0)
    assert analysis["mean_speed"] == pytest.approx((95.0 + 102.0) / 2)
    assert analysis["average_error"] == pytest.approx(((95.0 - 100.0) + (102.0 - 100.0)) / 2)


def test_analyze_motor_response_empty():
    analysis = AnalyzeMotorResponse(
        target_speed=0,
        timestamps=[],
        current_speeds=[],
        sample_interval=0.1,
    )

    assert analysis == {}
