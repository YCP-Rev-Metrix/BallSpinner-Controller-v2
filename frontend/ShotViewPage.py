from PyQt6 import QtWidgets, uic
from backend.Motors.BDCMotor import BDCMotor
from backend.Motors.SimMotor import SimMotor
import pyqtgraph as pg
import numpy as np
import threading
import time
import os
import io
from backend.models.SmartDotData import SmartDotDataInstance
import utils
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt, QTimer
from frontend.SmartDotGraph import SmartDotGraph
from frontend.MotorGraph import MotorGraph

from BSC import bsc, MotorData


class ShotViewPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)


        # Load the UI file (module-relative path).

        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ShotViewPage.ui'), self, package='frontend')
        #Buttons


        self.motorGraph = self.findChild(MotorGraph, 'MotorGraph')
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'SmartDotGraph')
        self.pushButton = self.findChild(QtWidgets.QPushButton, 'pushButton')

        self.scriptSpin = np.array([])
        self.scriptTilt = np.array([])
        self.scriptAngle = np.array([])

        self.SmartDot = None
        self.ConnectionManager = bsc.smartdotConnectionManager

        if(len(self.ConnectionManager.get_smartdots()) > 0):
            try:
                self.SmartDot = self.ConnectionManager.get_connections()[0]
                print("SmartDot connected:", self.SmartDot)
            except Exception as e:
                print("Error connecting to SmartDot:", e)
        

        self.displayedSpin = np.array([])
        self.displayedTilt = np.array([])
        self.displayedAngle = np.array([])
        self.displayedTime = np.array([])
        self.ElapsedTime = 0.0
        self.count = 0
        self.MaxTime = 0.0
        self.dt = 1 #Should never run as this

        self.timer = QTimer(self)
        # Expose the nested StartShotView as a public method on the instance
 
    def StartShotView(self, Data):
        self.scriptSpin = Data.spin
        self.scriptTilt = Data.tilt
        self.scriptAngle = Data.angle
        self.MaxTime = Data.length 
        # Keep seconds and milliseconds explicitly
        self.dt = float(Data.dt)            # interval in seconds
        self.dt_ms = int(self.dt * 1000)   # interval in milliseconds for QTimer

        # reset displayed data and counters
        self.displayedSpin = np.array([])
        self.displayedTilt = np.array([])
        self.displayedAngle = np.array([])
        self.displayedTime = np.array([])
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
        self.timer.start()

        


        
    def UpdateShotView(self):
        # Update using seconds so MaxTime comparison is consistent
        self.ElapsedTime += self.dt
        self.displayedTime = np.append(self.displayedTime, self.ElapsedTime)
        self.displayedSpin = np.append(self.displayedSpin, self.scriptSpin[self.count])
        self.displayedTilt = np.append(self.displayedTilt, self.scriptTilt[self.count])
        self.displayedAngle = np.append(self.displayedAngle, self.scriptAngle[self.count])
        self.motorGraph.updateDataBetter(self.displayedTime, self.displayedSpin, self.displayedTilt, self.displayedAngle,np.array([0.0]),np.array([0.0]),np.array([0.0]),np.array([0.0]))
        print("Updating Shot View:", self.ElapsedTime, self.count)
        if self.SmartDot:
            self.SmartDotGraph.updateDataBetter(self.SmartDot.xl_time,self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,
                                                self.SmartDot.gy_time,self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,
                                                self.SmartDot.mg_time, self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,
                                                self.SmartDot.lt_time, self.SmartDot.lt_value)
        self.count += 1
        if(self.ElapsedTime >= self.MaxTime):
            self.EndShotView()
            return
    def EndShotView(self):
        self.timer.stop()
        if self.SmartDot:
            self.SmartDot.stopCollecting()
            #Get datacontroller
            dc = bsc.get_data_controller()
            for i in range(0,len(self.SmartDot.xl_time)):
                dc.add_smartdot_data(SmartDotDataInstance(
                    sessionData=bsc.get_session(),
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
                    sessionData=bsc.get_session(),
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
                    sessionData=bsc.get_session(),
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
                    sessionData=bsc.get_session(),
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
        print("Shot View Ended")
        

            


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