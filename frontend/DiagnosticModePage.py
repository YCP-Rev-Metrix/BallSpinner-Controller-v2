from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np
pg.setConfigOptions(antialias=False)
import os
from PyQt6.QtCore import pyqtSignal, QTimer

#Database related imports
from BSC import bsc
from backend.models.SessionData import SessionData
from backend.models.DataController import DataController
from backend.models.DiagnosticScriptData import DiagnosticScriptDataInstance
from backend.drivers.DiagnosticScript import DiagnosticScript
#from backend.motors.BDCMotor import BDCMotor
#from backend.motors.SimMotor import SimMotor
from frontend.SmartDotViewer import SmartDotViewer
from frontend.SensorGraphDialog import SensorGraphDialog
from frontend.OverrideDialog import OverrideDialog

import datetime as dt


class DiagnosticModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)
    navigationLock = pyqtSignal(bool) # False = lock, True = unlock

    

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
        #Spin boxes for values
        self.dsbSpin = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbSpinValue')
        self.dsbTilt = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbTiltValue')
        self.dsbAngle = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbAngleValue')

        #load SmartDotViewer
        self.smartdotViewer = self.findChild(QtWidgets.QWidget, 'SmartDotViewer')
        self.smartdotViewer.hide_buttons()


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

        #configure OverrideButton
        self.btnOverride = self.findChild(QtWidgets.QPushButton, 'btnOverride')
        self.btnOverride.setCheckable(True)
        self.btnOverride.clicked.connect(self.toggle_override_mode)

        #Spin Motor graph setup
        self.spinGraph.setTitle("Diagnostic Spin Graph")
        self.spinGraph.setLabel('left', 'Spin Rate', units='RPM')
        self.spinGraph.setLabel('bottom', 'Time', units='s')
        self.spinCurve = self.spinGraph.plot([0.0], [0.0], pen=pg.mkPen(color='b', width=2)) #Extra refrence allows to be manipulated in thread
        self.spinGraph.setYRange(0,620)
        self.spinGraph.setMouseEnabled(x=False, y=False)
        #Tilt Motor graph setup
        self.tiltGraph.setTitle("Diagnostic Tilt Graph")
        self.tiltGraph.setLabel('left', 'Tilt Angle', units='Degrees')
        self.tiltGraph.setLabel('bottom', 'Time', units='s')
        self.tiltCurve = self.tiltGraph.plot([0.0], [0.0], pen=pg.mkPen(color='r', width=2)) #Extra refrence allows to be manipulated in thread
        self.tiltGraph.setYRange(-100,100)
        self.tiltGraph.setMouseEnabled(x=False, y=False)
        #Angle Motor graph setup
        self.angleGraph.setTitle("Diagnostic Angle Graph")
        self.angleGraph.setLabel('left', 'Angle', units='Degrees')
        self.angleGraph.setLabel('bottom', 'Time', units='s')
        self.angleCurve = self.angleGraph.plot([0.0], [0.0], pen=pg.mkPen(color='g', width=2)) #Extra refrence allows to be manipulated in thread
        self.angleGraph.setYRange(-50,50)
        self.angleGraph.setMouseEnabled(x=False, y=False)
        #Dial configurations
        self.spinDial = self.findChild(QtWidgets.QDial, 'dialSpin')
        self.tiltDial = self.findChild(QtWidgets.QDial, 'dialTilt')
        self.angleDial = self.findChild(QtWidgets.QDial, 'dialAngle')
        self.spinDial.setRange(0, 600)  # Set dial range from 0 to 600
        self.tiltDial.setRange(-90, 90)  # Set dial range from -90 to 90
        self.angleDial.setRange(-45, 45)  # Set dial range from -45 to 45

        # Always update labels when dials move (even if timer is stopped)
        self.spinDial.valueChanged.connect(self._update_dial_labels)
        self.tiltDial.valueChanged.connect(self._update_dial_labels)
        self.angleDial.valueChanged.connect(self._update_dial_labels)
        
        # Also update dials when spin boxes change
        self.dsbSpin.valueChanged.connect(self._update_dials_from_spinboxes)
        self.dsbTilt.valueChanged.connect(self._update_dials_from_spinboxes)
        self.dsbAngle.valueChanged.connect(self._update_dials_from_spinboxes)
        
        self._update_dial_labels()

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
                self.btnStop.setEnabled(True)
                self.diagnostic_script.start_motors([1,2,3])
                # start timer when entering active state
                self._sample_index = 0  # reset counter when starting
                self._timer.start()
                # Start SmartDotViewer updates if connected
                if len(bsc.get_smartdotConnectionManager().get_connections()) > 0:
                    self.smartdotViewer.start_updates()

                # Initialize the Session
                bsc.set_session(SessionData(id=-1, timeStamp=dt.datetime.now().isoformat(), name="Diagnostic Session", isShotMode=False))
                bsc.set_data_controller(DataController(bsc.get_session()))
                self.navigationLock.emit(False)
            else:
                # Stop
                self.btnStart.setEnabled(True)
                self.btnStop.setEnabled(False)
                self.diagnostic_script.stop_motors([1,2,3])
                bsc.disconnect_all_motors()
                # stop periodic updates
                self._timer.stop()
                # Stop SmartDotViewer updates if connected
                if len(bsc.get_smartdotConnectionManager().get_connections()) > 0:
                    self.smartdotViewer.stop_updates()
                self.navigationLock.emit(True)


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
        # Runs in main (GUI) thread. Poll dials and update buffers + plots.
        # Called only when the timer is active; no separate `active` flag needed.

        # Quantized time based on fixed interval (>=50ms)
        t = self._sample_index * self._sample_dt_s
        self._sample_index += 1

        spin_v = float(self.spinDial.value())
        tilt_v = float(self.tiltDial.value())
        angle_v = float(self.angleDial.value())

        # Write into circular numpy buffers (in-place, no allocations)
        idx = self._write_idx
        self._x[idx] = t
        self._spin_arr[idx] = spin_v
        self._tilt_arr[idx] = tilt_v
        self._angle_arr[idx] = angle_v
        # advance write index
        self._write_idx = (idx + 1) % self._N
        if self._write_idx == 0:
            self._filled = True

        # Only call change_speed / add data when value has changed
        if spin_v != self._last_values['spin']:
            self.add_diag_data_instance_to_data_controller(t, 0, spin_v)
            self._last_values['spin'] = spin_v
            self.labelSpin.setText(f"Spin Rate: {spin_v:.2f} RPM")
        self.diagnostic_script.change_speed(0, spin_v)

        if tilt_v != self._last_values['tilt']:
            self.diagnostic_script.change_speed(1, tilt_v)
            self.add_diag_data_instance_to_data_controller(t, 1, tilt_v)
            self._last_values['tilt'] = tilt_v
            self.labelTilt.setText(f"Tilt Angle: {tilt_v:.2f} Degrees")

        if angle_v != self._last_values['angle']:
            self.diagnostic_script.change_speed(2, angle_v)
            self.add_diag_data_instance_to_data_controller(t, 2, angle_v)
            self._last_values['angle'] = angle_v
            self.labelAngle.setText(f"Angle: {angle_v:.2f} Degrees")

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
        else:
            idx = self._write_idx
            # concatenate tail + head to make chronological arrays
            x_view = np.concatenate((self._x[idx:], self._x[:idx]))
            spin_view = np.concatenate((self._spin_arr[idx:], self._spin_arr[:idx]))
            tilt_view = np.concatenate((self._tilt_arr[idx:], self._tilt_arr[:idx]))
            angle_view = np.concatenate((self._angle_arr[idx:], self._angle_arr[:idx]))

        # update plots with numpy arrays (pyqtgraph handles numpy)
        self.spinCurve.setData(x_view, spin_view)
        self.tiltCurve.setData(x_view, tilt_view)
        self.angleCurve.setData(x_view, angle_view)


    def _update_dial_labels(self):
        """Update motor spin boxes to reflect current dial values regardless of timer state."""
        spin_v = float(self.spinDial.value())
        tilt_v = float(self.tiltDial.value())
        angle_v = float(self.angleDial.value())
        self.dsbSpin.setValue(spin_v)
        self.dsbTilt.setValue(tilt_v)
        self.dsbAngle.setValue(angle_v)

    def _update_dials_from_spinboxes(self):
        """Update dials to reflect current spin box values."""
        self.spinDial.setValue(int(self.dsbSpin.value()))
        self.tiltDial.setValue(int(self.dsbTilt.value()))
        self.angleDial.setValue(int(self.dsbAngle.value()))



    def reset(self):
        # ensure not running and reset UI
        self.smartdotViewer.reset()
        # Clear SmartDot data from the data controller so we start fresh
        dc = bsc.get_data_controller()
        if dc is not None:
            try:
                dc.smartdot_data.data_entries.clear()
            except AttributeError:
                pass
        self.clear_graphs()
        self.spinDial.setValue(0)
        self.tiltDial.setValue(0)
        self.angleDial.setValue(0)
        # ensure timer stopped
        self._timer.stop()
    
    def clear_graphs(self):
        # Clear instance buffers and reset plots
        # reset buffers and start time
        self._x = np.zeros(self._N, dtype=np.float64)
        self._spin_arr = np.zeros(self._N, dtype=np.float32)
        self._tilt_arr = np.zeros(self._N, dtype=np.float32)
        self._angle_arr = np.zeros(self._N, dtype=np.float32)
        self._write_idx = 0
        self._filled = False
        self.spinCurve.setData([0.0], [0.0])
        self.tiltCurve.setData([0.0], [0.0])
        self.angleCurve.setData([0.0], [0.0])
    
    
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
            # Set main window background to dark red when override mode is enabled
            main_window.setStyleSheet("background-color: #cc0000;")
            # Lock navigation when override mode is enabled
            self.navigationLock.emit(False)
            # set extended ranges for dials
            self.spinDial.setRange(0, 1200)  # Set dial range from 0 to 1200
            self.tiltDial.setRange(-359, 359)  # Set dial range from -359 to 359
            self.angleDial.setRange(-359, 359)  # Set dial range from -359 to 359
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
            # Reset main window background to default when override mode is disabled
            main_window.setStyleSheet("")
            # Unlock navigation when override mode is disabled
            self.navigationLock.emit(True)
            # reset dials to safe ranges
            self.spinDial.setRange(0, 600)  # Set dial range from 0 to 600
            self.tiltDial.setRange(-90, 90)  # Set dial range from -90 to 90
            self.angleDial.setRange(-45, 45)  # Set dial range from -45 to 45
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