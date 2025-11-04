from PyQt6 import QtWidgets, QtCore, uic
from PyQt6.QtCore import Qt, QTimer
import numpy as np
from SmartDotGraph import SmartDotGraph
from SmartDotConnectWidget import SmartDotConnectWidget
import math
import utils
if utils.is_raspberry_pi():
    from backend.smartdot.MetaMotionS import MetaMotion
else:
    from backend.smartdot.SimSmartDot import SimSmartDot
from PyQt6.QtCore import pyqtSignal


class SmartDotTestPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (name matches file in repo)
        uic.loadUi('SmartDotTestPage.ui', self)

        # Find the embedded SmartDotGraph widget created by the .ui (named SmartDotGraphContainer)
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'smartDotGraph')
        self.btnDisconnect = self.findChild(QtWidgets.QPushButton, 'btnDisconnect')
        self.btnDisconnect.clicked.connect(self.disconnectSmartDot)
        # Initially disable disconnect until a SmartDot is connected
        if self.btnDisconnect:
            self.btnDisconnect.setEnabled(False)
        self.smartdotConnectWidget = self.findChild(SmartDotConnectWidget, 'SmartDotConnect')
        self.smartdotConnectWidget.signalSmartDotConnected.connect(self.connectSmartDot)

        

        self.SmartDot = None  # Placeholder for the connected SmartDot device

        # Instance arrays to persist between timer callbacks
        self.arrayGeneralTime = np.array([0.0])
        self.arrayAccelerometer_X = np.array([0.0])
        self.arrayAccelerometer_Y = np.array([0.0])
        self.arrayAccelerometer_Z = np.array([0.0])
        self.arrayGyroscope_X = np.array([0.0])
        self.arrayGyroscope_Y = np.array([0.0])
        self.arrayGyroscope_Z = np.array([0.0])
        self.arrayMagnetometer_X = np.array([0.0])
        self.arrayMagnetometer_Y = np.array([0.0])
        self.arrayMagnetometer_Z = np.array([0.0])
        self.arrayLight = np.array([0.0])

        # Timer interval (ms) 
        self.timer_interval_ms = 15  # default milliseconds 

        # Use a QTimer on the GUI thread (safe for UI updates)
        self._timer = QTimer(self)
        self._timer.setInterval(self.timer_interval_ms)
        self._timer.timeout.connect(self._on_timer)
        # Timer will be started/stopped by buttons; do not start here

        # Wire Start/Stop buttons from the UI
        self.btnStart = self.findChild(QtWidgets.QPushButton, 'btnStart')
        self.btnStop = self.findChild(QtWidgets.QPushButton, 'btnStop')

       
        if self.btnStart:
            self.btnStart.clicked.connect(self.start_updates)
        if self.btnStop:
            self.btnStop.clicked.connect(self.stop_updates)

        # Set initial button states
        if self.btnStart:
            self.btnStart.setEnabled(False)
        if self.btnStop:
            self.btnStop.setEnabled(False)

    def disconnectSmartDot(self):
        print("Disconnecting SmartDot...")
        self.btnStart.setEnabled(False)
        # Here you would add the actual disconnection code
        if self.SmartDot:
            self.SmartDot.disconnect()
    def connectSmartDot(self, device):
        print("Connecting SmartDot...")
        self.SmartDot = device
        self.btnStart.setEnabled(True)
        # Enable disconnect once a device is connected
        if self.btnDisconnect:
            self.btnDisconnect.setEnabled(True)
        print(f"SmartDot: {self.SmartDot}")
        print(f"Smart dot type: {type(self.SmartDot)}")
        # Here you would add the actual connection code
        

    def start_updates(self):
        """Start the QTimer and enable periodic updates."""
        if not self._timer.isActive():
            self._timer.start()
            self.active = True
            print("start collecting")
            self.SmartDot.startCollecting()
            # While collecting, prevent disconnecting
            if self.btnDisconnect:
                self.btnDisconnect.setEnabled(False)
        if self.btnStart:
            self.btnStart.setEnabled(False)
        if self.btnStop:
            self.btnStop.setEnabled(True)

    def stop_updates(self):
        """Stop the QTimer and pause updates."""
     
        if self._timer.isActive():
            self._timer.stop()
        self.active = False
        print("stop collecting")
        self.SmartDot.stopCollecting()
        # Re-enable disconnect after collecting stops
        if self.btnDisconnect:
            self.btnDisconnect.setEnabled(True)
        if self.btnStart:
            self.btnStart.setEnabled(True)
        if self.btnStop:
            self.btnStop.setEnabled(False)

    def _on_timer(self):
        """Called on the GUI thread by QTimer every 15 ms to generate and push data to the graph."""
        if self.SmartDot:
            self.SmartDotGraph.updateDataBetter(self.SmartDot.xl_time,self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,
                                                self.SmartDot.gy_time,self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,
                                                self.SmartDot.mg_time, self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,
                                                self.SmartDot.lt_time, self.SmartDot.lt_value)
            #UpdateData(self.SmartDot.xl_time,self.SmartDot.xl_x, self.SmartDot.xl_y, self.SmartDot.xl_z,self.SmartDot.gy_x, self.SmartDot.gy_y, self.SmartDot.gy_z,self.SmartDot.mg_x, self.SmartDot.mg_y, self.SmartDot.mg_z,self.SmartDot.lt_value)
            return
        if not self.active:
            return
        # Simulate data generation
        # Use the current configured timer interval to compute the time step
        dt = float(self.timer_interval_ms) / 1000.0
        """
        Collect data points from the SmartDot device here.
        add the new data points to the respective arrays.
        self.arrayGeneralTime = np.append(self.arrayGeneralTime, self.arrayGeneralTime[-1] + dt)
        self.arrayAccelerometer_X = np.append(self.arrayAccelerometer_X, <new_accel_x_value>)
        self.arrayAccelerometer_Y = np.append(self.arrayAccelerometer_Y,  <new_accel_y_value>)
        self.arrayAccelerometer_Z = np.append(self.arrayAccelerometer_Z,  <new_accel_z_value>)
        self.arrayGyroscope_X = np.append(self.arrayGyroscope_X,  <new_gyro_x_value>)
        self.arrayGyroscope_Y = np.append(self.arrayGyroscope_Y,  <new_gyro_y_value>)
        self.arrayGyroscope_Z = np.append(self.arrayGyroscope_Z,  <new_gyro_z_value>)
        self.arrayMagnetometer_X = np.append(self.arrayMagnetometer_X,  <new_mag_x_value>)
        self.arrayMagnetometer_Y = np.append(self.arrayMagnetometer_Y,  <new_mag_y_value>)
        self.arrayMagnetometer_Z = np.append(self.arrayMagnetometer_Z,  <new_mag_z_value>)
        self.arrayLight = np.append(self.arrayLight, <new_light_value>)
        """

        # Update the embedded graph widget (runs on GUI thread)
        
        #self.SmartDotGraph.UpdateData(self.arrayGeneralTime,self.arrayAccelerometer_X, self.arrayAccelerometer_Y, self.arrayAccelerometer_Z,self.arrayGyroscope_X, self.arrayGyroscope_Y, self.arrayGyroscope_Z,self.arrayMagnetometer_X, self.arrayMagnetometer_Y, self.arrayMagnetometer_Z,self.arrayLight)


    def test_connection(self):
        # Simulate testing connection logic
        print("Testing SmartDot connection...")
        # Here you would add the actual connection testing code
        self.lblConnectionStatus.setText("Connection Successful!")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = SmartDotTestPage()
    widget.show()
    sys.exit(app.exec())