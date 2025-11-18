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

class ShotViewPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)


        # Load the UI file (module-relative path).

        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ShotViewPage.ui'), self, package='frontend')
        #Buttons


        self.motorGraph = self.findChild(MotorGraph, 'motorGraph')
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'smartDotGraph')
        self.pushButton = self.findChild(QtWidgets.QPushButton, 'pushButton')

        self.scriptSpin = np.array([])
        self.scriptTilt = np.array([])
        self.scriptAngle = np.array([])


        self.displayedSpin = np.array([])
        self.displayedTilt = np.array([])
        self.displayedAngle = np.array([])
        self.displayedTime = np.array([])
        self.ElapsedTime = 0.0
        self.count = 0
        self.MaxTime = 0.0
        self.dt = 1 #Should never run as this

        self.timer = QTimer(self)

        def StartShotView(self, MotorData):
            self.scriptSpin = MotorData.spin
            self.scriptTilt = MotorData.tilt
            self.scriptAngle = MotorData.angle
            self.MaxTime = MotorData.length 

            interval_ms = max(1, int(self.dt * 1000))
            self.timer.setInterval(interval_ms)
            self.timer.timeout.connect(lambda: UpdateShotView(self, self.dt))
            self.timer.start()


        
        def UpdateShotView(self, dt):
            self.ElapsedTime += dt
            self.displayedTime = np.append(self.displayedTime, self.ElapsedTime)
            self.displayedSpin = np.append(self.displayedSpin, self.scriptSpin[self.count])
            self.displayedTilt = np.append(self.displayedTilt, self.scriptTilt[self.count])
            self.displayedAngle = np.append(self.displayedAngle, self.scriptAngle[self.count])
            self.motorGraph.UpdateGraph(self.displayedTime, self.displayedSpin, self.displayedTilt, self.displayedAngle)
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