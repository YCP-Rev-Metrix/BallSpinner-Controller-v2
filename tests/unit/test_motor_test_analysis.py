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
        settle_threshold=0.05,
        steady_state_window=3,
    )

    assert analysis["rise_time"] == pytest.approx(0.3)
    assert analysis["time_above_target"] == pytest.approx(0.1)
    assert analysis["time_below_target"] == pytest.approx(0.4)
    assert analysis["overshoot_pct"] == pytest.approx(2.0)
    assert analysis["undershoot_pct"] == pytest.approx(100.0 - 0.0)
    assert analysis["rmse"] is not None
    assert analysis["iae"] is not None
    assert analysis["ise"] is not None


def test_analyze_motor_response_empty():
    analysis = AnalyzeMotorResponse(
        target_speed=0,
        timestamps=[],
        current_speeds=[],
        sample_interval=0.1,
    )

    assert analysis["rise_time"] is None
    assert analysis["settling_time"] is None
    assert analysis["rmse"] is None
    assert analysis["ia"+"e"] is None
