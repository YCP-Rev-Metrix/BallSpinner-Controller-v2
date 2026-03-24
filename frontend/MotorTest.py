import os
import sys
import time

# Ensure the project root is on sys.path so imports like `from BSC import BSC` work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from BSC import BSC


def CharacterizeMotors(self=None, bsc=None, target_speeds=None, hold_time=5.0, sample_interval=0.1):
    """Run a speed sweep on motor1 and return the results for each target speed."""

    if bsc is None:
        bsc = BSC()

    if target_speeds is None:
        target_speeds = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700]

    results = []
    for speed in target_speeds:
        results.append(TestMotor(self, bsc, speed, hold_time, bsc.diagnostic_sample_interval_ms / 1000.0))
        print(f"Completed test for target speed {speed}. Waiting 3 seconds before next test...")
        time.sleep(3)

    return results


def TestMotor(self, bsc, target_speed, hold_time, sample_interval):
    """Run a single test at a given target speed and return the recorded data."""

    target_speeds = []
    current_speeds = []

    bsc.motor1.start()  # Ensure motor starts at 0 speed
    bsc.motor1.changeSpeed(target_speed, False)
    start_time = time.time()

    while time.time() - start_time < hold_time:
        bsc.motor1.changeSpeed(target_speed, False)
        current_speed = bsc.motor1.getCurrentSpeed()

        target_speeds.append(target_speed)
        current_speeds.append(current_speed)

        print(f"Target Speed: {target_speed} | Current Speed: {current_speed:.2f}")
        time.sleep(sample_interval)

    bsc.motor1.stop()  # Stop the motor after the test
    end_time = time.time()

    time_to_target = None
    for i, speed in enumerate(current_speeds):
        if speed >= target_speed:
            time_to_target = i * sample_interval
            break

    overshoot = max(current_speeds) - target_speed if current_speeds else 0.0

    timestamps = [i * sample_interval for i in range(len(current_speeds))]

    response_analysis = AnalyzeMotorResponse(
        target_speed=target_speed,
        timestamps=timestamps,
        current_speeds=current_speeds,
        sample_interval=sample_interval,
    )

    return {
        "target_speed": target_speed,
        "target_speeds": target_speeds,
        "current_speeds": current_speeds,
        "timestamps": timestamps,
        "sample_interval": sample_interval,
        "overshoot": overshoot,
        "time_to_target": time_to_target,
        "runtime": end_time - start_time,
        "analysis": response_analysis,
    }


def AnalyzeMotorResponse(
    target_speed,
    timestamps,
    current_speeds,
    sample_interval,
    settle_threshold=0.05,
    steady_state_window=10,
):
    """Compute control metrics for a test waveform."""
    if not timestamps or not current_speeds:
        return {
            "rise_time": None,
            "settling_time": None,
            "steady_state_error_mean": None,
            "steady_state_error_std": None,
            "rmse": None,
            "iae": None,
            "ise": None,
            "max_error": None,
            "min_error": None,
            "time_above_target": 0.0,
            "time_below_target": 0.0,
            "overshoot_pct": None,
            "undershoot_pct": None,
            "variance": None,
            "std_dev": None,
        }

    errors = [target_speed - speed for speed in current_speeds]
    abs_errors = [abs(e) for e in errors]
    sq_errors = [e * e for e in errors]

    rise_time = None
    target_90 = 0.9 * target_speed
    for i, speed in enumerate(current_speeds):
        if speed >= target_90:
            rise_time = i * sample_interval
            break

    settling_time = None
    tolerance = settle_threshold * target_speed
    for i in range(len(current_speeds)):
        window = current_speeds[i:]
        if all(abs(v - target_speed) <= tolerance for v in window):
            settling_time = i * sample_interval
            break

    steady_samples = current_speeds[-steady_state_window:] if len(current_speeds) >= steady_state_window else current_speeds
    steady_errors = [target_speed - v for v in steady_samples]

    mean_error = sum(steady_errors) / len(steady_errors) if steady_errors else None
    variance = (
        sum((v - (sum(current_speeds) / len(current_speeds))) ** 2 for v in current_speeds) / len(current_speeds)
        if current_speeds
        else None
    )
    std_dev = variance ** 0.5 if variance is not None else None

    iae = sum(abs_errors) * sample_interval
    ise = sum(sq_errors) * sample_interval
    rmse = (sum(sq_errors) / len(sq_errors)) ** 0.5 if sq_errors else None

    time_above_target = sum(1 for v in current_speeds if v > target_speed) * sample_interval
    time_below_target = sum(1 for v in current_speeds if v < target_speed) * sample_interval

    overshoot = max(current_speeds) - target_speed
    undershoot = target_speed - min(current_speeds)

    return {
        "rise_time": rise_time,
        "settling_time": settling_time,
        "steady_state_error_mean": mean_error,
        "steady_state_error_std": (
            (sum((e - mean_error) ** 2 for e in steady_errors) / len(steady_errors)) ** 0.5
            if steady_errors and mean_error is not None
            else None
        ),
        "rmse": rmse,
        "iae": iae,
        "ise": ise,
        "max_error": max(errors),
        "min_error": min(errors),
        "time_above_target": time_above_target,
        "time_below_target": time_below_target,
        "overshoot_pct": (overshoot / target_speed) * 100 if target_speed else None,
        "undershoot_pct": (undershoot / target_speed) * 100 if target_speed else None,
        "variance": variance,
        "std_dev": std_dev,
    }


def tune_duty_cycle_scale(
    self=None,
    bsc=None,
    target_speed=300,
    hold_time=5.0,
    sample_interval=0.1,
    scale_candidates=None,
):
    """Find the duty cycle scale factor that yields the smallest overshoot for a given target speed."""

    if bsc is None:
        bsc = BSC()

    if not hasattr(bsc.motor1, "duty_cycle_scale"):
        print("Motor does not support duty_cycle_scale tuning; skipping scale sweep.")
        return None

    if scale_candidates is None:
        # A wider range around the default scale used by USBBDCMotor.
        # The best scale may be significantly smaller or larger than the current default.
        base_scale = 0.000043333333
        multipliers = [0.25, 0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 3.0]
        scale_candidates = [base_scale * m for m in multipliers]

    best = None
    best_abs_overshoot = float("inf")
    results = []

    for scale in scale_candidates:
        bsc.motor1.duty_cycle_scale = scale
        test_result = TestMotor(self, bsc, target_speed, hold_time, sample_interval)
        overshoot = test_result["overshoot"]
        abs_overshoot = abs(overshoot)
        results.append({
            "scale": scale,
            "overshoot": overshoot,
            "abs_overshoot": abs_overshoot,
        })

        if abs_overshoot < best_abs_overshoot:
            best_abs_overshoot = abs_overshoot
            best = results[-1]

    print("\n===== Duty Cycle Scale Tuning =====")
    for r in results:
        print(
            f"Scale={r['scale']:.9f} | Overshoot={r['overshoot']:.2f} | Abs={r['abs_overshoot']:.2f}"
        )

    if best is not None:
        print(
            f"\nBest scale {best['scale']:.9f} (abs overshoot {best['abs_overshoot']:.2f})"
        )

    return {
        "best": best,
        "results": results,
    }


def main():
    results = CharacterizeMotors(None)
    print("\n===== Motor Characterization Results =====")
    for r in results:
        print(
            f"Target {r['target_speed']:>4} | "
            f"TimeToTarget={r['time_to_target']}s | "
            f"Overshoot={r['overshoot']:.2f} | "
            f"Runtime={r['runtime']:.2f}s"
        )

    # Example of tuning the duty cycle scale to minimize overshoot.
    tune_duty_cycle_scale(None)

    return results


if __name__ == "__main__":
    main()

