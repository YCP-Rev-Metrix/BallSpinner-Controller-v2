from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import numpy as numpy


arrayAccelerometer_X = numpy.array([1,1,1,1,1,1,1,1,1,1])
arrayAccelerometer_Y = numpy.array([2,2,2,2,2,2,2,2,2,2])
arrayAccelerometer_Z = numpy.array([3,3,3,3,3,3,3,3,3,3])

arrayGyroscope_X = numpy.array([4,4,4,4,4,4,4,4,4,4])
arrayGyroscope_Y = numpy.array([5,5,5,5,5,5,5,5,5,5])
arrayGyroscope_Z = numpy.array([6,6,6,6,6,6,6,6,6,6])

arrayMagnetometer_X = numpy.array([7,7,7,7,7,7,7,7,7,7])
arrayMagnetometer_Y = numpy.array([8,8,8,8,8,8,8,8,8,8])
arrayMagnetometer_Z = numpy.array([9,9,9,9,9,9,9,9,9,9])

arrayLight = numpy.array([10,10,10,10,10,10,10,10,10,10])

arrayGeneralTime = numpy.array([0,1,2,3,4,5,6,7,8,9])


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
    

        #Initialize graph
        self.graph.setTitle("Smart Dot Sensor Data")
        self.graph.setLabel('left', 'Sensor Values', units='Units')
        self.graph.setLabel('bottom', 'Time', units='s')
        self.graph.setMouseEnabled(x=False, y=False)
        self.graph.setYRange(0,15)
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
            self.graph.plot(arrayGeneralTime, arrayMagnetometer_X, pen=pg.mkPen(color='w', width=2), name='Magnetometer_X')
        if self.chkMagnetometer_Y.isChecked():
            self.graph.plot(arrayGeneralTime, arrayMagnetometer_Y, pen=pg.mkPen(color='#FFA500', width=2), name='Magnetometer_Y')  # Orange
        if self.chkMagnetometer_Z.isChecked():
            self.graph.plot(arrayGeneralTime, arrayMagnetometer_Z, pen=pg.mkPen(color='#800080', width=2), name='Magnetometer_Z')  # Purple
        if self.chkLight.isChecked():
            self.graph.plot(arrayGeneralTime, arrayLight, pen=pg.mkPen(color='#808080', width=2), name='Light')  # Gray
#I didnt need to right this myself but its here now            


if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = SmartDotGraph()
    window.setWindowTitle("Diagnostic Mode Page")
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())