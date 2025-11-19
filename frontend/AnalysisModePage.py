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
from BSC import bsc



class AnalysisModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the UI file (module-relative path).
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'AnalysisModePage.ui'), self, package='frontend')
        self.smartDotGraph = self.findChild(SmartDotGraph, 'SmartDotGraph')
        self.motorGraph = self.findChild(MotorGraph, 'MotorGraph')


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

        #TODO: Add Diagnostic Support

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
