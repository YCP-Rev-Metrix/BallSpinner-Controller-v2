import time
from PyQt6 import QtWidgets, uic
import os
from PyQt6.QtCore import Qt, QTimer
import numpy as np

from .MotorGraph import MotorGraph
from .SmartDotGraph import SmartDotGraph
import math
from PyQt6.QtCore import pyqtSignal
from backend.models.SmartDotData import SmartDotDataInstance
import pyqtgraph as pg
from BSC import bsc


class AnalysisDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, type: str = None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'AnalysisDialog.ui'), self, package='frontend')
        self.label = self.findChild(QtWidgets.QLabel, 'label')
        self.label.setText(type)
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, 'buttonBox')
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.graph = self.findChild(pg.PlotWidget, 'graph')
        
        self.setWindowTitle("Analysis Options")
        self.setModal(True)
        self.resize(800, 800)








class AnalysisModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the UI file (module-relative path).
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'AnalysisModePage.ui'), self, package='frontend')
        self.smartDotGraph = self.findChild(SmartDotGraph, 'SmartDotGraph')
        self.motorGraph = self.findChild(MotorGraph, 'MotorGraph')
        self.smartDotGraph.setView(0)  # Set SmartDotGraph to show all data
        self.motorGraph.setView(0)     # Set MotorGraph to show all data

        self.btnSave = self.findChild(QtWidgets.QPushButton, 'btnSave')
        self.btnSave.clicked.connect(self.openPostDialog)

        self.btnOp1 = self.findChild(QtWidgets.QPushButton, 'btnOp1')
        self.btnOp2 = self.findChild(QtWidgets.QPushButton, 'btnOp2')
        self.btnOp3 = self.findChild(QtWidgets.QPushButton, 'btnOp3')
        self.btnOp4 = self.findChild(QtWidgets.QPushButton, 'btnOp4')

        self.btnOp1.clicked.connect(lambda: self.openAnalysisDialog("Option 1 Analysis"))
        self.btnOp2.clicked.connect(lambda: self.openAnalysisDialog("Option 2 Analysis"))
        self.btnOp3.clicked.connect(lambda: self.openAnalysisDialog("Option 3 Analysis"))
        self.btnOp4.clicked.connect(lambda: self.openAnalysisDialog("Option 4 Analysis"))

    def openAnalysisDialog(self, type: str):
        dialog = AnalysisDialog(self, type)
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            print("User accepted the dialog.")
            # Handle acceptance (e.g., proceed with analysis)
        else:
            print("User rejected the dialog.")
            # Handle rejection (e.g., cancel operation)


    def openPostDialog(self):
        from .PostDialog import PostDialog
        dialog = PostDialog(self)
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            print("User accepted the dialog.")
            # Handle acceptance (e.g., save data)
        else:
            print("User rejected the dialog.")
            # Handle rejection (e.g., cancel operation)

    def loadData(self):
        dc = bsc.get_data_controller()
        # Load SmartDot data from BSC data controller
        smartdot_data = dc.smartdot_data

        time_accel = []
        accel_x = []
        accel_y = []
        accel_z = []
        time_gyro = []
        gyro_x = []
        gyro_y = []
        gyro_z = []
        time_mag = []
        mag_x = []
        mag_y = []
        mag_z = []
        time_light = []
        light = []
        
        
        for data in smartdot_data.data_entries:
            if data.data_selector == 0:  # Accelerometer
                time_accel.append(data.time)
                accel_x.append(data.accelerometer_x)
                accel_y.append(data.accelerometer_y)
                accel_z.append(data.accelerometer_z)
            elif data.data_selector == 1:  # Gyroscope
                time_gyro.append(data.time)
                gyro_x.append(data.gyroscope_x)
                gyro_y.append(data.gyroscope_y)
                gyro_z.append(data.gyroscope_z)
            elif data.data_selector == 2:  # Magnetometer
                time_mag.append(data.time)
                mag_x.append(data.magnetometer_x)
                mag_y.append(data.magnetometer_y)
                mag_z.append(data.magnetometer_z)
            elif data.data_selector == 3:  # Light
                time_light.append(data.time)
                light.append(data.light)

        # Update SmartDot graph
        self.smartDotGraph.updateDataBetter(
            time_accel, accel_x, accel_y, accel_z,
            time_gyro, gyro_x, gyro_y, gyro_z,
            time_mag, mag_x, mag_y, mag_z,
            time_light, light
        )
        # Load Motor data from BSC data controller
        motor_data = dc.shot_script_data.get_shot_script_data_entries()
       
        time_motor = []
        motor_rpm = []
        motor_angleDeg = []
        motor_tiltDeg = []

        for data in motor_data:
            time_motor.append(data.time)
            motor_rpm.append(data.rpm)
            motor_angleDeg.append(data.angleDeg)
            motor_tiltDeg.append(data.tiltDeg)



        #Get encoder values
        time_encoder = []
        encoder_rpm = []
        encoder_angle = []
        encoder_tilt = []

        #TODO: Get store encoder data if we are using encoders, using 0.0 as temp
        time_encoder = [0.0]
        encoder_rpm = [0.0]
        encoder_angle = [0.0]
        encoder_tilt = [0.0]

        
            
        if time_motor == []:
            diag_data = dc.diagnostic_data.get_diagnostic_data_entries()
            time_rpm = []
            time_angle = []
            time_tilt = []
            for data in diag_data:
                match data.motor_id:
                    case 0:
                        time_rpm.append(data.time)
                        motor_rpm.append(data.instruction)
                    case 1:
                        time_angle.append(data.time)
                        motor_angleDeg.append(data.instruction)
                    case 2:
                        time_tilt.append(data.time)
                        motor_tiltDeg.append(data.instruction)
                    case _:
                        pass
            # Update Motor graph
            self.motorGraph.updateDataDiagnostic(time_rpm, motor_rpm, time_angle, motor_angleDeg, time_tilt, motor_tiltDeg
                                                 ,time_encoder, encoder_rpm, encoder_angle, encoder_tilt
                                                 ,[],[],[],[])
        else:
        # Update Motor graph
            self.motorGraph.updateDataBetter(time_motor, motor_rpm, motor_angleDeg, motor_tiltDeg, time_encoder, encoder_rpm, encoder_angle, encoder_tilt)
        


if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # Create and show the main window
    window = AnalysisModePage()
    window.setBaseSize(1920, 1080)
    window.setWindowTitle("Analysis Mode Page")
    window.show()

    # Start the event loop
    sys.exit(app.exec())
