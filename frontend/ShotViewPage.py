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
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread, QThreadPool, QRunnable, QObject
#Database related imports
from frontend.SmartDotGraph import SmartDotGraph
from frontend.MotorGraph import MotorGraph

from BSC import bsc, MotorData


# Configure a simple file logger for thread finish times
from logs.logger_config import get_logger
_logger = get_logger(__name__)





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
        # Thread pool for motor tasks and active task tracking
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(9)
        # Keep track of active worker runnables so they are not garbage collected
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
        print("Packaging motor data for Shot View")
        motor_package = utils.PackageMotorData(self, bsc)
        print("Motor data packaged")
        self.scriptSpin = motor_package.motor_rpm
        self.scriptTilt = motor_package.motor_tiltDeg
        self.scriptAngle = motor_package.motor_angleDeg
        self.MaxTime = motor_package.time_rpm[-1]  # assuming motor_data is sorted by time
        self.dt = motor_package.time_rpm[1] - motor_package.time_rpm[0]  # interval in seconds
        self.dt_ms = int(self.dt * 1000)

        self.shot_script.start_motors([0, 1, 2])
        time_values = []
        t = 0.0
        time_values = np.arange(0.25, self.MaxTime, self.dt)
         
        # reset displayed data and counters
        self.displayedSpin = array('f')
        self.displayedTilt = array('f')
        self.displayedAngle = array('f')
        # Reset per-motor time buffers (was using displayedTime previously which caused stale data)
        self.displayedSpinTime = array('d')
        self.displayedTiltTime = array('d')
        self.displayedAngleTime = array('d')
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
        # clear any leftover active thread refs from previous run
        try:
            self._active_threads.clear()
        except Exception:
            self._active_threads = []

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
        if self.SmartDot:
            # SmartDot buffers are array.array; convert to numpy arrays for plotting APIs that expect them
            # pass SmartDot buffers directly (they are array.array)
            self.SmartDotGraph.updateDataBetter(self.SmartDot.xl_time, self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,
                                                self.SmartDot.gy_time, self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,
                                                self.SmartDot.mg_time, self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,
                                                self.SmartDot.lt_time, self.SmartDot.lt_value)
        # Guard: if there is no script data, throw an error (invalid state)
        if len(self.scriptSpin) == 0:
            raise RuntimeError("UpdateShotView called but 'scriptSpin' is empty. Ensure StartShotView populated script data before starting.")

        # Guard: ensure index in range before accessing script arrays — treat as programming error
        if self.count >= len(self.scriptSpin):
            raise IndexError(f"UpdateShotView index {self.count} out of range for 'scriptSpin' length {len(self.scriptSpin)}")

        # Spawn a worker thread per motor that then calls change_speed_single
        try:
            self.spawn_motor_thread("Spin", 0, self.scriptSpin[self.count])
        except Exception as e:
            #print("Error spawning Spin motor thread:", e)
            pass
        
        try:
            self.spawn_motor_thread("Tilt", 1, self.scriptTilt[self.count])
        except Exception as e:
            pass
        
        try:
            self.spawn_motor_thread("Angle", 2, self.scriptAngle[self.count])
        except Exception as e:
            pass
            
        self.motorGraph.updateDataDiagnostic(
                        self.displayedSpinTime, self.displayedSpin,
                        self.displayedTiltTime, self.displayedTilt,
                        self.displayedAngleTime, self.displayedAngle,
                        array('d', [0.0]), array('f', [0.0]),array('f', [0.0]), array('f', [0.0]))    
        # advance to next index after spawning motor tasks
        self.count += 1

        if(self.ElapsedTime > self.MaxTime or self.count >= len(self.scriptSpin)):
            self.EndShotView()
            return


    class WorkerSignals(QObject):
        finished = pyqtSignal(object)


    class MotorRunnable(QRunnable):
        """A QRunnable that calls ShotScript.change_speed_single and emits a finished signal."""
        def __init__(self, motor_index: int, value: float, shot_script: ShotScript, signals: 'ShotViewPage.WorkerSignals'):
            super().__init__()
            self.motor_index = motor_index
            self.value = value
            self.shot_script = shot_script
            self.signals = signals

        def run(self):
            try:
                self.shot_script.change_speed_single(self.motor_index, self.value)
                result = {'motor_index': self.motor_index, 'value': self.value}
            except Exception as e:
                result = {'motor_index': self.motor_index, 'value': self.value, 'error': str(e)}
            try:
                # Emit finished result back to the GUI thread
                self.signals.finished.emit(result)
            except Exception:
                pass

    def spawn_motor_thread(self, motor: str, motor_index: int, value: float):
        """Submit a motor command to the QThreadPool as a QRunnable worker."""
        signals = ShotViewPage.WorkerSignals()
        runnable = ShotViewPage.MotorRunnable(motor_index, value, self.shot_script, signals)
        # keep reference so the runnable and its signals are not garbage collected
        self._active_threads.append(runnable)
        signals.finished.connect(lambda data, r=runnable: self._on_thread_finished(r, data))
        # Start the runnable in the pool
        self._thread_pool.start(runnable)

    def _on_thread_finished(self, worker: QThread, data: object):
        # Called when a worker thread emits finished_signal
        try:
            # remove worker/runnable from active list
            try:
                self._active_threads.remove(worker)
            except ValueError:
                pass
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
        # For QRunnable workers we don't have quit/wait/deleteLater; they will finish on their own.
        try:
            # Nothing to explicitly quit for QRunnable; ensure it's removed from active list above.
            pass
        except Exception:
            pass



    def EndShotView(self):
        #Stop timer
        self.timer.stop()
        #Ensure all motors are stopped
        self.shot_script.stop_motors()
        # Wait for thread pool tasks to complete (bounded). Then clear active task refs.
        try:
            # Wait up to 2 seconds for the pool to finish outstanding tasks
            self._thread_pool.waitForDone(2000)
        except Exception:
            pass
        try:
            self._active_threads.clear()
        except Exception:
            self._active_threads = []
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