from PyQt6 import QtWidgets, uic
from backend.drivers.ShotScript import ShotScript
#from backend.motors.USBBDCMotor import USBBDCMotor
#from backend.motors.SimMotor import SimMotor
import pyqtgraph as pg
import numpy as np
from array import array
import threading
import time
import os
import io
import logging
import datetime
from backend.models.SmartDotData import SmartDotDataInstance
import utils
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
#Database related imports
from frontend.SmartDotGraph import SmartDotGraph
from frontend.MotorGraph import MotorGraph

from BSC import bsc, MotorData
"""
# Configure a simple file logger for thread finish times
_logger = logging.getLogger('ShotViewPageThreadLogger')
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    try:
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, 'shotview_thread_times.log')
    except Exception:
        log_path = os.path.abspath('shotview_thread_times.log')
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(fmt)
    _logger.addHandler(fh)
"""



class ShotViewPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)
    navigationLock = pyqtSignal(bool) # False = lock, True = unlock
    #motor1 = USBBDCMotor()
    def __init__(self, parent=None):
        super().__init__(parent)

        #sim_motor2 = SimMotor(2)
        #sim_motor3 = SimMotor(3)
        #self.shot_script = ShotScript(self.motor1, sim_motor2, sim_motor3)
        self.shot_script = ShotScript(bsc.motor1, bsc.motor2, bsc.motor3)


        # Load the UI file (module-relative path).

        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ShotViewPage.ui'), self, package='frontend')
        #Buttons


        self.motorGraph = self.findChild(MotorGraph, 'MotorGraph')
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'SmartDotGraph')
        self.btnAnalyze = self.findChild(QtWidgets.QPushButton, 'btnAnalyze')
        self.btnAnalyze.clicked.connect(lambda: self.changePage.emit(3, "SampleText"))  # Go back to Home Page
        self.btnAnalyze.setEnabled(False)  # Disabled during shot view

        self.scriptSpin = array('f')
        self.scriptTilt = array('f')
        self.scriptAngle = array('f')

        self.SmartDot = None
        self.ConnectionManager = bsc.smartdotConnectionManager

        if(len(self.ConnectionManager.get_smartdots()) > 0):
            try:
                self.SmartDot = self.ConnectionManager.get_connections()[0]
                print("SmartDot connected:", self.SmartDot)
            except Exception as e:
                print("Error connecting to SmartDot:", e)
        

        self.displayedSpin = array('f')
        self.displayedTilt = array('f')
        self.displayedAngle = array('f')
        self.displayedSpinTime = array('d')
        self.displayedTiltTime = array('d')
        self.displayedAngleTime = array('d')
        self.ElapsedTime = 0.0
        self.count = 0
        self.MaxTime = 0.0
        self.dt = 1 #Should never run as this
        self.startTime = time.time() #Record start time of shot view

        self.timer = QTimer(self)
        # Keep track of active worker threads so they are not garbage collected
        self._active_threads = []

        # A small label on the page to show process output (created dynamically)
        try:
            layout = self.layout()
            if layout is None:
                from PyQt6.QtWidgets import QVBoxLayout
                layout = QVBoxLayout(self)
                self.setLayout(layout)
        except Exception:
            layout = None
        self.processOutputLabel = QtWidgets.QLabel(self)
        self.processOutputLabel.setObjectName('processOutputLabel')
        if layout is not None:
            layout.addWidget(self.processOutputLabel)
        # Expose the nested StartShotView as a public method on the instance
        

    def StartShotView(self):
        Controller = bsc.get_data_controller()
        self.btnAnalyze.setEnabled(False)  # Disabled during shot view
        self.navigationLock.emit(False) # Lock navigation during shot view
        

        if Controller.session_data.isShotMode:
            #Parse shot script data
            motor_package = utils.PackageMotorData(self, bsc)
            self.scriptSpin = motor_package.motor_rpm
            self.scriptTilt = motor_package.motor_tiltDeg
            self.scriptAngle = motor_package.motor_angleDeg
            self.MaxTime = motor_package.time_rpm[-1]  # assuming motor_data is sorted by time
            self.dt = motor_package.time_rpm[1] - motor_package.time_rpm[0]  # interval in seconds
            self.dt_ms = int(self.dt * 1000)
        else:
            #Parse diagnostic data if no shot script data
            self.scriptSpin = array('f')
            self.scriptTilt = array('f')
            self.scriptAngle = array('f')
            diag_data = Controller.diagnostic_data.get_diagnostic_data_entries()
            self.MaxTime = diag_data[-1].time  # assuming motor_data is sorted by time
            self.dt = bsc.diagnostic_sample_interval_ms / 1000.0  # interval in seconds
            self.dt_ms = int(self.dt * 1000)
            # check data at 0.25s intervals
            self.scriptSpin.append(0.0)
            self.scriptTilt.append(0.0)
            self.scriptAngle.append(0.0)
            for i in np.arange(0.25, self.MaxTime, self.dt):
                # find closest diag data for each motor
                spin_val = self.scriptSpin[-1]
                tilt_val = self.scriptTilt[-1]
                angle_val = self.scriptAngle[-1]
                for data in diag_data:
                    if abs(data.time - i) < self.dt / 2:
                        match data.motor_id:
                            case 0:
                                spin_val = data.instruction
                            case 1:
                                angle_val = data.instruction
                            case 2:
                                tilt_val = data.instruction
                            case _:
                                pass
                self.scriptSpin.append(spin_val)
                self.scriptTilt.append(tilt_val)
                self.scriptAngle.append(angle_val)

        self.shot_script.start_motors([0, 1, 2])
        time_values = []
        t = 0.0
        time_values = np.arange(0.25, self.MaxTime, self.dt)
         
        # reset displayed data and counters
        self.displayedSpin = array('f')
        self.displayedTilt = array('f')
        self.displayedAngle = array('f')
        self.displayedTime = array('d')
        self.ElapsedTime = 0.0
        self.count = 0
        if(len(self.ConnectionManager.get_smartdots()) > 0):
            try:
                self.SmartDot = self.ConnectionManager.get_smartdots()[0]
                print("SmartDot connected:", self.SmartDot)
            except Exception as e:
                print("Error connecting to SmartDot:", e)

        print("Starting Shot View with interval (ms):", self.dt_ms)
        print("Max Time (sec):", self.MaxTime)

        if (self.SmartDot):
            print("Using SmartDot in Shot View")
            self.SmartDot.startCollecting()
        else:
            print("No SmartDot connected in Shot View")

        self.timer.setInterval(self.dt_ms)
        # connect to UpdateShotView without passing ms; UpdateShotView will use seconds
        try:
            # disconnect previous connections if any
            self.timer.timeout.disconnect()
        except Exception:
            pass
        
        self.timer.timeout.connect(self.UpdateShotView)
        self.startTime = time.time() #Record start time of shot view
        self.timer.start()
        
        # Only call interpolate / set_motor_times_from_indices if motor supports them
        try:
            if hasattr(bsc.motor2, 'interpolate'):
                bsc.motor2.interpolate(self.scriptTilt)
            if hasattr(bsc.motor2, 'set_motor_times_from_indices'):
                bsc.motor2.set_motor_times_from_indices(time_values)
        except Exception as e:
            print("Warning: motor2 interpolation skipped:", e)



        
    def UpdateShotView(self):
        # Update using seconds so MaxTime comparison is consistent
        self.ElapsedTime += self.dt
        # append to array.array buffers (fast, low overhead)
        """
        #Move to on thread completion
        self.displayedTime.append(self.ElapsedTime)
        self.displayedSpin.append(self.scriptSpin[self.count])
        self.displayedTilt.append(self.scriptTilt[self.count])
        self.displayedAngle.append(self.scriptAngle[self.count])
        # motorGraph may expect numpy arrays; convert on-call
        # pass array.array buffers directly to avoid allocating ndarrays each update
        self.motorGraph.updateDataBetter(self.displayedTime, self.displayedSpin, self.displayedTilt, self.displayedAngle,
                         array('d', [0.0]), array('f', [0.0]), array('f', [0.0]), array('f', [0.0]))
        """
        if self.SmartDot:
            # SmartDot buffers are array.array; convert to numpy arrays for plotting APIs that expect them
            # pass SmartDot buffers directly (they are array.array)
            self.SmartDotGraph.updateDataBetter(self.SmartDot.xl_time, self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,
                                                self.SmartDot.gy_time, self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,
                                                self.SmartDot.mg_time, self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,
                                                self.SmartDot.lt_time, self.SmartDot.lt_value)
        self.count += 1



        # Change speeds for all motors atomically
        self.shot_script.change_speed([self.scriptSpin[self.count],self.scriptTilt[self.count],self.scriptAngle[self.count]])

        # Spawn a worker thread per motor that then calls change_speed_single
        self.spawn_motor_thread("Spin", 0, self.scriptSpin[self.count])
        self.spawn_motor_thread("Tilt", 1, self.scriptTilt[self.count])
        self.spawn_motor_thread("Angle", 2, self.scriptAngle[self.count])

        self.motorGraph.updateDataDiagnostic(
                        self.displayedSpinTime, self.displayedSpin,
                        self.displayedTiltTime, self.displayedTilt,
                        self.displayedAngleTime, self.displayedAngle,
                        array('d', [0.0]), array('f', [0.0]),array('f', [0.0]), array('f', [0.0]))    
        if(self.ElapsedTime >= self.MaxTime or self.count >= len(self.scriptSpin)):
            self.EndShotView()
            return


    class _MotorWorker(QThread):
        finished_signal = pyqtSignal(object)

        def __init__(self, motor_index: int, value: float, shot_script: ShotScript, parent=None):
            super().__init__(parent)
            self.motor_index = motor_index
            self.value = value
            self.shot_script = shot_script

        def run(self):
            
            try:
                self.shot_script.change_speed_single(self.motor_index, self.value)

                result = {'motor_index': self.motor_index, 'value': self.value,}
            except Exception as e:
                result = {'motor_index': self.motor_index, 'value': self.value, 'error': str(e)}

            self.finished_signal.emit(result)

    def spawn_motor_thread(self, motor: str, motor_index: int, value: float):
        """Spawn a QThread worker that counts and then calls ShotScript.change_speed_single."""
        worker = ShotViewPage._MotorWorker(motor_index, value, self.shot_script, parent=self)
        # keep reference
        self._active_threads.append(worker)
        worker.finished_signal.connect(lambda data, w=worker: self._on_thread_finished(w, data))
        worker.start()

    def _on_thread_finished(self, worker: QThread, data: object):
        # Called when a worker thread emits finished_signal
        try:
            # remove worker from active list
            self._active_threads.remove(worker)
        except ValueError:
            pass
        # compute time delta since last append for this motor and append value and delta
        try:
            self.motor_index = None
            self.value = None
            if isinstance(data, dict):
                self.motor_index = data.get('motor_index')
                self.value = data.get('value')
            # fallback if data is an object with attributes
            else:
                self.motor_index = getattr(data, 'motor_index', None)
                self.value = getattr(data, 'value', None)
            self.now = time.time()
            self.delta = self.now - self.startTime

            if self.motor_index == 0:
                # append motor value and delta to spin lists
                try:
                    self.displayedSpin.append(self.value)
                except Exception:
                    pass
                try:
                    self.displayedSpinTime.append(self.delta)
                except Exception:
                    pass
            elif self.motor_index == 1:
                try:
                    self.displayedTilt.append(self.value)
                except Exception:
                    pass
                try:
                    self.displayedTiltTime.append(self.delta)
                except Exception:
                    pass
            elif self.motor_index == 2:
                try:
                    self.displayedAngle.append(self.value)
                except Exception:
                    pass
                try:
                    self.displayedAngleTime.append(self.delta)
                except Exception:
                    pass

            # Logging: compute start/end times for the motor call based on reported duration (if available) 
            #_logger.info(f"Motor {self.motor_index} set to {self.value} at elapsed time {self.delta:.3f} sec. Now: {self.now:.3f} StartTime: {self.startTime:.3f}")
        except Exception as e:
            print("Error in _on_thread_finished processing:", e)
        # schedule deletion
        worker.quit()
        worker.wait(100)
        worker.deleteLater()



    def EndShotView(self):
        self.timer.stop()
        #Ensure all motors are stopped
        self.shot_script.stop_motors()
        #Make graph final update
        self.motorGraph.updateDataDiagnostic(
                        self.displayedSpinTime, self.displayedSpin,
                        self.displayedTiltTime, self.displayedTilt,
                        self.displayedAngleTime, self.displayedAngle,
                        array('d', [0.0]), array('f', [0.0]),array('f', [0.0]), array('f', [0.0]))
        # Update SmartDot graph only if SmartDot data is available
        if self.SmartDot:
            try:
                self.SmartDotGraph.updateDataBetter(self.SmartDot.xl_time, self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,
                                                    self.SmartDot.gy_time, self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,
                                                    self.SmartDot.mg_time, self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,
                                                    self.SmartDot.lt_time, self.SmartDot.lt_value)
            except Exception as e:
                print("Warning: SmartDotGraph update failed:", e)
        #Collect SmartDot data into DataController
        if self.SmartDot:
            self.SmartDot.stopCollecting()
            #Get datacontroller
            dc = bsc.get_data_controller()
            for i in range(0,len(self.SmartDot.xl_time)):
                dc.add_smartdot_data(SmartDotDataInstance(
                    time=self.SmartDot.xl_time[i],
                    data_selector=0, #Accelerometer
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
            for i in range(0,len(self.SmartDot.gy_time)):
                dc.add_smartdot_data(SmartDotDataInstance(
                    time=self.SmartDot.gy_time[i],
                    data_selector=1, #Gyroscope
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
            for i in range(0,len(self.SmartDot.mg_time)):
                dc.add_smartdot_data(SmartDotDataInstance(
                    time=self.SmartDot.mg_time[i],
                    data_selector=2, #Magnetometer
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
            for i in range(0,len(self.SmartDot.lt_time)):
                dc.add_smartdot_data(SmartDotDataInstance(
                    time=self.SmartDot.lt_time[i],
                    data_selector=3, #Light
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
            print("Submitted SmartDot data to DataController")
        if(utils.is_raspberry_pi()):
            bsc.disconnect_all_motors()
        print("Shot View Ended")
        self.btnAnalyze.setEnabled(True)  # Enable Analyze button after shot view
        self.navigationLock.emit(True) # Unlock navigation after shot view
        

            


if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = ShotViewPage()
    window.setWindowTitle("Shot View Page")
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())