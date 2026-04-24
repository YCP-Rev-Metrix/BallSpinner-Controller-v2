from dataclasses import dataclass
from typing import Dict, List

from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np
pg.setConfigOptions(antialias=False)
import os
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox

#Database related imports
from BSC import bsc
from backend.models.SessionData import SessionData
from backend.models.DataController import DataController
from backend.models.DiagnosticScriptData import DiagnosticScriptDataInstance
from backend.models.HeatData import HeatDataInstance
from backend.models.EncoderData import EncoderDataInstance
from backend.models.SmartDotData import SmartDotDataInstance
from frontend.SmartDotGraph import SmartDotGraph
from frontend.SmartDotConnectWidget import SmartDotConnectWidget
from frontend.SensorGraphDialog import SensorGraphDialog
from frontend.OverrideDialog import OverrideDialog

import datetime as dt


@dataclass
class MotorChannel:
    key: str
    motor_attr: str
    slider: QtWidgets.QSlider
    label: QtWidgets.QLabel
    encoder_label: QtWidgets.QLabel
    current_label: QtWidgets.QLabel
    temp_label: QtWidgets.QLabel
    graph: pg.PlotWidget
    curve: pg.PlotDataItem
    encoder_curve: pg.PlotDataItem
    diag_motor_id: int
    motor_id: int
    label_fmt: str
    slider_range: tuple
    override_slider_range: tuple
    graph_range: tuple
    override_graph_range: tuple
    temp_values: List[float]
    temp_time: List[float]
    current_values: List[float]
    current_time: List[float]
    apply_speed_on_tick: bool


class CircularBufferSet:
    # Initialize fixed-size circular buffers for values and encoders.
    def __init__(self, size: int, keys: List[str]):
        self.size = max(1, int(size))
        self.keys = list(keys)
        self.x = np.zeros(self.size, dtype=np.float64)
        self.values = {key: np.zeros(self.size, dtype=np.float32) for key in self.keys}
        self.encoders = {key: np.zeros(self.size, dtype=np.float32) for key in self.keys}
        self.write_idx = 0
        self.filled = False

    # Reset buffers to zero and clear write state.
    def clear(self):
        self.x.fill(0.0)
        for key in self.keys:
            self.values[key].fill(0.0)
            self.encoders[key].fill(0.0)
        self.write_idx = 0
        self.filled = False

    # Append a timestamped sample into the circular buffers.
    def append(self, t: float, values: Dict[str, float], encoders: Dict[str, float]):
        idx = self.write_idx
        self.x[idx] = t
        for key in self.keys:
            self.values[key][idx] = values.get(key, 0.0)
            self.encoders[key][idx] = encoders.get(key, 0.0)
        self.write_idx = (idx + 1) % self.size
        if self.write_idx == 0:
            self.filled = True

    # Return chronological views of buffered values and encoder data.
    def get_views(self):
        if not self.filled:
            count = self.write_idx
            x_view = self.x[:count]
            values_view = {key: self.values[key][:count] for key in self.keys}
            encoder_view = {key: self.encoders[key][:count] for key in self.keys}
            return x_view, values_view, encoder_view

        idx = self.write_idx
        x_view = np.concatenate((self.x[idx:], self.x[:idx]))
        values_view = {
            key: np.concatenate((self.values[key][idx:], self.values[key][:idx]))
            for key in self.keys
        }
        encoder_view = {
            key: np.concatenate((self.encoders[key][idx:], self.encoders[key][:idx]))
            for key in self.keys
        }
        return x_view, values_view, encoder_view


class DiagnosticModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)
    navigationLock = pyqtSignal(bool, str) # False = lock, True = unlock

    # Initialize UI, state, and helper structures.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.OverrideMode = False

        uic.loadUi(os.path.join(os.path.dirname(__file__), 'DiagnosticModePage.ui'), self, package='frontend')

        self._channel_keys = ["spin", "tilt", "angle"]
        self._setup_widgets()
        self._setup_graphs()
        self._setup_sensor_storage()
        self._setup_channels()
        self._setup_controls()
        self._setup_smartdot()
        self._setup_sampling()

        self._last_values = {key: 0.0 for key in self._channel_keys}
        self._sample_index = 0

        self._diagnostic_duration_s = 300.0
        self._diagnostic_warning_threshold_s = 60.0
        self._diagnostic_end_time_s = self._diagnostic_duration_s
        self._diagnostic_warning_shown = False
        self._diagnostic_warning_pending = False
        self._extend_warning_dialog = None

        self._motors_connected = False
        self._diagnostic_active = False
        self._recording_enabled = False

        self._set_zero_buttons_enabled(False)
        self._set_motor_controls_enabled(False)

    # Resolve widgets by name from the UI file.
    def _setup_widgets(self):
        self.btnConnectMotors = self.findChild(QtWidgets.QPushButton, 'btnEnableMotors')
        self.btnStartDiagnostic = self.findChild(QtWidgets.QPushButton, 'btnStartDiagnostic')
        self.btnZeroMotors = self.findChild(QtWidgets.QPushButton, 'btnZeroMotors')
        self.btnSave = self.findChild(QtWidgets.QPushButton, 'btnSave')
        self.btnAnalyze = self.findChild(QtWidgets.QPushButton, 'btnAnalyze')
        self.btnOverride = self.findChild(QtWidgets.QPushButton, 'btnOverride')

        self.btnGraphTemp = self.findChild(QtWidgets.QPushButton, 'btnGraphTemp')
        self.btnGraphCurrent = self.findChild(QtWidgets.QPushButton, 'btnGraphCurrent')

        self.spinGraph = self.findChild(pg.PlotWidget, 'grphSpin')
        self.tiltGraph = self.findChild(pg.PlotWidget, 'grphTilt')
        self.angleGraph = self.findChild(pg.PlotWidget, 'grphAngle')
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'grphSmartDot')

        self.labelSpin = self.findChild(QtWidgets.QLabel, 'lblSpin')
        self.labelTilt = self.findChild(QtWidgets.QLabel, 'lblTilt')
        self.labelAngle = self.findChild(QtWidgets.QLabel, 'lblAngle')
        self.labelSpinEncoder = self.findChild(QtWidgets.QLabel, 'lblSpinEncoder')
        self.labelTiltEncoder = self.findChild(QtWidgets.QLabel, 'lblTiltEncoder')
        self.labelAngleEncoder = self.findChild(QtWidgets.QLabel, 'lblAngleEncoder')

        self.lblSpinCurrent = self.findChild(QtWidgets.QLabel, 'lblSpinCurrent')
        self.lblTiltCurrent = self.findChild(QtWidgets.QLabel, 'lblTiltCurrent')
        self.lblAngleCurrent = self.findChild(QtWidgets.QLabel, 'lblAngleCurrent')
        self.lblSpinTemp = self.findChild(QtWidgets.QLabel, 'lblSpinTemp')
        self.lblTiltTemp = self.findChild(QtWidgets.QLabel, 'lblTiltTemp')
        self.lblAngleTemp = self.findChild(QtWidgets.QLabel, 'lblAngleTemp')

        self.spinSlider = self.findChild(QtWidgets.QSlider, 'sliderSpin')
        self.tiltSlider = self.findChild(QtWidgets.QSlider, 'sliderTilt')
        self.angleSlider = self.findChild(QtWidgets.QSlider, 'sliderAngle')

        self.btnSpinIncrease = self.findChild(QtWidgets.QPushButton, 'btnSpinInc')
        self.btnSpinDecrease = self.findChild(QtWidgets.QPushButton, 'btnSpinDec')
        self.btnTiltIncrease = self.findChild(QtWidgets.QPushButton, 'btnTiltInc')
        self.btnTiltDecrease = self.findChild(QtWidgets.QPushButton, 'btnTiltDec')
        self.btnAngleIncrease = self.findChild(QtWidgets.QPushButton, 'btnAngleInc')
        self.btnAngleDecrease = self.findChild(QtWidgets.QPushButton, 'btnAngleDec')

        self.smartdotConnectWidget = self.findChild(SmartDotConnectWidget, 'wgtSmartDotConnect')

    # Configure plot widgets and their base curves.
    def _setup_graphs(self):
        self.spinGraph.setTitle("Diagnostic Spin Graph")
        self.spinGraph.setLabel('left', 'Spin Rate', units='RPM')
        self.spinGraph.setLabel('bottom', 'Time', units='s')
        self.spinCurve = self.spinGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#ff0000', width=2))
        self.spinEncoderCurve = self.spinGraph.plot(
            [0.0],
            [0.0],
            pen=pg.mkPen(color='#00ffff', width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
            name='Spin Encoder'
        )
        self.spinGraph.setMouseEnabled(x=False, y=False)

        self.tiltGraph.setTitle("Diagnostic Tilt Graph")
        self.tiltGraph.setLabel('left', 'Tilt Angle', units='Degrees')
        self.tiltGraph.setLabel('bottom', 'Time', units='s')
        self.tiltCurve = self.tiltGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#00aa00', width=2))
        self.tiltEncoderCurve = self.tiltGraph.plot(
            [0.0],
            [0.0],
            pen=pg.mkPen(color='#ffff00', width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
            name='Tilt Encoder'
        )
        self.tiltGraph.setMouseEnabled(x=False, y=False)

        self.angleGraph.setTitle("Diagnostic Angle Graph")
        self.angleGraph.setLabel('left', 'Angle', units='Degrees')
        self.angleGraph.setLabel('bottom', 'Time', units='s')
        self.angleCurve = self.angleGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#0000ff', width=2))
        self.angleEncoderCurve = self.angleGraph.plot(
            [0.0],
            [0.0],
            pen=pg.mkPen(color='#ff00ff', width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
            name='Angle Encoder'
        )
        self.angleGraph.setMouseEnabled(x=False, y=False)

    # Initialize lists used for sensor charting.
    def _setup_sensor_storage(self):
        self.spin_temp_values = []
        self.spin_temp_time = []
        self.tilt_temp_values = []
        self.tilt_temp_time = []
        self.angle_temp_values = []
        self.angle_temp_time = []

        self.spin_current_values = []
        self.spin_current_time = []
        self.tilt_current_values = []
        self.tilt_current_time = []
        self.angle_current_values = []
        self.angle_current_time = []

    # Build the per-motor channel configuration.
    def _setup_channels(self):
        self._channels = [
            MotorChannel(
                key="spin",
                motor_attr="motor1",
                slider=self.spinSlider,
                label=self.labelSpin,
                encoder_label=self.labelSpinEncoder,
                current_label=self.lblSpinCurrent,
                temp_label=self.lblSpinTemp,
                graph=self.spinGraph,
                curve=self.spinCurve,
                encoder_curve=self.spinEncoderCurve,
                diag_motor_id=0,
                motor_id=1,
                label_fmt="Spin Rate: {value:.2f} RPM",
                slider_range=(0, 600),
                override_slider_range=(0, 1200),
                graph_range=(0, 620),
                override_graph_range=(0, 1250),
                temp_values=self.spin_temp_values,
                temp_time=self.spin_temp_time,
                current_values=self.spin_current_values,
                current_time=self.spin_current_time,
                apply_speed_on_tick=True,
            ),
            MotorChannel(
                key="tilt",
                motor_attr="motor2",
                slider=self.tiltSlider,
                label=self.labelTilt,
                encoder_label=self.labelTiltEncoder,
                current_label=self.lblTiltCurrent,
                temp_label=self.lblTiltTemp,
                graph=self.tiltGraph,
                curve=self.tiltCurve,
                encoder_curve=self.tiltEncoderCurve,
                diag_motor_id=1,
                motor_id=2,
                label_fmt="Tilt Angle: {value:.2f} Degrees",
                slider_range=(-22, 22),
                override_slider_range=(-359, 359),
                graph_range=(-22, 22),
                override_graph_range=(-400, 400),
                temp_values=self.tilt_temp_values,
                temp_time=self.tilt_temp_time,
                current_values=self.tilt_current_values,
                current_time=self.tilt_current_time,
                apply_speed_on_tick=False,
            ),
            MotorChannel(
                key="angle",
                motor_attr="motor3",
                slider=self.angleSlider,
                label=self.labelAngle,
                encoder_label=self.labelAngleEncoder,
                current_label=self.lblAngleCurrent,
                temp_label=self.lblAngleTemp,
                graph=self.angleGraph,
                curve=self.angleCurve,
                encoder_curve=self.angleEncoderCurve,
                diag_motor_id=2,
                motor_id=3,
                label_fmt="Angle: {value:.2f} Degrees",
                slider_range=(-45, 45),
                override_slider_range=(-359, 359),
                graph_range=(-45, 45),
                override_graph_range=(-400, 400),
                temp_values=self.angle_temp_values,
                temp_time=self.angle_temp_time,
                current_values=self.angle_current_values,
                current_time=self.angle_current_time,
                apply_speed_on_tick=False,
            ),
        ]
        self._apply_channel_ranges(override=False)

    # Wire up buttons, sliders, and other UI controls.
    def _setup_controls(self):
        self.btnGraphTemp.clicked.connect(self.show_temp_graph)
        self.btnGraphCurrent.clicked.connect(self.show_current_graph)

        self.btnSave.clicked.connect(self.openPostDialog)
        self.btnAnalyze.clicked.connect(self.analyze_data)
        self.btnAnalyze.setEnabled(True)

        self.btnOverride.setCheckable(True)
        self.btnOverride.clicked.connect(self.toggle_override_mode)

        self.btnSpinIncrease.clicked.connect(
            lambda: self.adjustSliderWithButton(self.spinSlider, step=10, increase=True)
        )
        self.btnSpinDecrease.clicked.connect(
            lambda: self.adjustSliderWithButton(self.spinSlider, step=10, increase=False)
        )
        self.btnTiltIncrease.clicked.connect(
            lambda: self.adjustSliderWithButton(self.tiltSlider, step=1, increase=True)
        )
        self.btnTiltDecrease.clicked.connect(
            lambda: self.adjustSliderWithButton(self.tiltSlider, step=1, increase=False)
        )
        self.btnAngleIncrease.clicked.connect(
            lambda: self.adjustSliderWithButton(self.angleSlider, step=1, increase=True)
        )
        self.btnAngleDecrease.clicked.connect(
            lambda: self.adjustSliderWithButton(self.angleSlider, step=1, increase=False)
        )

        for channel in self._channels:
            channel.slider.valueChanged.connect(self._update_slider_labels)

        self.btnConnectMotors.setText("Connect Motors")
        self.btnConnectMotors.clicked.connect(self.toggle_connect_motors)
        self.btnStartDiagnostic.clicked.connect(self.toggle_diagnostics)
        self.btnStartDiagnostic.setText("Start Diagnostic")
        self.btnStartDiagnostic.setEnabled(False)
        self.btnZeroMotors.clicked.connect(self._return_motors_to_zero)
        self.btnZeroMotors.setEnabled(False)

    # Initialize SmartDot integration and signals.
    def _setup_smartdot(self):
        self.SmartDot = None
        if self.smartdotConnectWidget:
            self.smartdotConnectWidget.signalSmartDotConnected.connect(self.connectSmartDot)
            self.smartdotConnectWidget.signalDeviceDisconnected.connect(self.on_device_disconnected)

    # Set up the timer and circular buffers for sampling.
    def _setup_sampling(self):
        self._timer = QTimer(self)
        self._sample_interval_ms = bsc.sample_interval_ms
        self._sample_dt_s = self._sample_interval_ms / 1000.0
        self._timer.setInterval(self._sample_interval_ms)
        self._timer.timeout.connect(self._on_timer)

        self._history_seconds = 3.0
        maxlen = int((self._history_seconds * 1000) // self._sample_interval_ms)
        self._buffers = CircularBufferSet(maxlen, self._channel_keys)

    # Resolve the motor instance for a channel.
    def _get_motor(self, channel: MotorChannel):
        return getattr(bsc, channel.motor_attr, None)

    # Apply slider and graph ranges based on override state.
    def _apply_channel_ranges(self, override: bool):
        for channel in self._channels:
            if override:
                slider_min, slider_max = channel.override_slider_range
                graph_min, graph_max = channel.override_graph_range
            else:
                slider_min, slider_max = channel.slider_range
                graph_min, graph_max = channel.graph_range
            channel.slider.setRange(slider_min, slider_max)
            channel.graph.setYRange(graph_min, graph_max)

    # Read current slider values into a keyed dict.
    def _get_slider_values(self) -> Dict[str, float]:
        return {channel.key: float(channel.slider.value()) for channel in self._channels}

    # Read a single encoder value safely.
    def _read_encoder_value(self, channel: MotorChannel) -> float:
        motor = self._get_motor(channel)
        if motor is None:
            return 0.0
        try:
            return float(motor.getCurrentSpeed())
        except Exception:
            return 0.0

    # Read encoder values for all channels.
    def _read_encoder_values(self) -> Dict[str, float]:
        return {channel.key: self._read_encoder_value(channel) for channel in self._channels}

    # Read current and temperature values for all channels.
    def _read_sensor_values(self) -> Dict[str, tuple]:
        values = {}
        for channel in self._channels:
            motor = self._get_motor(channel)
            current, temp, err = self._read_motor_vals(motor, channel.motor_attr)
            values[channel.key] = (current, temp, err)
        return values

    # Update current/temp labels from sensor readings.
    def _update_sensor_labels(self, sensor_values: Dict[str, tuple]):
        for channel in self._channels:
            current, temp, err = sensor_values[channel.key]
            if err:
                if channel.current_label:
                    channel.current_label.setText("N/A Read Error")
                if channel.temp_label:
                    channel.temp_label.setText("N/A Read Error")
                continue
            if current is not None:
                if channel.current_label:
                    channel.current_label.setText(f"{current:.2f} A")
            if temp is not None:
                if channel.temp_label:
                    channel.temp_label.setText(f"{temp:.1f} °C")

    # Store sensor readings and heat data while recording.
    def _record_sensor_data(self, t: float, sensor_values: Dict[str, tuple], dc: DataController):
        if not self._recording_enabled:
            return
        for channel in self._channels:
            current, temp, _err = sensor_values[channel.key]
            if current is not None:
                channel.current_time.append(t)
                channel.current_values.append(current)
            if temp is not None:
                channel.temp_time.append(t)
                channel.temp_values.append(temp)
                if dc is not None:
                    dc.add_heat_data(HeatDataInstance(time=t, motor_id=channel.motor_id, value=temp))

    # Add encoder samples to the data controller.
    def _record_encoder_data(self, t: float, encoder_values: Dict[str, float], dc: DataController):
        if not self._recording_enabled or dc is None:
            return
        for channel in self._channels:
            dc.add_encoder_data(EncoderDataInstance(time=t, pulses=encoder_values[channel.key], motor_id=channel.motor_id))

    # Update encoder labels using the latest readings.
    def _update_encoder_labels(self):
        for channel in self._channels:
            if channel.encoder_label:
                enc_value = self._read_encoder_value(channel)
                channel.encoder_label.setText(f"Enc: {enc_value:.1f} RPM")

    # Apply motor output changes and record diagnostic instructions.
    def _update_motor_outputs(self, t: float, slider_values: Dict[str, float], recording: bool, dc: DataController):
        for channel in self._channels:
            value = slider_values[channel.key]
            if value != self._last_values[channel.key]:
                if recording and dc is not None:
                    enc_value = self._read_encoder_value(channel)
                    dc.add_encoder_data(
                        EncoderDataInstance(time=t, pulses=enc_value, motor_id=channel.motor_id)
                    )
                self.add_diag_data_instance_to_data_controller(t, channel.diag_motor_id, value)
                self._last_values[channel.key] = value
                if channel.label:
                    channel.label.setText(channel.label_fmt.format(value=value))
                if not channel.apply_speed_on_tick:
                    motor = self._get_motor(channel)
                    self._change_motor_speed(motor, value)

        for channel in self._channels:
            if channel.apply_speed_on_tick:
                motor = self._get_motor(channel)
                self._change_motor_speed(motor, slider_values[channel.key])

        self._update_encoder_labels()

    # Push SmartDot samples into the graph during recording.
    def _update_smartdot_graph(self, recording: bool):
        if recording and self.SmartDot is not None and self.SmartDotGraph is not None:
            self.SmartDotGraph.updateDataBetter(
                self.SmartDot.xl_time, self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,
                self.SmartDot.gy_time, self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,
                self.SmartDot.mg_time, self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,
                self.SmartDot.lt_time, self.SmartDot.lt_value
            )

    # Refresh graph ranges and data from the circular buffers.
    def _refresh_graphs(self):
        last_idx = (self._buffers.write_idx - 1) % self._buffers.size
        latest_t = float(self._buffers.x[last_idx])
        start_t = max(0, latest_t - self._history_seconds)
        for channel in self._channels:
            channel.graph.setXRange(start_t, latest_t)

        x_view, values_view, encoder_view = self._buffers.get_views()
        for channel in self._channels:
            channel.curve.setData(x_view, values_view[channel.key])
            try:
                channel.encoder_curve.setData(x_view, encoder_view[channel.key])
            except Exception:
                pass

    # Clear the stored sensor value arrays.
    def _clear_sensor_arrays(self):
        for channel in self._channels:
            channel.temp_values.clear()
            channel.temp_time.clear()
            channel.current_values.clear()
            channel.current_time.clear()


    # Open the post-session dialog and submit data if accepted.
    def openPostDialog(self):
        from .PostDialog import PostDialog
        dialog = PostDialog(self)
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            print("User accepted the dialog.")
            session_name = dialog.getSessionName()
            print(f"Session Name: {session_name}")
            bsc.get_data_controller().set_session_name(session_name)

            # make sure any collected SmartDot data is moved into the DataController
            self._package_smartdot_data_to_controller()

            print("Submitting data to cloud")
            bsc.get_data_controller().submit_session_data()
            print("Data submitted to cloud")
            # Handle acceptance (e.g., save data)
        else:
            print("User rejected the dialog.")
            # Handle rejection (e.g., cancel operation)
    
    # Show temperature graphs in a separate dialog.
    def show_temp_graph(self):
        """Open a dialog showing temperature graphs for all three motors."""
        dialog = SensorGraphDialog(
            title="Temperature Sensor Data",
            spin_time=self.spin_temp_time,
            spin_values=self.spin_temp_values,
            tilt_time=self.tilt_temp_time,
            tilt_values=self.tilt_temp_values,
            angle_time=self.angle_temp_time,
            angle_values=self.angle_temp_values,
            y_label="Temperature (°C)",
            parent=self
        )
        dialog.exec()
    
    # Show current graphs in a separate dialog.
    def show_current_graph(self):
        """Open a dialog showing current graphs for all three motors."""
        dialog = SensorGraphDialog(
            title="Current Sensor Data",
            spin_time=self.spin_current_time,
            spin_values=self.spin_current_values,
            tilt_time=self.tilt_current_time,
            tilt_values=self.tilt_current_values,
            angle_time=self.angle_current_time,
            angle_values=self.angle_current_values,
            y_label="Current (A)",
            parent=self
        )
        dialog.exec()

    # Toggle motor connection state.
    def toggle_connect_motors(self):
        if self._motors_connected:
            self._disconnect_motors()
        else:
            self._connect_motors()

    # Start motors and enable manual control without recording.
    def _connect_motors(self):
        # Start motors and allow manual control without recording data.
        for channel in self._channels:
            motor = self._get_motor(channel)
            if motor is None:
                continue
            try:
                motor.start()
            except Exception as e:
                print(f"Error starting motor: {e}")

        self._motors_connected = True
        self._recording_enabled = False
        self._diagnostic_active = False

        self.btnConnectMotors.setText("Disconnect Motors")
        self.btnStartDiagnostic.setEnabled(True)
        self.btnStartDiagnostic.setText("Start Diagnostic")
        self._set_zero_buttons_enabled(True)
        self._set_motor_controls_enabled(True)

        if not self._timer.isActive():
            self._timer.start()
        self.navigationLock.emit(False, "Motors Connected - Manual Control Enabled")

    # Stop motors and disable manual control.
    def _disconnect_motors(self):
        if self._diagnostic_active:
            self._stop_diagnostics()

        self._recording_enabled = False
        self._diagnostic_active = False
        self._motors_connected = False

        try:
            for channel in self._channels:
                motor = self._get_motor(channel)
                if motor is None:
                    continue
                try:
                    motor.stop()
                except Exception:
                    pass
            bsc.disconnect_all_motors()
        finally:
            try:
                self._timer.stop()
            except Exception:
                pass

        self.btnConnectMotors.setText("Connect Motors")
        self.btnStartDiagnostic.setEnabled(False)
        self.btnStartDiagnostic.setText("Start Diagnostic")
        self._set_zero_buttons_enabled(False)
        self._set_motor_controls_enabled(False)

        self.reset(clear_graphs=False, clear_data=False)
        self._clear_encoder_values()
        self.navigationLock.emit(True, "")

    # Toggle diagnostic recording state.
    def toggle_diagnostics(self):
        if self._diagnostic_active:
            self._stop_diagnostics()
        else:
            self._start_diagnostics()

    # Start diagnostic recording and reset buffers.
    def _start_diagnostics(self):
        if not self._motors_connected:
            self._connect_motors()

        self.btnConnectMotors.setEnabled(False)
        self._set_zero_buttons_enabled(False)
        self.btnStartDiagnostic.setText("Stop Diagnostic")

        self.btnOverride.setEnabled(False)

        self._recording_enabled = True
        self._diagnostic_active = True

        if self._timer.isActive():
            self._timer.stop()

        self._sample_index = 0
        self.clear_graphs()  # also resets buffers and indices
        self._clear_sensor_arrays()

        if self.SmartDot is not None:
            self.start_smartdot_updates()

        self._diagnostic_end_time_s = self._diagnostic_duration_s
        self._diagnostic_warning_shown = False

        bsc.set_session(SessionData(id=-1, timeStamp=dt.datetime.now().isoformat(), name="Diagnostic Session", isShotMode=False))
        bsc.set_data_controller(DataController(bsc.get_session()))

        if not self._timer.isActive():
            self._timer.start()

        

    # Stop diagnostic recording and restore controls.
    def _stop_diagnostics(self):
        self._recording_enabled = False
        self._diagnostic_active = False

        self.btnConnectMotors.setEnabled(True)
        self._set_zero_buttons_enabled(True)
        self.btnStartDiagnostic.setText("Start Diagnostic")
        self.btnOverride.setEnabled(True)

        if self.SmartDot is not None:
            self.stop_smartdot_updates()

        if not self._motors_connected:
            try:
                self._timer.stop()
            except Exception:
                pass

        self._reset_spin_motor_only()
        if not self._motors_connected:
            self.navigationLock.emit(True, "")

    # Add a diagnostic script data point to the data controller.
    def add_diag_data_instance_to_data_controller(self, time: float, motor_id: int, instruction: float):
        if not self._recording_enabled:
            return
        dc: DataController = bsc.get_data_controller()
        if dc is None:
            return
        data = DiagnosticScriptDataInstance(
            time=time,
            motor_id=motor_id,
            instruction=instruction
        )
        dc.add_diagnostic_script_data(data)

    def _show_extend_diagnostic_warning(self):
        self._diagnostic_warning_pending = True
        self._diagnostic_warning_shown = True

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Diagnostic Timeout Warning")
        dialog.setText(
            "Diagnostic recording will stop in 1 minute. "
            "Would you like to extend the diagnostic for another 5 minutes?"
        )
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        dialog.buttonClicked.connect(self._on_extend_warning_response)
        dialog.finished.connect(self._on_extend_warning_finished)
        dialog.open()

        self._extend_warning_dialog = dialog

    def _on_extend_warning_response(self, button):
        if button == self._extend_warning_dialog.button(QMessageBox.StandardButton.Yes):
            self._diagnostic_end_time_s += self._diagnostic_duration_s
            self._diagnostic_warning_shown = False

    def _on_extend_warning_finished(self, result):
        self._diagnostic_warning_pending = False
        self._extend_warning_dialog = None

    # Change motor speed with compatibility for different signatures.
    def _change_motor_speed(self, motor, value: float):
        if motor is None:
            return
        try:
            motor.changeSpeed(float(value), False)
        except TypeError:
            try:
                motor.changeSpeed(float(value))
            except Exception as e:
                print(f"Error changing motor speed: {e}")
        except Exception as e:
            print(f"Error changing motor speed: {e}")

    # Read current and temperature values from a motor, if supported.
    def _read_motor_vals(self, motor, motor_label: str):
        if motor is None or not hasattr(motor, "getVals"):
            return None, None, False
        try:
            vals = motor.getVals()
        except Exception as e:
            print(f"Error reading {motor_label} sensors: {e}")
            return None, None, True
        if not isinstance(vals, dict):
            return None, None, True
        return vals.get("input_current"), vals.get("temp_motor"), False

    # Periodic sampling tick: read, record, drive outputs, and refresh graphs.
    def _on_timer(self):
        # Runs in main (GUI) thread. Poll sliders and update buffers + plots.
        # Called only when the timer is active; no separate `active` flag needed.
        if not self._motors_connected:
            return
        dc = bsc.get_data_controller()
        recording = self._recording_enabled and dc is not None
        self._update_smartdot_graph(recording)

        # Quantized time based on fixed interval (>=50ms)
        t = self._sample_index * self._sample_dt_s
        if recording:
            if t >= self._diagnostic_end_time_s:
                if self._extend_warning_dialog is not None and self._extend_warning_dialog.isVisible():
                    self._extend_warning_dialog.done(QMessageBox.StandardButton.No)
                self._stop_diagnostics()
                QMessageBox.information(self, "Diagnostic Timeout", "Diagnostic recording has reached the timeout and has been stopped.")
                return
            if (t >= self._diagnostic_end_time_s - self._diagnostic_warning_threshold_s
                    and not self._diagnostic_warning_shown
                    and not self._diagnostic_warning_pending):
                self._show_extend_diagnostic_warning()
            self._sample_index += 1

        slider_values = self._get_slider_values()
        encoder_values = self._read_encoder_values()
        sensor_values = self._read_sensor_values()

        self._update_sensor_labels(sensor_values)
        self._record_sensor_data(t, sensor_values, dc)

        if recording:
            self._buffers.append(t, slider_values, encoder_values)
            self._record_encoder_data(t, encoder_values, dc)

        self._update_motor_outputs(t, slider_values, recording, dc)

        if recording:
            self._refresh_graphs()

    # Update slider labels and encoder labels on manual slider changes.
    def _update_slider_labels(self):
        """Update motor spin boxes to reflect current slider values regardless of timer state."""
        for channel in self._channels:
            value = float(channel.slider.value())
            if channel.label:
                channel.label.setText(channel.label_fmt.format(value=value))
        self._update_encoder_labels()

    # Reset UI state, buffers, and optionally recorded data.
    def reset(self, clear_graphs: bool = True, clear_data: bool = True):
        # ensure not running and reset UI
        # Stop SmartDot updates if running
        if self.SmartDot is not None:
            self.stop_smartdot_updates()
        if clear_data:
            # Clear SmartDot data from the data controller so we start fresh
            dc = bsc.get_data_controller()
            if dc is not None:
                try:
                    dc.smartdot_data.data_entries.clear()
                except AttributeError:
                    pass
        if clear_graphs:
            self.clear_graphs()
        for channel in self._channels:
            channel.slider.setValue(0)
        self._last_values = {key: 0.0 for key in self._channel_keys}
        for channel in self._channels:
            channel.label.setText(channel.label_fmt.format(value=0.0))
            if channel.encoder_label:
                channel.encoder_label.setText("Enc: 0.0 RPM")
        # ensure timer stopped
        if not self._motors_connected:
            self._timer.stop()
        self._set_zero_buttons_enabled(self._motors_connected and not self._diagnostic_active)
        self._set_motor_controls_enabled(self._motors_connected)
    
    # Clear plot data and reset circular buffers.
    def clear_graphs(self):
        # Clear instance buffers and reset plots
        self._buffers.clear()
        for channel in self._channels:
            channel.curve.setData([0.0], [0.0])
            channel.encoder_curve.setData([0.0], [0.0])
        
        # Clear SmartDot graph data if available
        if self.SmartDotGraph is not None:
            if hasattr(self.SmartDotGraph, 'clear'):
                self.SmartDotGraph.clear()   

    # Clear encoder readout labels and encoder graph traces.
    def _clear_encoder_values(self):
        for channel in self._channels:
            if channel.encoder_label:
                channel.encoder_label.setText("Enc: 0.0 RPM")
            try:
                channel.encoder_curve.setData([0.0], [0.0])
            except Exception:
                pass

    # Enable or disable the zeroing button.
    def _set_zero_buttons_enabled(self, enabled: bool):
        self.btnZeroMotors.setEnabled(enabled)

    # Enable or disable motor control widgets.
    def _set_motor_controls_enabled(self, enabled: bool):
        controls = (
            self.spinSlider,
            self.tiltSlider,
            self.angleSlider,
            self.btnSpinIncrease,
            self.btnSpinDecrease,
            self.btnTiltIncrease,
            self.btnTiltDecrease,
            self.btnAngleIncrease,
            self.btnAngleDecrease,
        )
        for control in controls:
            if control:
                control.setEnabled(enabled)

    # Command motors to return to zero and reset sliders.
    def _return_motors_to_zero(self):
        if self._diagnostic_active:
            return
        try:
            bsc.zero()
        except Exception as e:
            print(f"Error homing motors: {e}")
        self.spinSlider.setValue(0)
        self.tiltSlider.setValue(0)
        self.angleSlider.setValue(0)
        self._update_slider_labels()

    # Reset only spin motor/channel state while leaving tilt/angle untouched.
    def _reset_spin_motor_only(self):
        spin_channel = next((channel for channel in self._channels if channel.key == "spin"), None)
        if spin_channel is None:
            return

        # Command spin motor to zero output and stop movement.
        spin_motor = self._get_motor(spin_channel)
        self._change_motor_speed(spin_motor, 0.0)
        if spin_motor is not None and hasattr(spin_motor, "stop"):
            try:
                spin_motor.stop()
            except Exception:
                pass

        if spin_channel.slider.value() != 0:
            spin_channel.slider.setValue(0)
        self._last_values["spin"] = 0.0
        if spin_channel.label:
            spin_channel.label.setText(spin_channel.label_fmt.format(value=0.0))
        if spin_channel.encoder_label:
            spin_channel.encoder_label.setText("Enc: 0.0 RPM")

    # Show override dialog and apply the selected mode.
    def toggle_override_mode(self):
        """Open override mode configuration dialog."""
        dialog = OverrideDialog(self, current_enabled=self.OverrideMode)
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            override_enabled = dialog.is_override_enabled()
            self.toggle_enable_override(override_enabled)
            self.btnOverride.setChecked(override_enabled)
        else:
            # User cancelled, reset button state
            self.btnOverride.setChecked(self.OverrideMode)
    
    # Apply override mode ranges and styling.
    def toggle_enable_override(self, enable: bool):
        self.OverrideMode = enable
        
        if self.OverrideMode:
            print("Override Mode Enabled")
            # Mark override mode for QSS styling
            self._apply_override_style(True)
            self._apply_channel_ranges(override=True)
        else:
            print("Override Mode Disabled")
            # Clear override mode styling flag
            self._apply_override_style(False)
            self._apply_channel_ranges(override=False)
            self._reset_spin_motor_only()

    # Apply override mode styling on the main window.
    def _apply_override_style(self, enabled: bool):
        main_window = self.window()
        if main_window is None:
            return
        main_window.setProperty("override", "true" if enabled else "false")
        main_window.style().unpolish(main_window)
        main_window.style().polish(main_window)
        # Re-apply the stylesheet so descendant selectors re-evaluate.
        main_window.setStyleSheet(main_window.styleSheet())
        main_window.update()
    
    # Store the connected SmartDot device instance.
    def connectSmartDot(self, device):
        """Called when a SmartDot device is connected."""
        print("Connecting SmartDot...")
        self.SmartDot = device
        print(f"SmartDot: {self.SmartDot}")
        print(f"Smart dot type: {type(self.SmartDot)}")

    # Move buffered SmartDot readings into the data controller.
    def _package_smartdot_data_to_controller(self):
        """Move any buffered SmartDot readings into the shared DataController.

        This mirrors the logic used by :class:`ShotViewPage` so that
        diagnostic mode also persists SmartDot information before
        submitting/clearing the session. It is safe to call multiple times.
        """
        if self.SmartDot is None:
            return
        # stop collecting if still running (ensures arrays are final)
        try:
            self.SmartDot.stopCollecting()
        except Exception:
            pass
        dc = bsc.get_data_controller()
        if dc is None:
            return
        # accelerometer samples
        xl_count = min(
            len(self.SmartDot.xl_time),
            len(self.SmartDot.xl_x),
            len(self.SmartDot.xl_y),
            len(self.SmartDot.xl_z),
        )
        for i in range(xl_count):
            dc.add_smartdot_data(SmartDotDataInstance(
                time=self.SmartDot.xl_time[i],
                data_selector=0,  # Accelerometer
                accelerometer_x=self.SmartDot.xl_x[i],
                accelerometer_y=self.SmartDot.xl_y[i],
                accelerometer_z=self.SmartDot.xl_z[i],
                gyroscope_x=-1,
                gyroscope_y=-1,
                gyroscope_z=-1,
                magnetometer_x=-1,
                magnetometer_y=-1,
                magnetometer_z=-1,
                light=-1
            ))
        # gyroscope samples
        gy_count = min(
            len(self.SmartDot.gy_time),
            len(self.SmartDot.gy_x),
            len(self.SmartDot.gy_y),
            len(self.SmartDot.gy_z),
        )
        for i in range(gy_count):
            dc.add_smartdot_data(SmartDotDataInstance(
                time=self.SmartDot.gy_time[i],
                data_selector=1,  # Gyroscope
                accelerometer_x=-1,
                accelerometer_y=-1,
                accelerometer_z=-1,
                gyroscope_x=self.SmartDot.gy_x[i],
                gyroscope_y=self.SmartDot.gy_y[i],
                gyroscope_z=self.SmartDot.gy_z[i],
                magnetometer_x=-1,
                magnetometer_y=-1,
                magnetometer_z=-1,
                light=-1
            ))
        # magnetometer samples
        mg_count = min(
            len(self.SmartDot.mg_time),
            len(self.SmartDot.mg_x),
            len(self.SmartDot.mg_y),
            len(self.SmartDot.mg_z),
        )
        for i in range(mg_count):
            dc.add_smartdot_data(SmartDotDataInstance(
                time=self.SmartDot.mg_time[i],
                data_selector=2,  # Magnetometer
                accelerometer_x=-1,
                accelerometer_y=-1,
                accelerometer_z=-1,
                gyroscope_x=-1,
                gyroscope_y=-1,
                gyroscope_z=-1,
                magnetometer_x=self.SmartDot.mg_x[i],
                magnetometer_y=self.SmartDot.mg_y[i],
                magnetometer_z=self.SmartDot.mg_z[i],
                light=-1
            ))
        # light samples
        lt_count = min(len(self.SmartDot.lt_time), len(self.SmartDot.lt_value))
        for i in range(lt_count):
            dc.add_smartdot_data(SmartDotDataInstance(
                time=self.SmartDot.lt_time[i],
                data_selector=3,  # Light
                accelerometer_x=-1,
                accelerometer_y=-1,
                accelerometer_z=-1,
                gyroscope_x=-1,
                gyroscope_y=-1,
                gyroscope_z=-1,
                magnetometer_x=-1,
                magnetometer_y=-1,
                magnetometer_z=-1,
                light=self.SmartDot.lt_value[i]
            ))
        print("Packaged SmartDot data into DataController")
    
    # Handle SmartDot disconnect events.
    def on_device_disconnected(self, mac_address):
        """Called when device disconnects."""
        print(f"Device disconnected: {mac_address}")
        # Stop updates if running
        if self._timer.isActive():
            self.stop_smartdot_updates()
        # Clear the SmartDot reference
        self.SmartDot = None
    
    # Start collecting data from SmartDot.
    def start_smartdot_updates(self):
        """Start collecting data from SmartDot."""
        if self.SmartDot is not None:
            print("Starting SmartDot data collection")
            self.SmartDot.startCollecting()
    
    # Stop collecting data from SmartDot and package results.
    def stop_smartdot_updates(self):
        """Stop collecting data from SmartDot."""
        if self.SmartDot is not None:
            print("Stopping SmartDot data collection")
            self.SmartDot.stopCollecting()
            # when we stop collecting we can also package what we've gathered
            self._package_smartdot_data_to_controller()

    # Package SmartDot data and navigate to analysis view.
    def analyze_data(self):
        """Handler for the Analyze button.

        Packages any remaining SmartDot samples and then transitions to the
        analysis page by emitting the changePage signal with the active
        DataController (same behaviour as DataViewPage.analyze_data).
        """
        # ensure collected samples are stored in the controller
        self._package_smartdot_data_to_controller()
        dc = bsc.get_data_controller()
        if dc is None:
            return
        self.changePage.emit(3, dc)

    # Adjust a slider by a fixed step from a button click.
    def adjustSliderWithButton(self, slider: QtWidgets.QSlider, step: int, increase: bool):
        """Utility to adjust a slider by a fixed step when a button is clicked."""
        current_value = slider.value()
        if increase:
            new_value = current_value + step
        else:
            new_value = current_value - step
        # Clamp to slider range
        new_value = max(slider.minimum(), min(slider.maximum(), new_value))
        slider.setValue(new_value)

if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = DiagnosticModePage()
    window.setWindowTitle("Diagnostic Mode Page")
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())