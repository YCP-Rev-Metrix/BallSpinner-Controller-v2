import time
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QTimer
import numpy as np
from SmartDotGraph import SmartDotGraph
import math


class AnalysisModePage(QtWidgets.QWidget):
    """Analysis mode page that generates simulated sensor data and displays it
    in the embedded SmartDotGraph widget. A QTimer runs on the GUI thread and
    is started/stopped by the Start/Stop buttons in the UI.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the UI file.
        uic.loadUi('AnalysisModePage.ui', self)

        # Find the embedded SmartDotGraph widget created by the .ui (named SmartDotGraphContainer)
        self.SmartDotGraph = self.findChild(SmartDotGraph, 'SmartDotGraphContainer')

        # Active flag to control updates; start stopped until user presses Start
        self.active = False

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

        # Timer interval (ms) — made configurable via an instance variable
        self.timer_interval_ms = 15  # default milliseconds (~66.7 Hz)

        # Use a QTimer on the GUI thread (safe for UI updates)
        self._timer = QTimer(self)
        self._timer.setInterval(self.timer_interval_ms)
        self._timer.timeout.connect(self._on_timer)
        # Timer will be started/stopped by buttons; do not start here

        # Wire Start/Stop buttons from the UI
        self.btnStart = self.findChild(QtWidgets.QPushButton, 'btn_Test_Start')
        self.btnStop = self.findChild(QtWidgets.QPushButton, 'btn_TestStop')
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
        self.arrayGeneralTime = np.append(self.arrayGeneralTime, self.arrayGeneralTime[-1] + dt)
        self.arrayAccelerometer_X = np.append(self.arrayAccelerometer_X, math.sin(self.arrayGeneralTime[-1]) * 5 + 5)
        self.arrayAccelerometer_Y = np.append(self.arrayAccelerometer_Y, math.cos(self.arrayGeneralTime[-1]) * 5 + 5)
        self.arrayAccelerometer_Z = np.append(self.arrayAccelerometer_Z, math.sin(self.arrayGeneralTime[-1]) * 5 + 5)
        self.arrayGyroscope_X = np.append(self.arrayGyroscope_X, math.cos(self.arrayGeneralTime[-1]*2) * 5 + 5)
        self.arrayGyroscope_Y = np.append(self.arrayGyroscope_Y, math.sin(self.arrayGeneralTime[-1]*2) * 5 + 5)
        self.arrayGyroscope_Z = np.append(self.arrayGyroscope_Z, math.cos(self.arrayGeneralTime[-1]*2) * 5 + 5)
        self.arrayMagnetometer_X = np.append(self.arrayMagnetometer_X, math.sin(self.arrayGeneralTime[-1]*0.5) * 5 + 5)
        self.arrayMagnetometer_Y = np.append(self.arrayMagnetometer_Y, math.cos(self.arrayGeneralTime[-1]*0.5) * 5 + 5)
        self.arrayMagnetometer_Z = np.append(self.arrayMagnetometer_Z, math.sin(self.arrayGeneralTime[-1]*0.5) * 5 + 5)
        self.arrayLight = np.append(self.arrayLight, np.mod(self.arrayGeneralTime[-1]*3, 10))

        # Update the embedded graph widget (runs on GUI thread)
        if self.SmartDotGraph is not None:
            try:
                self.SmartDotGraph.UpdateData(self.arrayGeneralTime,
                                              self.arrayAccelerometer_X, self.arrayAccelerometer_Y, self.arrayAccelerometer_Z,
                                              self.arrayGyroscope_X, self.arrayGyroscope_Y, self.arrayGyroscope_Z,
                                              self.arrayMagnetometer_X, self.arrayMagnetometer_Y, self.arrayMagnetometer_Z,
                                              self.arrayLight)
            except Exception:
                # Avoid bringing down the GUI; if needed, replace with logging
                pass


if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # Create and show the main window
    window = AnalysisModePage()
    window.setGeometry(100, 100, 800, 600)  # x, y, width, height
    window.setWindowTitle("Analysis Mode Page")
    window.show()

    # Start the event loop
    sys.exit(app.exec())
