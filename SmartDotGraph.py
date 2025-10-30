from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np

# Module-level arrays used by the graph update. Kept as globals for minimal changes
arrayGeneralTime = np.array([0.0])
arrayAccelerometer_X = np.array([0.0])
arrayAccelerometer_Y = np.array([0.0])
arrayAccelerometer_Z = np.array([0.0])
arrayGyroscope_X = np.array([0.0])
arrayGyroscope_Y = np.array([0.0])
arrayGyroscope_Z = np.array([0.0])
arrayMagnetometer_X = np.array([0.0])
arrayMagnetometer_Y = np.array([0.0])
arrayMagnetometer_Z = np.array([0.0])
arrayLight = np.array([0.0])


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
        self.graph.setYRange(0,15)
        legend = self.graph.addLegend()
        legend.setColumnCount(3)
  
       
   
        # Connect checkbox state changes to update_graph method
        self.chkAccelerometer_X.stateChanged.connect(self.update_graph)
        self.chkAccelerometer_Y.stateChanged.connect(self.update_graph)
        self.chkAccelerometer_Z.stateChanged.connect(self.update_graph)
        self.chkGyroscope_X.stateChanged.connect(self.update_graph)
        self.chkGyroscope_Y.stateChanged.connect(self.update_graph)
        self.chkGyroscope_Z.stateChanged.connect(self.update_graph)
        self.chkMagnetometer_X.stateChanged.connect(self.update_graph)
        self.chkMagnetometer_Y.stateChanged.connect(self.update_graph)
        self.chkMagnetometer_Z.stateChanged.connect(self.update_graph)
        self.chkLight.stateChanged.connect(self.update_graph)
        self.update_graph()  # Initial graph update

        #Limit view checkbox
        self.chkLimitView.stateChanged.connect(self.toggle_limit_view)
        self.dsbLookBackSeconds.valueChanged.connect(self.toggle_limit_view)

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

    def toggle_limit_view(self):
        if self.chkLimitView.isChecked():
            self.graph.setXRange(arrayGeneralTime[-1]- self.dsbLookBackSeconds.value(), arrayGeneralTime[-1])
        else:
            self.graph.enableAutoRange(axis='x')
    def update_graph(self):
        self.graph.clear()  # Clear existing plots

        # Plot data based on checkbox states
        if self.chkAccelerometer_X.isChecked():
            self.graph.plot(arrayGeneralTime, arrayAccelerometer_X, pen=pg.mkPen(color='r', width=2), name='Accelerometer_X')
        if self.chkAccelerometer_Y.isChecked():
            self.graph.plot(arrayGeneralTime, arrayAccelerometer_Y, pen=pg.mkPen(color='g', width=2), name='Accelerometer_Y')
        if self.chkAccelerometer_Z.isChecked():
            self.graph.plot(arrayGeneralTime, arrayAccelerometer_Z, pen=pg.mkPen(color='b', width=2), name='Accelerometer_Z')
        if self.chkGyroscope_X.isChecked():
            self.graph.plot(arrayGeneralTime, arrayGyroscope_X, pen=pg.mkPen(color='c', width=2), name='Gyroscope_X')
        if self.chkGyroscope_Y.isChecked():
            self.graph.plot(arrayGeneralTime, arrayGyroscope_Y, pen=pg.mkPen(color='m', width=2), name='Gyroscope_Y')
        if self.chkGyroscope_Z.isChecked():
            self.graph.plot(arrayGeneralTime, arrayGyroscope_Z, pen=pg.mkPen(color='y', width=2), name='Gyroscope_Z')
        if self.chkMagnetometer_X.isChecked():
            self.graph.plot(arrayGeneralTime, arrayMagnetometer_X, pen=pg.mkPen(color="#008080", width=2), name='Magnetometer_X')
        if self.chkMagnetometer_Y.isChecked():
            self.graph.plot(arrayGeneralTime, arrayMagnetometer_Y, pen=pg.mkPen(color="#800000", width=2), name='Magnetometer_Y')  # Orange
        if self.chkMagnetometer_Z.isChecked():
            self.graph.plot(arrayGeneralTime, arrayMagnetometer_Z, pen=pg.mkPen(color='#800080', width=2), name='Magnetometer_Z')  # Purple
        if self.chkLight.isChecked():
            self.graph.plot(arrayGeneralTime, arrayLight, pen=pg.mkPen(color='w', width=2), name='Light')  # Gray
        self.toggle_limit_view()  # Apply limit view if enabled

    #expose UpdateData as a class method
    def UpdateData(self, timeArray, accelerometerX, accelerometerY, accelerometerZ,gyroscopeX, gyroscopeY, gyroscopeZ,magnetometerX, magnetometerY, magnetometerZ,lightArray):
        global arrayGeneralTime
        global arrayAccelerometer_X, arrayAccelerometer_Y, arrayAccelerometer_Z
        global arrayGyroscope_X, arrayGyroscope_Y, arrayGyroscope_Z
        global arrayMagnetometer_X, arrayMagnetometer_Y, arrayMagnetometer_Z
        global arrayLight

        arrayGeneralTime = timeArray
        arrayAccelerometer_X = accelerometerX
        arrayAccelerometer_Y = accelerometerY
        arrayAccelerometer_Z = accelerometerZ
        arrayGyroscope_X = gyroscopeX
        arrayGyroscope_Y = gyroscopeY
        arrayGyroscope_Z = gyroscopeZ
        arrayMagnetometer_X = magnetometerX
        arrayMagnetometer_Y = magnetometerY
        arrayMagnetometer_Z = magnetometerZ
        arrayLight = lightArray

        # Refresh the graph with new data
        # Use Qt's event loop to schedule the update if needed; direct call works for simple tests
        self.update_graph()



if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = SmartDotGraph()
    window.setWindowTitle("Smart Dot Graph")
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())