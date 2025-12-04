import time
from PyQt6 import QtWidgets, uic, QtCore
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
import utils
from utils import PackageSmartDotData, SmartDotDataPackage, PackageMotorData, MotorDataPackage

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

        # Enable touch events on dialog controls and buttons
        try:
            try:
                self.buttonBox.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            except Exception:
                pass
        except Exception:
            pass
        
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

        # Accept touch events on operation buttons
        try:
            for b in (self.btnSave, self.btnOp1, self.btnOp2, self.btnOp3, self.btnOp4):
                if b is not None:
                    try:
                        b.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
                    except Exception:
                        pass
        except Exception:
            pass

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

    def loadData(self):
        dc = bsc.get_data_controller()
        # Update SmartDot graph
        smartdot_package = utils.PackageSmartDotData(self, bsc)
        self.smartDotGraph.updateDataBetter(
            smartdot_package.time_accel, smartdot_package.accel_x, smartdot_package.accel_y, smartdot_package.accel_z,
            smartdot_package.time_gyro, smartdot_package.gyro_x, smartdot_package.gyro_y, smartdot_package.gyro_z,
            smartdot_package.time_mag, smartdot_package.mag_x, smartdot_package.mag_y, smartdot_package.mag_z,
            smartdot_package.time_light, smartdot_package.light
        )

        # Update Motor graph
        motor_package = utils.PackageMotorData(self, bsc)
        self.motorGraph.updateDataDiagnostic(
            motor_package.time_rpm, motor_package.motor_rpm,
            motor_package.time_angle, motor_package.motor_angleDeg,
            motor_package.time_tilt, motor_package.motor_tiltDeg,
            motor_package.time_encoder, motor_package.encoder_rpm, motor_package.encoder_angle, motor_package.encoder_tilt
        )

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
