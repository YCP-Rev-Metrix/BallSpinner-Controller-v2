import argparse
import json
import os
import sys
import time
import numpy as np

# Ensure the project root is on sys.path so imports like `from BSC import BSC` work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from BSC import BSC
from tuning_config import load_tuning_config


def _load_motor_test_config():
    config = load_tuning_config()
    return config.get("motor_test") or {}


def CharacterizeMotors(self=None, bsc=None, target_speeds=None, hold_time=None, sample_interval=None):
    """Run a speed sweep on motor1 and return the results for each target speed."""

    if bsc is None:
        bsc = BSC()

    test_cfg = _load_motor_test_config()

    if target_speeds is None:
        target_speeds = test_cfg.get(
            "target_speeds",
            [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700],
        )

    if hold_time is None:
        hold_time = test_cfg.get("hold_time_s", 5.0)

    if sample_interval is None:
        sample_interval = test_cfg.get("sample_interval_s", bsc.sample_interval_ms / 1000.0)

    dwell_time = test_cfg.get("dwell_time_s", 3.0)

    results = []
    for speed in target_speeds:
        results.append(TestMotor(self, bsc, speed, hold_time, sample_interval))
        print(f"Completed test for target speed {speed}. Waiting 3 seconds before next test...")
        time.sleep(dwell_time)

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


def AnalyzeMotorResponse(target_speed, timestamps, current_speeds, sample_interval, time_to_target=None):
    """Analyze the motor response to extract characteristics like rise time, settling time, etc."""

    if not current_speeds:
        return {}

    # remove data from before the motor gets to speed
    if time_to_target is not None:
        idx = int(round(time_to_target / sample_interval))
        if idx < 0:
            idx = 0
        timestamps = timestamps[idx:]
        current_speeds = current_speeds[idx:]

    speeds = np.array(current_speeds, dtype=float)
    times = np.array(timestamps, dtype=float)

    error = speeds - target_speed
    abs_error = np.abs(error)
    
    min_speed = float(np.min(speeds))
    max_speed = float(np.max(speeds))
    standard_deviation = float(np.std(speeds))
    variance = float(np.var(speeds))
    mean_speed = float(np.mean(speeds))
    median_speed = float(np.median(speeds))
    average_error = float(np.mean(error))
    average_abs_error = float(np.mean(abs_error))
    rms_error = float(np.sqrt(np.mean(np.square(error))))
    max_error = float(np.max(error))
    min_error = float(np.min(error))

    peak_idx = int(np.argmax(speeds))
    min_idx = int(np.argmin(speeds))
    peak_time = float(times[peak_idx])
    min_time = float(times[min_idx])

    overshoot = max_speed - target_speed
    undershoot = target_speed - min_speed
    overshoot_pct = None
    if target_speed != 0:
        overshoot_pct = (overshoot / target_speed) * 100.0

    # Rise time (10% -> 90%) and time-to-95% for positive targets.
    rise_time_10_90 = None
    time_to_95 = None
    if target_speed > 0:
        t10 = 0.1 * target_speed
        t90 = 0.9 * target_speed
        t95 = 0.95 * target_speed

        above_10 = np.where(speeds >= t10)[0]
        above_90 = np.where(speeds >= t90)[0]
        above_95 = np.where(speeds >= t95)[0]

        if above_10.size and above_90.size:
            rise_time_10_90 = float(times[above_90[0]] - times[above_10[0]])
        if above_95.size:
            time_to_95 = float(times[above_95[0]])

    # Settling time: first time after which the response stays within 2% of target.
    settle_time = None
    if target_speed != 0:
        tol = max(0.02 * abs(target_speed), 1.0)
        within = np.abs(speeds - target_speed) <= tol
        if np.all(within):
            settle_time = float(times[0])
        else:
            last_out = np.where(~within)[0]
            if last_out.size and last_out[-1] < len(times) - 1:
                settle_time = float(times[last_out[-1] + 1])

    # Steady-state stats from the last 10% of samples (minimum 3 points).
    tail_count = max(3, int(len(speeds) * 0.1))
    tail = speeds[-tail_count:]
    steady_state_mean = float(np.mean(tail))
    steady_state_std = float(np.std(tail))
    steady_state_error = steady_state_mean - target_speed

    # Max slew rate (RPM per second).
    max_slew_rate = None
    if len(speeds) >= 2:
        dt = np.diff(times)
        dv = np.diff(speeds)
        valid = dt > 0
        if np.any(valid):
            max_slew_rate = float(np.max(np.abs(dv[valid] / dt[valid])))
    
    return {
        "min_speed": min_speed,
        "max_speed": max_speed,
        "mean_speed": mean_speed,
        "median_speed": median_speed,
        "standard_deviation": standard_deviation,
        "variance": variance,
        "average_error": average_error,
        "average_abs_error": average_abs_error,
        "max_error": max_error,
        "min_error": min_error,
        "rms_error": rms_error,
        "overshoot": overshoot,
        "undershoot": undershoot,
        "overshoot_pct": overshoot_pct,
        "rise_time_10_90": rise_time_10_90,
        "time_to_95": time_to_95,
        "settle_time": settle_time,
        "steady_state_mean": steady_state_mean,
        "steady_state_std": steady_state_std,
        "steady_state_error": steady_state_error,
        "peak_time": peak_time,
        "min_time": min_time,
        "max_slew_rate": max_slew_rate,
    }
    





def tune_duty_cycle_scale(
    self=None,
    bsc=None,
    target_speed=300,
    hold_time=None,
    sample_interval=None,
    scale_candidates=None,
):
    """Find the duty cycle scale factor that yields the smallest overshoot for a given target speed."""

    if bsc is None:
        bsc = BSC()

    if not hasattr(bsc.motor1, "duty_cycle_scale"):
        print("Motor does not support duty_cycle_scale tuning; skipping scale sweep.")
        return None

    test_cfg = _load_motor_test_config()

    if hold_time is None:
        hold_time = test_cfg.get("hold_time_s", 5.0)

    if sample_interval is None:
        sample_interval = test_cfg.get("sample_interval_s", bsc.sample_interval_ms / 1000.0)

    if scale_candidates is None:
        scale_candidates = test_cfg.get("scale_candidates")

    if scale_candidates is None or not scale_candidates:
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


def _format_results_text(results):
    lines = ["===== Motor Characterization Results ====="]
    for r in results:
        lines.append(
            f"Target {r['target_speed']:>4} | "
            f"TimeToTarget={r['time_to_target']}s | "
            f"Overshoot={r['overshoot']:.2f} | "
            f"Runtime={r['runtime']:.2f}s"
        )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run spin motor diagnostics.")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--out", help="Write output to a file instead of stdout")
    parser.add_argument("--hold-time", type=float, help="Seconds to hold each target speed")
    parser.add_argument("--sample-interval", type=float, help="Seconds between samples")
    parser.add_argument("--target-speeds", help="Comma-separated list of target speeds")
    parser.add_argument("--skip-scale-tune", action="store_true", help="Skip duty scale sweep")

    args = parser.parse_args(argv)

    target_speeds = None
    if args.target_speeds:
        target_speeds = [float(s) for s in args.target_speeds.split(",") if s.strip()]

    results = CharacterizeMotors(
        None,
        None,
        target_speeds=target_speeds,
        hold_time=args.hold_time,
        sample_interval=args.sample_interval,
    )

    if args.json:
        output = json.dumps(results, indent=2)
    else:
        output = _format_results_text(results)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output)

    if not args.skip_scale_tune:
        tune_duty_cycle_scale(None)

    return results


if __name__ == "__main__":
    main()

