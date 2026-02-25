from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np
pg.setConfigOptions(antialias=False)
import os
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from array import array

#Database related imports
from BSC import bsc
from backend.models.SessionData import SessionData
from backend.models.DataController import DataController
from backend.models.DiagnosticScriptData import DiagnosticScriptDataInstance
from backend.models.EncoderData import EncoderDataInstance
from backend.models.SmartDotData import SmartDotDataInstance
from backend.drivers.DiagnosticScript import DiagnosticScript
#from backend.motors.BDCMotor import BDCMotor
#from backend.motors.SimMotor import SimMotor
from frontend.SmartDotGraph import SmartDotGraph
from frontend.SmartDotConnectWidget import SmartDotConnectWidget
from frontend.SensorGraphDialog import SensorGraphDialog
from frontend.OverrideDialog import OverrideDialog
import utils
if utils.is_raspberry_pi():
    from backend.smartdot.MetaMotionS import MetaMotion
else:
    from backend.smartdot.SimSmartDot import SimSmartDot

import datetime as dt


class DiagnosticModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)
    navigationLock = pyqtSignal(bool, str) # False = lock, True = unlock

    

    def __init__(self, parent=None):
        super().__init__(parent)
        
        #Set override mode to false initially
        self.OverrideMode = False

        # Load the UI file (module-relative path).
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'DiagnosticModePage.ui'), self, package='frontend')

        # Initialize diagnostic script object
        self.diagnostic_script = DiagnosticScript(bsc.motor1, bsc.motor2, bsc.motor3)

        #Buttons
        self.btnStart = self.findChild(QtWidgets.QPushButton, 'btnStart')
        self.btnStop = self.findChild(QtWidgets.QPushButton, 'btnStop')
        self.btnClear = self.findChild(QtWidgets.QPushButton, 'btnClear')
        self.btnSave = self.findChild(QtWidgets.QPushButton, 'btnSave')

        # Additional initialization code can go here
        self.spinGraph = self.findChild(pg.PlotWidget, 'grphSpin')
        self.tiltGraph = self.findChild(pg.PlotWidget, 'grphTilt')
        self.angleGraph = self.findChild(pg.PlotWidget, 'grphAngle')

        #label configurations
        self.labelSpin = self.findChild(QtWidgets.QLabel, 'lblSpin')
        self.labelTilt = self.findChild(QtWidgets.QLabel, 'lblTilt')
        self.labelAngle = self.findChild(QtWidgets.QLabel, 'lblAngle')
        # encoder value labels (UILabels may not be present in older UI versions)
        self.labelSpinEncoder = self.findChild(QtWidgets.QLabel, 'lblSpinEncoder')
        self.labelTiltEncoder = self.findChild(QtWidgets.QLabel, 'lblTiltEncoder')
        self.labelAngleEncoder = self.findChild(QtWidgets.QLabel, 'lblAngleEncoder')
        # if UI didn't provide labels, create them and insert in control rows
        def _make_label(existing, name, default_text):
            lbl = existing
            if lbl is None:
                lbl = QtWidgets.QLabel(default_text, self)
                lbl.setFont(self.labelSpin.font() if hasattr(self, 'labelSpin') else lbl.font())
                lbl.setObjectName(name)
            return lbl
        self.labelSpinEncoder = _make_label(self.labelSpinEncoder, 'lblSpinEncoder', 'Enc: 0.0 RPM')
        self.labelTiltEncoder = _make_label(self.labelTiltEncoder, 'lblTiltEncoder', 'Enc: 0.0 RPM')
        self.labelAngleEncoder = _make_label(self.labelAngleEncoder, 'lblAngleEncoder', 'Enc: 0.0 RPM')
        # attach newly created labels into the existing control layouts if needed
        def _attach_to_layout(label, reference_widget):
            if reference_widget is None or label is None:
                return
            parent = reference_widget.parent()
            if parent is not None and hasattr(parent, 'layout'):
                layout = parent.layout()
                if layout is not None and label not in [layout.itemAt(i).widget() for i in range(layout.count())]:
                    layout.addWidget(label)
        _attach_to_layout(self.labelSpinEncoder, self.labelSpin)
        _attach_to_layout(self.labelTiltEncoder, self.labelTilt)
        _attach_to_layout(self.labelAngleEncoder, self.labelAngle)
        #Spin boxes for values
        self.dsbSpin = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbSpinValue')
        self.dsbTilt = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbTiltValue')
        self.dsbAngle = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbAngleValue')

        # SmartDot initialization
        self.SmartDot = None  # Placeholder for the connected SmartDot device
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'grphSmartDot')
        self.smartdotConnectWidget = self.findChild(SmartDotConnectWidget, 'wgtSmartDotConnect')
        if self.smartdotConnectWidget:
            self.smartdotConnectWidget.signalSmartDotConnected.connect(self.connectSmartDot)
            self.smartdotConnectWidget.signalDeviceDisconnected.connect(self.on_device_disconnected)
        
        # SmartDot data arrays
        self.arrayGeneralTime = array('d', [0.0])
        self.arrayAccelerometer_X = array('f', [0.0])
        self.arrayAccelerometer_Y = array('f', [0.0])
        self.arrayAccelerometer_Z = array('f', [0.0])
        self.arrayGyroscope_X = array('f', [0.0])
        self.arrayGyroscope_Y = array('f', [0.0])
        self.arrayGyroscope_Z = array('f', [0.0])
        self.arrayMagnetometer_X = array('f', [0.0])
        self.arrayMagnetometer_Y = array('f', [0.0])
        self.arrayMagnetometer_Z = array('f', [0.0])
        self.arrayLight = array('f', [0.0])


        #Motor Sensor Data Viewer Setup
        #Current Value Labels
        self.Spincurv = self.findChild(QtWidgets.QLabel, 'lblSpinCurrent')
        self.Tiltcurv = self.findChild(QtWidgets.QLabel, 'lblTiltCurrent')
        self.Anglecurv = self.findChild(QtWidgets.QLabel, 'lblAngleCurrent')
        #Temp Value Labels
        self.Spintempv = self.findChild(QtWidgets.QLabel, 'lblSpinTemp')
        self.Tilttempv = self.findChild(QtWidgets.QLabel, 'lblTiltTemp')
        self.Angletempv = self.findChild(QtWidgets.QLabel, 'lblAngleTemp')

        #Example Initialization Values
        """
        self.Spincurv.setText("0.00 A")
        self.Tiltcurv.setText("0.00 A")
        self.Anglecurv.setText("0.00 A")
        self.Spintempv.setText("25.0 °C")
        self.Tilttempv.setText("25.0 °C")
        self.Angletempv.setText("25.0 °C")
        """
        #Buttons for graphs
        self.btnGraphTemp = self.findChild(QtWidgets.QPushButton, 'btnGraphTemp')
        self.btnGraphCurrent = self.findChild(QtWidgets.QPushButton, 'btnGraphCurrent')
        #Connect graph buttons
        self.btnGraphTemp.clicked.connect(self.show_temp_graph) #see method at bottom
        self.btnGraphCurrent.clicked.connect(self.show_current_graph) #see method at bottom

        #Sensor Arrays
        """example data arrays for input to graph dialog, feel free to use your own data collection methods"""
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
        
        #Configure Save Button
        self.btnSave.clicked.connect(self.openPostDialog)

        # configure Analyze button (added via UI)
        self.btnAnalyze = self.findChild(QtWidgets.QPushButton, 'btnAnalyze')
        if self.btnAnalyze:
            self.btnAnalyze.clicked.connect(self.analyze_data)
            # leave enabled so user can move to analysis at any time
            self.btnAnalyze.setEnabled(True)

        #configure OverrideButton
        self.btnOverride = self.findChild(QtWidgets.QPushButton, 'btnOverride')
        self.btnOverride.setCheckable(True)
        self.btnOverride.clicked.connect(self.toggle_override_mode)

        #Spin Motor graph setup
        self.spinGraph.setTitle("Diagnostic Spin Graph")
        self.spinGraph.setLabel('left', 'Spin Rate', units='RPM')
        self.spinGraph.setLabel('bottom', 'Time', units='s')
        # align colors with analysis mode: rpm=red, angle=green, tilt=blue
        self.spinCurve = self.spinGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#ff0000', width=2)) # rpm (spin)
        # encoder overlay on spin graph (encoder rpm cyan)
        self.spinEncoderCurve = self.spinGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#00ffff', width=1, style=pg.QtCore.Qt.PenStyle.DashLine), name='Spin Encoder')
        # tilt encoder overlay (encoder tilt yellow)
        self.tiltEncoderCurve = self.tiltGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#ffff00', width=1, style=pg.QtCore.Qt.PenStyle.DashLine), name='Tilt Encoder')
        # angle encoder overlay (encoder angle magenta)
        self.angleEncoderCurve = self.angleGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#ff00ff', width=1, style=pg.QtCore.Qt.PenStyle.DashLine), name='Angle Encoder')
        self.spinGraph.setYRange(0,620)
        self.spinGraph.setMouseEnabled(x=False, y=False)
        #Tilt Motor graph setup
        self.tiltGraph.setTitle("Diagnostic Tilt Graph")
        self.tiltGraph.setLabel('left', 'Tilt Angle', units='Degrees')
        self.tiltGraph.setLabel('bottom', 'Time', units='s')
        # tilt acts as motor angle in analysis (green)
        self.tiltCurve = self.tiltGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#00aa00', width=2)) #Extra refrence allows to be manipulated in thread
        self.tiltGraph.setYRange(-50,50)
        self.tiltGraph.setMouseEnabled(x=False, y=False)
        #Angle Motor graph setup
        self.angleGraph.setTitle("Diagnostic Angle Graph")
        self.angleGraph.setLabel('left', 'Angle', units='Degrees')
        self.angleGraph.setLabel('bottom', 'Time', units='s')
        # angle acts as motor tilt in analysis (blue)
        self.angleCurve = self.angleGraph.plot([0.0], [0.0], pen=pg.mkPen(color='#0000ff', width=2)) #Extra refrence allows to be manipulated in thread
        self.angleGraph.setYRange(-100,100)
        self.angleGraph.setMouseEnabled(x=False, y=False)
        # Slider configurations (replace dials with horizontal sliders)
        self.spinSlider = self.findChild(QtWidgets.QSlider, 'sliderSpin')
        self.tiltSlider = self.findChild(QtWidgets.QSlider, 'sliderTilt')
        self.angleSlider = self.findChild(QtWidgets.QSlider, 'sliderAngle')
        # Set slider ranges (orientation is set in UI file)
        self.spinSlider.setRange(0, 600)
        self.tiltSlider.setRange(-45, 45)
        self.angleSlider.setRange(-90, 90)

        # Always update labels when sliders move (even if timer is stopped)
        self.spinSlider.valueChanged.connect(self._update_slider_labels)
        self.tiltSlider.valueChanged.connect(self._update_slider_labels)
        self.angleSlider.valueChanged.connect(self._update_slider_labels)

        # Also update sliders when spin boxes change
        self.dsbSpin.valueChanged.connect(self._update_sliders_from_spinboxes)
        self.dsbTilt.valueChanged.connect(self._update_sliders_from_spinboxes)
        self.dsbAngle.valueChanged.connect(self._update_sliders_from_spinboxes)

        self._update_slider_labels()

        # Note: btnStart and btnStop are used for motors, not SmartDot updates
        self.btnStart.clicked.connect(lambda: self.toggle_Buttons())
        self.btnStop.clicked.connect(lambda: self.toggle_Buttons())
        self.btnClear.clicked.connect(lambda: self.clear_graphs())
        # Use a QTimer for periodic sampling & UI updates (runs in main thread)
        self._timer = QTimer(self)
        # Get sample interval from central `bsc` object (milliseconds) and clamp to >=50ms
        self._sample_interval_ms = max(50, bsc.diagnostic_sample_interval_ms)
        self._sample_dt_s = self._sample_interval_ms / 1000.0
        self._timer.setInterval(self._sample_interval_ms)
        self._timer.timeout.connect(self._on_timer)

        # Buffers: keep ~3s of history -> ~N samples based on sample interval
        self._maxlen = int((3000 // self._sample_interval_ms))
        # Numpy-backed circular buffers for fast, low-allocation updates
        self._N = max(1, self._maxlen)
        self._x = np.zeros(self._N, dtype=np.float64)
        self._spin_arr = np.zeros(self._N, dtype=np.float32)
        # axis encoder buffer copied alongside spin values
        self._spin_enc_arr = np.zeros(self._N, dtype=np.float32)
        self._tilt_arr = np.zeros(self._N, dtype=np.float32)
        self._angle_arr = np.zeros(self._N, dtype=np.float32)
        self._write_idx = 0
        self._filled = False

        self._last_values = {'spin': 0.0, 'tilt': 0.0, 'angle': 0.0}
        self._sample_index = 0  # drives quantized 50ms grid

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
    
    def toggle_Buttons(self):
            # Use timer activity to decide start/stop state
            if not self._timer.isActive():
                # Start
                self.btnStart.setEnabled(False)
                self.btnOverride.setEnabled(False)
                self.btnStop.setEnabled(True)
                self.diagnostic_script.start_motors([1,2,3])
                # start timer when entering active state
                self._sample_index = 0  # reset counter when starting
                self._timer.start()
                # Start SmartDot updates if connected
                if self.SmartDot is not None:
                    self.start_smartdot_updates()

                # Initialize the Session
                bsc.set_session(SessionData(id=-1, timeStamp=dt.datetime.now().isoformat(), name="Diagnostic Session", isShotMode=False))
                bsc.set_data_controller(DataController(bsc.get_session()))
                self.navigationLock.emit(False,"Motor Running")
            else:
                # Stop
                self.btnStart.setEnabled(True)
                self.btnOverride.setEnabled(True)
                self.btnStop.setEnabled(False)
                self.diagnostic_script.stop_motors([1,2,3])
                bsc.disconnect_all_motors()
                # stop periodic updates
                self._timer.stop()
                # Stop SmartDot updates if connected
                if self.SmartDot is not None:
                    self.stop_smartdot_updates()
                self.navigationLock.emit(True,"")


    def EStop(self):
        #Motor.stop() uncomment when motor works
        self.diagnostic_script.stop_motors([1,2,3])
        bsc.disconnect_all_motors()
        self.clear_graphs()
        self.btnStart.setEnabled(True)
        self.btnStop.setEnabled(False)
        # ensure periodic updates stopped
        self._timer.stop()
        # expose EStop publicly so other modules can call: instance.EStop()
    def add_diag_data_instance_to_data_controller(self, time: float, motor_id: int, instruction: float):
        dc: DataController = bsc.get_data_controller()
        data = DiagnosticScriptDataInstance(
            time=time,
            motor_id=motor_id,
            instruction=instruction
        )
        dc.add_diagnostic_script_data(data)

    def _on_timer(self):
        # Runs in main (GUI) thread. Poll sliders and update buffers + plots.
        # Called only when the timer is active; no separate `active` flag needed.
        # grab data controller early for encoder logging
        dc = bsc.get_data_controller()
        # Update SmartDot graph if device is connected
        if self.SmartDot is not None and self.SmartDotGraph is not None:
            self.SmartDotGraph.updateDataBetter(
                self.SmartDot.xl_time, self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,
                self.SmartDot.gy_time, self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,
                self.SmartDot.mg_time, self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,
                self.SmartDot.lt_time, self.SmartDot.lt_value
            )

        # Quantized time based on fixed interval (>=50ms)
        t = self._sample_index * self._sample_dt_s
        self._sample_index += 1

        spin_v = float(self.spinSlider.value())
        tilt_v = float(self.tiltSlider.value())
        angle_v = float(self.angleSlider.value())

        # Write into circular numpy buffers (in-place, no allocations)
        idx = self._write_idx
        self._x[idx] = t
        self._spin_arr[idx] = spin_v
        self._tilt_arr[idx] = tilt_v
        self._angle_arr[idx] = angle_v
        # sample encoders at same instant
        try:
            enc_sp = bsc.motor1.getCurrentSpeed()
        except Exception:
            enc_sp = 0.0
        try:
            enc_tl = bsc.motor2.getCurrentSpeed()
        except Exception:
            enc_tl = 0.0
        try:
            enc_ag = bsc.motor3.getCurrentSpeed()
        except Exception:
            enc_ag = 0.0
        self._spin_enc_arr[idx] = enc_sp
        self._tilt_enc_arr[idx] = enc_tl
        self._angle_enc_arr[idx] = enc_ag
        # record encoder readings every tick
        if dc is not None:
            dc.add_encoder_data(EncoderDataInstance(time=t, pulses=enc_sp, motor_id=1))
            dc.add_encoder_data(EncoderDataInstance(time=t, pulses=enc_tl, motor_id=2))
            dc.add_encoder_data(EncoderDataInstance(time=t, pulses=enc_ag, motor_id=3))
        # advance write index
        self._write_idx = (idx + 1) % self._N
        if self._write_idx == 0:
            self._filled = True

        # Only call change_speed/add data when value has changed; encoder labels update every tick
        if spin_v != self._last_values['spin']:
            # record encoder along with motor time when spin changes
            try:
                enc_sp = bsc.motor1.getCurrentSpeed()
            except Exception:
                enc_sp = 0.0
            dc.add_encoder_data(EncoderDataInstance(time=t, pulses=enc_sp, motor_id=1))
            self.add_diag_data_instance_to_data_controller(t, 0, spin_v)
            self._last_values['spin'] = spin_v
            self.labelSpin.setText(f"Spin Rate: {spin_v:.2f} RPM")
            
        # always refresh encoder label irrespective of change
        self.diagnostic_script.change_speed(0, spin_v)
        try:
            enc_sp = bsc.motor1.getCurrentSpeed()
        except Exception:
            enc_sp = 0.0
        if hasattr(self, 'labelSpinEncoder') and self.labelSpinEncoder:
            self.labelSpinEncoder.setText(f"Enc: {enc_sp:.1f} RPM")

        if tilt_v != self._last_values['tilt']:
            # record tilt encoder when tilt value changes
            try:
                enc_tl = bsc.motor2.getCurrentSpeed()
            except Exception:
                enc_tl = 0.0
            dc.add_encoder_data(EncoderDataInstance(time=t, pulses=enc_tl, motor_id=2))
            self.add_diag_data_instance_to_data_controller(t, 1, tilt_v)
            self._last_values['tilt'] = tilt_v
            self.labelTilt.setText(f"Tilt Angle: {tilt_v:.2f} Degrees")
            self.diagnostic_script.change_speed(1, tilt_v)
        # refresh tilt encoder label every tick
        try:
            enc_tl = bsc.motor2.getCurrentSpeed()
        except Exception:
            enc_tl = 0.0
        if hasattr(self, 'labelTiltEncoder') and self.labelTiltEncoder:
            self.labelTiltEncoder.setText(f"Enc: {enc_tl:.1f} RPM")

        if angle_v != self._last_values['angle']:
            # record angle encoder when angle value changes
            try:
                enc_ag = bsc.motor3.getCurrentSpeed()
            except Exception:
                enc_ag = 0.0
            dc.add_encoder_data(EncoderDataInstance(time=t, pulses=enc_ag, motor_id=3))
            self.add_diag_data_instance_to_data_controller(t, 2, angle_v)
            self._last_values['angle'] = angle_v
            self.labelAngle.setText(f"Angle: {angle_v:.2f} Degrees")
            self.diagnostic_script.change_speed(2, angle_v)
        # refresh angle encoder label every tick
        try:
            enc_ag = bsc.motor3.getCurrentSpeed()
        except Exception:
            enc_ag = 0.0
        if hasattr(self, 'labelAngleEncoder') and self.labelAngleEncoder:
            self.labelAngleEncoder.setText(f"Enc: {enc_ag:.1f} RPM")

        # Update graph x-ranges to show last ~3s
        # compute latest timestamp from circular buffer
        last_idx = (self._write_idx - 1) % self._N
        latest_t = float(self._x[last_idx])
        start_t = max(0, latest_t - 3.0)
        self.spinGraph.setXRange(start_t, latest_t)
        self.tiltGraph.setXRange(start_t, latest_t)
        self.angleGraph.setXRange(start_t, latest_t)

        # Plotting: build chronological views from circular buffers
        if not self._filled:
            count = self._write_idx
            x_view = self._x[:count]
            spin_view = self._spin_arr[:count]
            tilt_view = self._tilt_arr[:count]
            angle_view = self._angle_arr[:count]
            enc_view = self._spin_enc_arr[:count]
            tilt_enc_view = self._tilt_enc_arr[:count]
            angle_enc_view = self._angle_enc_arr[:count]
        else:
            idx = self._write_idx
            # concatenate tail + head to make chronological arrays
            x_view = np.concatenate((self._x[idx:], self._x[:idx]))
            spin_view = np.concatenate((self._spin_arr[idx:], self._spin_arr[:idx]))
            tilt_view = np.concatenate((self._tilt_arr[idx:], self._tilt_arr[:idx]))
            angle_view = np.concatenate((self._angle_arr[idx:], self._angle_arr[:idx]))
            enc_view = np.concatenate((self._spin_enc_arr[idx:], self._spin_enc_arr[:idx]))
            tilt_enc_view = np.concatenate((self._tilt_enc_arr[idx:], self._tilt_enc_arr[:idx]))
            angle_enc_view = np.concatenate((self._angle_enc_arr[idx:], self._angle_enc_arr[:idx]))

        # update plots with numpy arrays (pyqtgraph handles numpy)
        self.spinCurve.setData(x_view, spin_view)
        # plot encoder overlay if available
        try:
            self.spinEncoderCurve.setData(x_view, enc_view)
        except Exception:
            pass
        self.tiltCurve.setData(x_view, tilt_view)
        try:
            self.tiltEncoderCurve.setData(x_view, tilt_enc_view)
        except Exception:
            pass
        self.angleCurve.setData(x_view, angle_view)
        try:
            self.angleEncoderCurve.setData(x_view, angle_enc_view)
        except Exception:
            pass


    def _update_slider_labels(self):
        """Update motor spin boxes to reflect current slider values regardless of timer state."""
        spin_v = float(self.spinSlider.value())
        tilt_v = float(self.tiltSlider.value())
        angle_v = float(self.angleSlider.value())
        self.dsbSpin.setValue(spin_v)
        self.dsbTilt.setValue(tilt_v)
        self.dsbAngle.setValue(angle_v)
        # refresh encoder labels even if unchanged
        try:
            enc_sp = bsc.motor1.getCurrentSpeed()
        except Exception:
            enc_sp = 0.0
        try:
            enc_tl = bsc.motor2.getCurrentSpeed()
        except Exception:
            enc_tl = 0.0
        try:
            enc_ag = bsc.motor3.getCurrentSpeed()
        except Exception:
            enc_ag = 0.0


    def _update_sliders_from_spinboxes(self):
        """Update sliders to reflect current spin box values."""
        self.spinSlider.setValue(int(self.dsbSpin.value()))
        self.tiltSlider.setValue(int(self.dsbTilt.value()))
        self.angleSlider.setValue(int(self.dsbAngle.value()))

    def reset(self):
        # ensure not running and reset UI
        # Stop SmartDot updates if running
        if self.SmartDot is not None:
            self.stop_smartdot_updates()
        # Clear SmartDot data from the data controller so we start fresh
        dc = bsc.get_data_controller()
        if dc is not None:
            try:
                dc.smartdot_data.data_entries.clear()
            except AttributeError:
                pass
        self.clear_graphs()
        self.spinSlider.setValue(0)
        self.tiltSlider.setValue(0)
        self.angleSlider.setValue(0)
        # reset encoder labels if present
        if hasattr(self, 'labelSpinEncoder') and self.labelSpinEncoder:
            self.labelSpinEncoder.setText("Enc: 0.0 RPM")
        if hasattr(self, 'labelTiltEncoder') and self.labelTiltEncoder:
            self.labelTiltEncoder.setText("Enc: 0.0 RPM")
        if hasattr(self, 'labelAngleEncoder') and self.labelAngleEncoder:
            self.labelAngleEncoder.setText("Enc: 0.0 RPM")
        # ensure timer stopped
        self._timer.stop()
    
    def clear_graphs(self):
        # Clear instance buffers and reset plots
        # reset buffers and start time
        self._x = np.zeros(self._N, dtype=np.float64)
        self._spin_arr = np.zeros(self._N, dtype=np.float32)
        self._spin_enc_arr = np.zeros(self._N, dtype=np.float32)
        self._tilt_arr = np.zeros(self._N, dtype=np.float32)
        self._tilt_enc_arr = np.zeros(self._N, dtype=np.float32)
        self._angle_arr = np.zeros(self._N, dtype=np.float32)
        self._angle_enc_arr = np.zeros(self._N, dtype=np.float32)
        self._write_idx = 0
        self._filled = False
        self.spinCurve.setData([0.0], [0.0])
        self.tiltCurve.setData([0.0], [0.0])
        self.angleCurve.setData([0.0], [0.0])
        # also clear encoder overlays
        self.spinEncoderCurve.setData([0.0], [0.0])
        self.tiltEncoderCurve.setData([0.0], [0.0])
        self.angleEncoderCurve.setData([0.0], [0.0])
        
        # Clear SmartDot graph data if available
        if self.SmartDotGraph is not None:
            if hasattr(self.SmartDotGraph, 'clear'):
                self.SmartDotGraph.clear()   
    
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
    
    def toggle_enable_override(self, enable: bool):
        self.OverrideMode = enable
        # Get the main window (top-level parent)
        main_window = self.window()
        
        if self.OverrideMode:
            print("Override Mode Enabled")
            # Mark override mode for QSS styling
            self._apply_override_style(True)
            # Lock navigation when override mode is enabled
            self.navigationLock.emit(False,"Override Mode Enabled")
            # set extended ranges for sliders
            self.spinSlider.setRange(0, 1200)
            self.tiltSlider.setRange(-359, 359)
            self.angleSlider.setRange(-359, 359)
            # extend spin box ranges accordingly
            self.dsbSpin.setRange(0, 1200)
            self.dsbTilt.setRange(-359, 359)
            self.dsbAngle.setRange(-359, 359)
            #update graph Y ranges
            self.spinGraph.setYRange(0,1250)
            self.tiltGraph.setYRange(-400,400)
            self.angleGraph.setYRange(-400,400)
        else:
            print("Override Mode Disabled")
            # Clear override mode styling flag
            self._apply_override_style(False)
            # Unlock navigation when override mode is disabled
            self.navigationLock.emit(True,"")
            # reset sliders to safe ranges
            self.spinSlider.setRange(0, 600)
            self.tiltSlider.setRange(-90, 90)
            self.angleSlider.setRange(-45, 45)
            # reset spin box ranges accordingly
            self.dsbSpin.setRange(0, 600)
            self.dsbTilt.setRange(-90, 90)
            self.dsbAngle.setRange(-45, 45)
            #update graph Y ranges
            self.spinGraph.setYRange(0,620)
            self.tiltGraph.setYRange(-100,100)
            self.angleGraph.setYRange(-50,50)
            
        # Reset UI and state whenever override toggles
        self.reset()

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
    
    def connectSmartDot(self, device):
        """Called when a SmartDot device is connected."""
        print("Connecting SmartDot...")
        self.SmartDot = device
        print(f"SmartDot: {self.SmartDot}")
        print(f"Smart dot type: {type(self.SmartDot)}")

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
        for i in range(len(self.SmartDot.xl_time)):
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
        for i in range(len(self.SmartDot.gy_time)):
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
        for i in range(len(self.SmartDot.mg_time)):
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
        for i in range(len(self.SmartDot.lt_time)):
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
    
    def on_device_disconnected(self, mac_address):
        """Called when device disconnects."""
        print(f"Device disconnected: {mac_address}")
        # Stop updates if running
        if self._timer.isActive():
            self.stop_smartdot_updates()
        # Clear the SmartDot reference
        self.SmartDot = None
    
    def start_smartdot_updates(self):
        """Start collecting data from SmartDot."""
        if self.SmartDot is not None:
            print("Starting SmartDot data collection")
            self.SmartDot.startCollecting()
    
    def stop_smartdot_updates(self):
        """Stop collecting data from SmartDot."""
        if self.SmartDot is not None:
            print("Stopping SmartDot data collection")
            self.SmartDot.stopCollecting()
            # when we stop collecting we can also package what we've gathered
            self._package_smartdot_data_to_controller()

    def analyze_data(self):
        """Handler for the Analyze button.

        Packages any remaining SmartDot samples and then transitions to the
        analysis page by emitting the changePage signal with the active
        DataController (same behaviour as DataViewPage.analyze_data).
        """
        print("Analyze Data Clicked")
        # ensure collected samples are stored in the controller
        self._package_smartdot_data_to_controller()
        dc = bsc.get_data_controller()
        if dc is None:
            return
        self.changePage.emit(3, dc)



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