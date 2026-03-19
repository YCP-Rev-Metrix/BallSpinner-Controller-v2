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

    return {
        "target_speed": target_speed,
        "target_speeds": target_speeds,
        "current_speeds": current_speeds,
        "timestamps": timestamps,
        "sample_interval": sample_interval,
        "overshoot": overshoot,
        "time_to_target": time_to_target,
        "runtime": end_time - start_time,
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
        # A small range around the default scale used by USBBDCMotor
        scale_candidates = [
            0.000035,
            0.000038,
            0.000040,
            0.000042,
            0.000044,
            0.000046,
            0.000048,
            0.000050,
        ]

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

