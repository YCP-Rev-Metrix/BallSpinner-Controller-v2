from unittest import case
from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np

# Module-level arrays used by the graph update. Kept as globals for minimal changes

class SmartDotGraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load the UI file.
        uic.loadUi('SmartDotGraph.ui', self)

        # Get references to UI elements
        self.graph = self.findChild(pg.PlotWidget, 'graphSmartDot')

        self.chkAccelerometer_X = self.findChild(QtWidgets.QCheckBox, 'chkXL_X')
        self.chkAccelerometer_Y = self.findChild(QtWidgets.QCheckBox, 'chkXL_Y')
        self.chkAccelerometer_Z = self.findChild(QtWidgets.QCheckBox, 'chkXL_Z')
        self.chkGyroscope_X = self.findChild(QtWidgets.QCheckBox, 'chkGL_X')
        self.chkGyroscope_Y = self.findChild(QtWidgets.QCheckBox, 'chkGL_Y')
        self.chkGyroscope_Z = self.findChild(QtWidgets.QCheckBox, 'chkGL_Z')   
        self.chkMagnetometer_X = self.findChild(QtWidgets.QCheckBox, 'chkMG_X')
        self.chkMagnetometer_Y = self.findChild(QtWidgets.QCheckBox, 'chkMG_Y')
        self.chkMagnetometer_Z = self.findChild(QtWidgets.QCheckBox, 'chkMG_Z')
        self.chkLight = self.findChild(QtWidgets.QCheckBox, 'chkLight')
        self.chkLimitView = self.findChild(QtWidgets.QCheckBox, 'chkLimitView')
        self.dsbLookBackSeconds = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbLookBackSeconds')
        self.btnSelectAll = self.findChild(QtWidgets.QPushButton, 'btnSelectAll')
        self.btnDeselectAll = self.findChild(QtWidgets.QPushButton, 'btnDeselectAll')
    

        #Initialize graph
        self.graph.setTitle("Smart Dot Sensor Data")
        self.graph.setLabel('left', 'Sensor Values', units='Units')
        self.graph.setLabel('bottom', 'Time', units='s')
        self.graph.setMouseEnabled(x=False, y=False)
        legend = self.graph.addLegend()
        legend.setColumnCount(3)


        #Select/Deselect All buttons
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnDeselectAll.clicked.connect(self.deselect_all)
    def select_all(self):
        self.chkAccelerometer_X.setChecked(True)
        self.chkAccelerometer_Y.setChecked(True)
        self.chkAccelerometer_Z.setChecked(True)
        self.chkGyroscope_X.setChecked(True)
        self.chkGyroscope_Y.setChecked(True)
        self.chkGyroscope_Z.setChecked(True)
        self.chkMagnetometer_X.setChecked(True)
        self.chkMagnetometer_Y.setChecked(True)
        self.chkMagnetometer_Z.setChecked(True)
        self.chkLight.setChecked(True)
    def deselect_all(self):
        self.chkAccelerometer_X.setChecked(False)
        self.chkAccelerometer_Y.setChecked(False)
        self.chkAccelerometer_Z.setChecked(False)
        self.chkGyroscope_X.setChecked(False)
        self.chkGyroscope_Y.setChecked(False)
        self.chkGyroscope_Z.setChecked(False)
        self.chkMagnetometer_X.setChecked(False)
        self.chkMagnetometer_Y.setChecked(False)
        self.chkMagnetometer_Z.setChecked(False)
        self.chkLight.setChecked(False)



    #expose UpdateData as a class method
 
    def updateDataBetter(self,
                        acclerometerTime, acclerometerX, accelerometerY, accelerometerZ,
                        gyroscoperTime, gyroscopeX, gyroscopeY, gyroscopeZ,
                        magnometerTime, 
                        magnetometerX, magnetometerY, magnetometerZ,
                        lightTime, lightValue):
        self.graph.clear()  # Clear existing plots
        # Plot data based on checkbox states
        if self.chkAccelerometer_X.isChecked():
            self.graph.plot(acclerometerTime, acclerometerX, pen=pg.mkPen(color='r', width=2), name='Accelerometer_X')
        if self.chkAccelerometer_Y.isChecked():
            self.graph.plot(acclerometerTime, accelerometerY, pen=pg.mkPen(color='g', width=2), name='Accelerometer_Y')
        if self.chkAccelerometer_Z.isChecked():
            self.graph.plot(acclerometerTime, accelerometerZ, pen=pg.mkPen(color='b', width=2), name='Accelerometer_Z')
        if self.chkGyroscope_X.isChecked():
            self.graph.plot(gyroscoperTime, gyroscopeX, pen=pg.mkPen(color='c', width=2), name='Gyroscope_X')
        if self.chkGyroscope_Y.isChecked():
            self.graph.plot(gyroscoperTime, gyroscopeY, pen=pg.mkPen(color='m', width=2), name='Gyroscope_Y')
        if self.chkGyroscope_Z.isChecked():
            self.graph.plot(gyroscoperTime, gyroscopeZ, pen=pg.mkPen(color='y', width=2), name='Gyroscope_Z')
        if self.chkMagnetometer_X.isChecked():
            self.graph.plot(magnometerTime, magnetometerX, pen=pg.mkPen(color="#008080", width=2), name='Magnetometer_X')
        if self.chkMagnetometer_Y.isChecked():
            self.graph.plot(magnometerTime, magnetometerY, pen=pg.mkPen(color="#800000", width=2), name='Magnetometer_Y')  # Orange
        if self.chkMagnetometer_Z.isChecked():
            self.graph.plot(magnometerTime, magnetometerZ, pen=pg.mkPen(color='#800080', width=2), name='Magnetometer_Z')  # Purple
        if self.chkLight.isChecked():
            self.graph.plot(lightTime, lightValue, pen=pg.mkPen(color='w', width=2), name='Light')  # Gray
        last = max(acclerometerTime[-1], gyroscoperTime[-1], magnometerTime[-1], lightTime[-1])
        if self.chkLimitView.isChecked():
            self.graph.setXRange(last - self.dsbLookBackSeconds.value(), last)
        else:
            self.graph.enableAutoRange(axis='x')
    def updateAccelerometer(self, time, x, y, z):
        if self.chkAccelerometer_X.isChecked():
            self.graph.plot(time, x, pen=pg.mkPen(color='r', width=2), name='Accelerometer_X')
        if self.chkAccelerometer_Y.isChecked():
            self.graph.plot(time, y, pen=pg.mkPen(color='g', width=2), name='Accelerometer_Y')
        if self.chkAccelerometer_Z.isChecked():
            self.graph.plot(time, z, pen=pg.mkPen(color='b', width=2), name='Accelerometer_Z')
        last = time[-1]
        if self.chkLimitView.isChecked():
            self.graph.setXRange(last - self.dsbLookBackSeconds.value(), last)
        else:
            self.graph.enableAutoRange(axis='x')
    def updateGyroscope(self, time, x, y, z):
        if self.chkGyroscope_X.isChecked():
            self.graph.plot(time, x, pen=pg.mkPen(color='c', width=2), name='Gyroscope_X')
        if self.chkGyroscope_Y.isChecked():
            self.graph.plot(time, y, pen=pg.mkPen(color='m', width=2), name='Gyroscope_Y')
        if self.chkGyroscope_Z.isChecked():
            self.graph.plot(time, z, pen=pg.mkPen(color='y', width=2), name='Gyroscope_Z')
        last = time[-1]
        if self.chkLimitView.isChecked():
            self.graph.setXRange(last - self.dsbLookBackSeconds.value(), last)
        else:
            self.graph.enableAutoRange(axis='x')
    def updateMagnetometer(self, time, x, y, z):
        if self.chkMagnetometer_X.isChecked():
            self.graph.plot(time, x, pen=pg.mkPen(color="#008080", width=2), name='Magnetometer_X')
        if self.chkMagnetometer_Y.isChecked():
            self.graph.plot(time, y, pen=pg.mkPen(color="#800000", width=2), name='Magnetometer_Y')
        if self.chkMagnetometer_Z.isChecked():
            self.graph.plot(time, z, pen=pg.mkPen(color='#800080', width=2), name='Magnetometer_Z')
        last = time[-1]
        if self.chkLimitView.isChecked():
            self.graph.setXRange(last - self.dsbLookBackSeconds.value(), last)
        else:
            self.graph.enableAutoRange(axis='x')
    def updateLight(self, time, value):
        if self.chkLight.isChecked():
            self.graph.plot(time, value, pen=pg.mkPen(color='w', width=2), name='Light')
        last = time[-1]
        if self.chkLimitView.isChecked():
            self.graph.setXRange(last - self.dsbLookBackSeconds.value(), last)
        else:
            self.graph.enableAutoRange(axis='x')
    def setMode(self, mode):
        match mode:
            case 'Accelerometer':
                self.chkAccelerometer_X.setVisible(True)
                self.chkAccelerometer_Y.setVisible(True)
                self.chkAccelerometer_Z.setVisible(True)
                self.chkGyroscope_X.setVisible(False)
                self.chkGyroscope_Y.setVisible(False)
                self.chkGyroscope_Z.setVisible(False)
                self.chkMagnetometer_X.setVisible(False)
                self.chkMagnetometer_Y.setVisible(False)
                self.chkMagnetometer_Z.setVisible(False)
                self.chkLight.setVisible(False)
                # uncheck all other checkboxes
                self.deselect_all()
            case 'Gyroscope':
                self.chkAccelerometer_X.setVisible(False)
                self.chkAccelerometer_Y.setVisible(False)
                self.chkAccelerometer_Z.setVisible(False)
                self.chkGyroscope_X.setVisible(True)
                self.chkGyroscope_Y.setVisible(True)
                self.chkGyroscope_Z.setVisible(True)
                self.chkMagnetometer_X.setVisible(False)
                self.chkMagnetometer_Y.setVisible(False)
                self.chkMagnetometer_Z.setVisible(False)
                self.chkLight.setVisible(False)
                # uncheck all other checkboxes
                self.deselect_all()
            case 'Magnetometer':
                self.chkAccelerometer_X.setVisible(False)
                self.chkAccelerometer_Y.setVisible(False)
                self.chkAccelerometer_Z.setVisible(False)
                self.chkGyroscope_X.setVisible(False)
                self.chkGyroscope_Y.setVisible(False)
                self.chkGyroscope_Z.setVisible(False)
                self.chkMagnetometer_X.setVisible(True)
                self.chkMagnetometer_Y.setVisible(True)
                self.chkMagnetometer_Z.setVisible(True)
                self.chkLight.setVisible(False)
                 # uncheck all other checkboxes
                self.deselect_all()
            case 'Light':
                self.chkAccelerometer_X.setVisible(False)
                self.chkAccelerometer_Y.setVisible(False)
                self.chkAccelerometer_Z.setVisible(False)
                self.chkGyroscope_X.setVisible(False)
                self.chkGyroscope_Y.setVisible(False)
                self.chkGyroscope_Z.setVisible(False)
                self.chkMagnetometer_X.setVisible(False)
                self.chkMagnetometer_Y.setVisible(False)
                self.chkMagnetometer_Z.setVisible(False)
                self.chkLight.setVisible(True)
                 # uncheck all other checkboxes
                self.deselect_all()
            case _:
                # Show all checkboxes
                self.chkAccelerometer_X.setVisible(True)
                self.chkAccelerometer_Y.setVisible(True)
                self.chkAccelerometer_Z.setVisible(True)
                self.chkGyroscope_X.setVisible(True)
                self.chkGyroscope_Y.setVisible(True)
                self.chkGyroscope_Z.setVisible(True)
                self.chkMagnetometer_X.setVisible(True)
                self.chkMagnetometer_Y.setVisible(True)
                self.chkMagnetometer_Z.setVisible(True)
                self.chkLight.setVisible(True)


if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = SmartDotGraph()
    window.setWindowTitle("Smart Dot Graph")
    window.show()

    window.setMode('Gyroscope')
    
    # Start the event loop
    sys.exit(app.exec())