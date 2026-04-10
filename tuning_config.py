import copy
import json
import os

DEFAULT_TUNING_PATH = os.path.join(
    os.path.dirname(__file__),
    "config",
    "motor_tuning.json",
)

DEFAULT_TUNING_CONFIG = {
    "version": 1,
    "sample_interval_ms": 50,
    "motor1": {
        "duty_cycle_scale": 0.0000218,
        "kp": 0.05,
        "ki": 0.02,
        "kd": 0.0,
        "target_speed_min": 0.0,
        "target_speed_max": 1200.0,
        "integral_limit": 1200.0,
        "ramp_step": 2.0,
        "missed_speed_warn_threshold": 10,
        "kick": {
            "enabled": True,
            "min_target_rpm": 1.0,
            "threshold_divisor": 900.0,
            "duty_divisor": 6000.0,
            "max_duty": 1.0,
        },
        "comm": {
            "port": "/dev/ttyACM0",
            "baud": 115200,
            "serial_timeout_s": 0.05,
            "get_values_timeout_s": 0.2,
        },
    },
    "motor_test": {
        "target_speeds": [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700],
        "hold_time_s": 5.0,
        "sample_interval_s": 0.1,
        "dwell_time_s": 3.0,
        "scale_candidates": [],
    },
}


def _deep_update(dst, src):
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            _deep_update(dst[key], value)
        else:
            dst[key] = value
    return dst


def get_default_tuning_config():
    return copy.deepcopy(DEFAULT_TUNING_CONFIG)


def load_tuning_config(path=DEFAULT_TUNING_PATH):
    config = get_default_tuning_config()
    if not os.path.exists(path):
        return config

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            _deep_update(config, data)
    except Exception:
        return config

    return config


def save_tuning_config(config, path=DEFAULT_TUNING_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True)


def _as_float(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _as_int(value, fallback):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def apply_tuning_config(bsc, config, apply_comm=False):
    if not config:
        return

    interval_ms = config.get("sample_interval_ms")
    if isinstance(interval_ms, (int, float)):
        bsc.sample_interval_ms = interval_ms

    motor_cfg = config.get("motor1") or {}
    motor = getattr(bsc, "motor1", None)
    if motor is None:
        return

    if hasattr(motor, "duty_cycle_scale"):
        motor.duty_cycle_scale = _as_float(
            motor_cfg.get("duty_cycle_scale", motor.duty_cycle_scale),
            motor.duty_cycle_scale,
        )
    if hasattr(motor, "Kp"):
        motor.Kp = _as_float(motor_cfg.get("kp", motor.Kp), motor.Kp)
    if hasattr(motor, "Ki"):
        motor.Ki = _as_float(motor_cfg.get("ki", motor.Ki), motor.Ki)
    if hasattr(motor, "Kd"):
        motor.Kd = _as_float(motor_cfg.get("kd", motor.Kd), motor.Kd)

    if hasattr(motor, "target_speed_min"):
        motor.target_speed_min = _as_float(
            motor_cfg.get("target_speed_min", motor.target_speed_min),
            motor.target_speed_min,
        )
    if hasattr(motor, "target_speed_max"):
        motor.target_speed_max = _as_float(
            motor_cfg.get("target_speed_max", motor.target_speed_max),
            motor.target_speed_max,
        )
    if hasattr(motor, "integral_limit"):
        motor.integral_limit = _as_float(
            motor_cfg.get("integral_limit", motor.integral_limit),
            motor.integral_limit,
        )
    if hasattr(motor, "ramp_step"):
        motor.ramp_step = _as_float(motor_cfg.get("ramp_step", motor.ramp_step), motor.ramp_step)
    if hasattr(motor, "missed_speed_warn_threshold"):
        motor.missed_speed_warn_threshold = _as_int(
            motor_cfg.get("missed_speed_warn_threshold", motor.missed_speed_warn_threshold),
            motor.missed_speed_warn_threshold,
        )

    kick_cfg = motor_cfg.get("kick") or {}
    if hasattr(motor, "kick_enabled"):
        motor.kick_enabled = bool(kick_cfg.get("enabled", motor.kick_enabled))
    if hasattr(motor, "kick_min_target_rpm"):
        motor.kick_min_target_rpm = _as_float(
            kick_cfg.get("min_target_rpm", motor.kick_min_target_rpm),
            motor.kick_min_target_rpm,
        )
    if hasattr(motor, "kick_threshold_divisor"):
        motor.kick_threshold_divisor = _as_float(
            kick_cfg.get("threshold_divisor", motor.kick_threshold_divisor),
            motor.kick_threshold_divisor,
        )
    if hasattr(motor, "kick_duty_divisor"):
        motor.kick_duty_divisor = _as_float(
            kick_cfg.get("duty_divisor", motor.kick_duty_divisor),
            motor.kick_duty_divisor,
        )
    if hasattr(motor, "kick_max_duty"):
        motor.kick_max_duty = _as_float(
            kick_cfg.get("max_duty", motor.kick_max_duty),
            motor.kick_max_duty,
        )

    comm_cfg = motor_cfg.get("comm") or {}
    if hasattr(motor, "serial_port"):
        motor.serial_port = comm_cfg.get("port", motor.serial_port)
    if hasattr(motor, "serial_baud"):
        motor.serial_baud = _as_int(comm_cfg.get("baud", motor.serial_baud), motor.serial_baud)
    if hasattr(motor, "serial_timeout_s"):
        motor.serial_timeout_s = _as_float(
            comm_cfg.get("serial_timeout_s", motor.serial_timeout_s),
            motor.serial_timeout_s,
        )
    if hasattr(motor, "get_values_timeout_s"):
        motor.get_values_timeout_s = _as_float(
            comm_cfg.get("get_values_timeout_s", motor.get_values_timeout_s),
            motor.get_values_timeout_s,
        )

    if apply_comm and hasattr(motor, "reconfigure_serial"):
        motor.reconfigure_serial(
            port=comm_cfg.get("port"),
            baud=comm_cfg.get("baud"),
            timeout_s=comm_cfg.get("serial_timeout_s"),
        )
