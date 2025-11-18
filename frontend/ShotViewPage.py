from PyQt6 import QtWidgets, uic
from backend.Motors.BDCMotor import BDCMotor
from backend.Motors.SimMotor import SimMotor
import pyqtgraph as pg
import numpy as np
import threading
import time
import os
import io
import utils
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt, QTimer
from frontend.SmartDotGraph import SmartDotGraph
from frontend.MotorGraph import MotorGraph

from BSC import BSC, MotorData


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
        self.ConnectionManager = BSC().smartdotConnectionManager
        """
            if self.ConnectionManager.is_connected():
            self.SmartDot = self.ConnectionManager.get_connected_device()
            print("SmartDot connected:", self.SmartDot)
        """
        try:
            self.SmartDot = self.ConnectionManager.get_smartdots()[0]
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

        print("Starting Shot View with interval (ms):", self.dt_ms)
        print("Max Time (sec):", self.MaxTime)

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
            self.timer.stop()
            return
            


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