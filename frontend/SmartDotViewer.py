from PyQt6 import QtWidgets, QtCore, uic
from PyQt6.QtCore import Qt, QTimer
import numpy as np
from array import array
from frontend.SmartDotGraph import SmartDotGraph
from frontend.SmartDotConnectWidget import SmartDotConnectWidget
import math
import utils
if utils.is_raspberry_pi():
    from backend.smartdot.MetaMotionS import MetaMotion
else:
    from backend.smartdot.SimSmartDot import SimSmartDot
from PyQt6.QtCore import pyqtSignal


class SmartDotViewer(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        import os
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'SmartDotViewer.ui'), self, package='frontend')

        # Find the embedded SmartDotGraph widget created by the .ui (named SmartDotGraphContainer)
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'smartDotGraph')
        """
        self.btnDisconnect = self.findChild(QtWidgets.QPushButton, 'btnDisconnect')
        self.btnDisconnect.clicked.connect(self.disconnectSmartDot)
        """
        self.smartdotConnectWidget = self.findChild(SmartDotConnectWidget, 'SmartDotConnect')
        # self.smartdotConnectWidget.start_scan()
        self.smartdotConnectWidget.signalSmartDotConnected.connect(self.connectSmartDot)
        self.smartdotConnectWidget.signalDeviceDisconnected.connect(self.on_device_disconnected)

        

        self.SmartDot = None  # Placeholder for the connected SmartDot device

        # Instance arrays to persist between timer callbacks
        self.arrayGeneralTime = array('d', [0.0])
        self.arrayAccelerometer_X = array('f', [0.0])
        self.arrayAccelerometer_Y = array('f', [0.0])
        self.arrayAccelerometer_Z = array('f', [0.0])
        self.arrayGyroscope_X = array('f', [0.0])
        self.arrayGyroscope_Y = array('f', [0.0])
        self.arrayGyroscope_Z = array('f', [0.0])
        self.arrayMagnetometer_X = array('f', [0.0])
        self.arrayMagnetometer_Y = array('f', [0.0])
        self.arrayMagnetometer_Z = array('f', [0.0])
        self.arrayLight = array('f', [0.0])

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
    def hide_buttons(self):
        if self.btnStart:
            self.btnStart.setVisible(False)
        if self.btnStop:
            self.btnStop.setVisible(False)
    def show_buttons(self):
        if self.btnStart:
            self.btnStart.setVisible(True)
        if self.btnStop:
            self.btnStop.setVisible(True)
    

    def disconnectSmartDot(self):
        self.btnStart.setEnabled(False)
        # Here you would add the actual disconnection code
        if self.SmartDot:
            print("Disconnecting SmartDot...")
            self.SmartDot.disconnect()
    
    def on_device_disconnected(self, mac_address):
        """Called when device disconnects"""
        print(f"Device disconnected: {mac_address}")
        # Disable the disconnect button
        if self.btnDisconnect:
            self.btnDisconnect.setEnabled(False)
        # Disable start/stop buttons since device is disconnected
        if self.btnStart:
            self.btnStart.setEnabled(False)
        if self.btnStop:
            self.btnStop.setEnabled(False)
        # Stop timer if running
        if self._timer.isActive():
            self._timer.stop()
        self.active = False
        # Clear the SmartDot reference
        self.SmartDot = None
    
    def connectSmartDot(self, device):
        print("Connecting SmartDot...")
        self.SmartDot = device
        self.btnStart.setEnabled(True)
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
    widget = SmartDotViewer()
    widget.show()
    sys.exit(app.exec())
