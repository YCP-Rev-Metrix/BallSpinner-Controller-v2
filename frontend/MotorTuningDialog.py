from PyQt6 import QtWidgets
import re

from tuning_config import (
    DEFAULT_TUNING_PATH,
    apply_tuning_config,
    get_default_tuning_config,
    load_tuning_config,
    save_tuning_config,
)


class MotorTuningDialog(QtWidgets.QDialog):
    def __init__(self, bsc, parent=None, config_path=None):
        super().__init__(parent)
        self._bsc = bsc
        self._config_path = config_path or DEFAULT_TUNING_PATH
        self._config = load_tuning_config(self._config_path)

        self.setWindowTitle("Motor Tuning Parameters")
        self.resize(720, 640)

        layout = QtWidgets.QVBoxLayout(self)
        self._tabs = QtWidgets.QTabWidget()
        layout.addWidget(self._tabs)

        self._build_general_tab()
        self._build_control_tab()
        self._build_kick_tab()
        self._build_comm_tab()
        self._build_motor_test_tab()

        self._status = QtWidgets.QLabel("")
        layout.addWidget(self._status)

        btn_row = QtWidgets.QHBoxLayout()
        self._btn_load = QtWidgets.QPushButton("Reload")
        self._btn_save = QtWidgets.QPushButton("Save")
        self._btn_apply = QtWidgets.QPushButton("Apply")
        self._btn_close = QtWidgets.QPushButton("Close")

        self._btn_load.clicked.connect(self._reload)
        self._btn_save.clicked.connect(self._save)
        self._btn_apply.clicked.connect(self._apply)
        self._btn_close.clicked.connect(self.accept)

        btn_row.addWidget(self._btn_load)
        btn_row.addStretch(1)
        btn_row.addWidget(self._btn_save)
        btn_row.addWidget(self._btn_apply)
        btn_row.addWidget(self._btn_close)
        layout.addLayout(btn_row)

        self._load_into_widgets(self._config)

    def _build_general_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        self.spnSampleIntervalMs = QtWidgets.QSpinBox()
        self.spnSampleIntervalMs.setRange(1, 10000)
        self.spnSampleIntervalMs.setSuffix(" ms")
        form.addRow("Sample Interval", self.spnSampleIntervalMs)
        self._tabs.addTab(tab, "General")

    def _build_control_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)

        self.spnDutyScale = QtWidgets.QDoubleSpinBox()
        self.spnDutyScale.setDecimals(9)
        self.spnDutyScale.setRange(0.0, 1.0)
        self.spnDutyScale.setSingleStep(0.00001)

        self.spnKp = QtWidgets.QDoubleSpinBox()
        self.spnKp.setDecimals(4)
        self.spnKp.setRange(0.0, 100.0)

        self.spnKi = QtWidgets.QDoubleSpinBox()
        self.spnKi.setDecimals(4)
        self.spnKi.setRange(0.0, 100.0)

        self.spnKd = QtWidgets.QDoubleSpinBox()
        self.spnKd.setDecimals(4)
        self.spnKd.setRange(0.0, 100.0)

        self.spnTargetMin = QtWidgets.QDoubleSpinBox()
        self.spnTargetMin.setDecimals(1)
        self.spnTargetMin.setRange(0.0, 5000.0)

        self.spnTargetMax = QtWidgets.QDoubleSpinBox()
        self.spnTargetMax.setDecimals(1)
        self.spnTargetMax.setRange(0.0, 5000.0)

        self.spnIntegralLimit = QtWidgets.QDoubleSpinBox()
        self.spnIntegralLimit.setDecimals(1)
        self.spnIntegralLimit.setRange(0.0, 5000.0)

        self.spnRampStep = QtWidgets.QDoubleSpinBox()
        self.spnRampStep.setDecimals(2)
        self.spnRampStep.setRange(0.0, 100.0)

        self.spnMissedWarn = QtWidgets.QSpinBox()
        self.spnMissedWarn.setRange(1, 1000)

        form.addRow("Duty Scale", self.spnDutyScale)
        form.addRow("Kp", self.spnKp)
        form.addRow("Ki", self.spnKi)
        form.addRow("Kd", self.spnKd)
        form.addRow("Target Min (RPM)", self.spnTargetMin)
        form.addRow("Target Max (RPM)", self.spnTargetMax)
        form.addRow("Integral Limit", self.spnIntegralLimit)
        form.addRow("Ramp Step", self.spnRampStep)
        form.addRow("Missed Speed Warn", self.spnMissedWarn)

        self._tabs.addTab(tab, "Control")

    def _build_kick_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)

        self.chkKickEnabled = QtWidgets.QCheckBox("Enable kick")
        self.spnKickMinTarget = QtWidgets.QDoubleSpinBox()
        self.spnKickMinTarget.setDecimals(1)
        self.spnKickMinTarget.setRange(0.0, 5000.0)

        self.spnKickThresholdDiv = QtWidgets.QDoubleSpinBox()
        self.spnKickThresholdDiv.setDecimals(1)
        self.spnKickThresholdDiv.setRange(1.0, 100000.0)

        self.spnKickDutyDiv = QtWidgets.QDoubleSpinBox()
        self.spnKickDutyDiv.setDecimals(1)
        self.spnKickDutyDiv.setRange(1.0, 100000.0)

        self.spnKickMaxDuty = QtWidgets.QDoubleSpinBox()
        self.spnKickMaxDuty.setDecimals(3)
        self.spnKickMaxDuty.setRange(0.0, 1.0)

        form.addRow(self.chkKickEnabled)
        form.addRow("Min Target RPM", self.spnKickMinTarget)
        form.addRow("Threshold Divisor", self.spnKickThresholdDiv)
        form.addRow("Duty Divisor", self.spnKickDutyDiv)
        form.addRow("Max Duty", self.spnKickMaxDuty)

        self._tabs.addTab(tab, "Kick")

    def _build_comm_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)

        self.txtPort = QtWidgets.QLineEdit()

        self.spnBaud = QtWidgets.QSpinBox()
        self.spnBaud.setRange(1200, 2000000)

        self.spnSerialTimeout = QtWidgets.QDoubleSpinBox()
        self.spnSerialTimeout.setDecimals(3)
        self.spnSerialTimeout.setRange(0.0, 10.0)

        self.spnGetValuesTimeout = QtWidgets.QDoubleSpinBox()
        self.spnGetValuesTimeout.setDecimals(3)
        self.spnGetValuesTimeout.setRange(0.0, 10.0)

        form.addRow("Port", self.txtPort)
        form.addRow("Baud", self.spnBaud)
        form.addRow("Serial Timeout (s)", self.spnSerialTimeout)
        form.addRow("Get Values Timeout (s)", self.spnGetValuesTimeout)

        note = QtWidgets.QLabel("Changing comm settings will reopen the serial port.")
        form.addRow(note)

        self._tabs.addTab(tab, "Comm")

    def _build_motor_test_tab(self):
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)

        self.txtTargetSpeeds = QtWidgets.QLineEdit()
        self.txtTargetSpeeds.setPlaceholderText("50, 100, 150, ...")

        self.spnHoldTime = QtWidgets.QDoubleSpinBox()
        self.spnHoldTime.setDecimals(2)
        self.spnHoldTime.setRange(0.1, 300.0)

        self.spnTestSampleInterval = QtWidgets.QDoubleSpinBox()
        self.spnTestSampleInterval.setDecimals(3)
        self.spnTestSampleInterval.setRange(0.001, 5.0)

        self.spnDwellTime = QtWidgets.QDoubleSpinBox()
        self.spnDwellTime.setDecimals(2)
        self.spnDwellTime.setRange(0.0, 30.0)

        self.txtScaleCandidates = QtWidgets.QLineEdit()
        self.txtScaleCandidates.setPlaceholderText("0.00002, 0.00003, ...")

        form.addRow("Target Speeds", self.txtTargetSpeeds)
        form.addRow("Hold Time (s)", self.spnHoldTime)
        form.addRow("Sample Interval (s)", self.spnTestSampleInterval)
        form.addRow("Dwell Time (s)", self.spnDwellTime)
        form.addRow("Scale Candidates", self.txtScaleCandidates)

        self._tabs.addTab(tab, "Motor Test")

    def _load_into_widgets(self, config):
        config = config or get_default_tuning_config()
        self.spnSampleIntervalMs.setValue(int(config.get("sample_interval_ms", 50)))

        motor_cfg = config.get("motor1") or {}
        self.spnDutyScale.setValue(float(motor_cfg.get("duty_cycle_scale", 0.0)))
        self.spnKp.setValue(float(motor_cfg.get("kp", 0.0)))
        self.spnKi.setValue(float(motor_cfg.get("ki", 0.0)))
        self.spnKd.setValue(float(motor_cfg.get("kd", 0.0)))
        self.spnTargetMin.setValue(float(motor_cfg.get("target_speed_min", 0.0)))
        self.spnTargetMax.setValue(float(motor_cfg.get("target_speed_max", 1200.0)))
        self.spnIntegralLimit.setValue(float(motor_cfg.get("integral_limit", 1200.0)))
        self.spnRampStep.setValue(float(motor_cfg.get("ramp_step", 2.0)))
        self.spnMissedWarn.setValue(int(motor_cfg.get("missed_speed_warn_threshold", 10)))

        kick_cfg = motor_cfg.get("kick") or {}
        self.chkKickEnabled.setChecked(bool(kick_cfg.get("enabled", True)))
        self.spnKickMinTarget.setValue(float(kick_cfg.get("min_target_rpm", 1.0)))
        self.spnKickThresholdDiv.setValue(float(kick_cfg.get("threshold_divisor", 900.0)))
        self.spnKickDutyDiv.setValue(float(kick_cfg.get("duty_divisor", 6000.0)))
        self.spnKickMaxDuty.setValue(float(kick_cfg.get("max_duty", 1.0)))

        comm_cfg = motor_cfg.get("comm") or {}
        self.txtPort.setText(str(comm_cfg.get("port", "/dev/ttyACM0")))
        self.spnBaud.setValue(int(comm_cfg.get("baud", 115200)))
        self.spnSerialTimeout.setValue(float(comm_cfg.get("serial_timeout_s", 0.05)))
        self.spnGetValuesTimeout.setValue(float(comm_cfg.get("get_values_timeout_s", 0.2)))

        test_cfg = config.get("motor_test") or {}
        self.txtTargetSpeeds.setText(self._format_list(test_cfg.get("target_speeds", [])))
        self.spnHoldTime.setValue(float(test_cfg.get("hold_time_s", 5.0)))
        self.spnTestSampleInterval.setValue(float(test_cfg.get("sample_interval_s", 0.1)))
        self.spnDwellTime.setValue(float(test_cfg.get("dwell_time_s", 3.0)))
        self.txtScaleCandidates.setText(self._format_list(test_cfg.get("scale_candidates", [])))

    def _collect_config(self):
        config = get_default_tuning_config()
        config["sample_interval_ms"] = int(self.spnSampleIntervalMs.value())

        motor_cfg = config["motor1"]
        motor_cfg["duty_cycle_scale"] = float(self.spnDutyScale.value())
        motor_cfg["kp"] = float(self.spnKp.value())
        motor_cfg["ki"] = float(self.spnKi.value())
        motor_cfg["kd"] = float(self.spnKd.value())
        motor_cfg["target_speed_min"] = float(self.spnTargetMin.value())
        motor_cfg["target_speed_max"] = float(self.spnTargetMax.value())
        motor_cfg["integral_limit"] = float(self.spnIntegralLimit.value())
        motor_cfg["ramp_step"] = float(self.spnRampStep.value())
        motor_cfg["missed_speed_warn_threshold"] = int(self.spnMissedWarn.value())

        kick_cfg = motor_cfg["kick"]
        kick_cfg["enabled"] = bool(self.chkKickEnabled.isChecked())
        kick_cfg["min_target_rpm"] = float(self.spnKickMinTarget.value())
        kick_cfg["threshold_divisor"] = float(self.spnKickThresholdDiv.value())
        kick_cfg["duty_divisor"] = float(self.spnKickDutyDiv.value())
        kick_cfg["max_duty"] = float(self.spnKickMaxDuty.value())

        comm_cfg = motor_cfg["comm"]
        comm_cfg["port"] = self.txtPort.text().strip()
        comm_cfg["baud"] = int(self.spnBaud.value())
        comm_cfg["serial_timeout_s"] = float(self.spnSerialTimeout.value())
        comm_cfg["get_values_timeout_s"] = float(self.spnGetValuesTimeout.value())

        test_cfg = config["motor_test"]
        test_cfg["target_speeds"] = self._parse_number_list(self.txtTargetSpeeds.text(), as_int=True)
        test_cfg["hold_time_s"] = float(self.spnHoldTime.value())
        test_cfg["sample_interval_s"] = float(self.spnTestSampleInterval.value())
        test_cfg["dwell_time_s"] = float(self.spnDwellTime.value())
        test_cfg["scale_candidates"] = self._parse_number_list(self.txtScaleCandidates.text(), as_int=False)

        return config

    def _reload(self):
        self._config = load_tuning_config(self._config_path)
        self._load_into_widgets(self._config)
        self._status.setText("Reloaded config from disk.")

    def _save(self):
        config = self._collect_config()
        save_tuning_config(config, self._config_path)
        self._config = config
        self._status.setText("Saved config.")

    def _apply(self):
        config = self._collect_config()
        try:
            apply_tuning_config(self._bsc, config, apply_comm=True)
            self._status.setText("Applied tuning to motor.")
        except Exception as exc:
            self._status.setText(f"Apply failed: {exc}")

    @staticmethod
    def _parse_number_list(text, as_int=False):
        if not text:
            return []
        parts = re.split(r"[\s,]+", text.strip())
        values = []
        for part in parts:
            if not part:
                continue
            try:
                value = float(part)
            except ValueError:
                continue
            if as_int:
                value = int(round(value))
            values.append(value)
        return values

    @staticmethod
    def _format_list(values):
        if not values:
            return ""
        return ", ".join(str(v) for v in values)
