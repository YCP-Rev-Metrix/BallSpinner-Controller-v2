from PyQt6 import QtWidgets, QtCore, uic
from PyQt6.QtCore import Qt, QTimer
import numpy as np
from SmartDotGraph import SmartDotGraph
import math

class SmartDotTestPage(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (name matches file in repo)
        uic.loadUi('SmartDotTestPage.ui', self)

        # Find the embedded SmartDotGraph widget created by the .ui (named SmartDotGraphContainer)
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'smartDotGraph')
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
            self.btnStart.setEnabled(True)
        if self.btnStop:
            self.btnStop.setEnabled(False)

    def start_updates(self):
        """Start the QTimer and enable periodic updates."""
        if not self._timer.isActive():
            self._timer.start()
        self.active = True
        if self.btnStart:
            self.btnStart.setEnabled(False)
        if self.btnStop:
            self.btnStop.setEnabled(True)

    def stop_updates(self):
        """Stop the QTimer and pause updates."""
        if self._timer.isActive():
            self._timer.stop()
        self.active = False
        if self.btnStart:
            self.btnStart.setEnabled(True)
        if self.btnStop:
            self.btnStop.setEnabled(False)

    def _on_timer(self):
        """Called on the GUI thread by QTimer every 15 ms to generate and push data to the graph."""
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

        self.SmartDotGraph.UpdateData(self.arrayGeneralTime,self.arrayAccelerometer_X, self.arrayAccelerometer_Y, self.arrayAccelerometer_Z,self.arrayGyroscope_X, self.arrayGyroscope_Y, self.arrayGyroscope_Z,self.arrayMagnetometer_X, self.arrayMagnetometer_Y, self.arrayMagnetometer_Z,self.arrayLight)


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