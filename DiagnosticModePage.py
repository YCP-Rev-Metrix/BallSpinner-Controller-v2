from PyQt6 import QtWidgets, uic
from backend.Motors.BDCMotor import BDCMotor
from backend.Motors.SimMotor import SimMotor
import pyqtgraph as pg
import numpy as np
import threading
import time
import os
import io
import utils
from PyQt6.QtCore import pyqtSignal


spinArray = np.array([0.0])
tiltArray = np.array([0.0])
angleArray = np.array([0.0])
xArray = np.array([0.0])


class DiagnosticModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        

        # check if pi, if not then run sim motor
        if utils.is_raspberry_pi():
            Motor = BDCMotor(26)
        else :
            Motor = SimMotor(26)

        # Load the UI file.
        uic.loadUi('DiagnosticModePage.ui', self)
        #Buttons
        btnStart = self.findChild(QtWidgets.QPushButton, 'btnStart')
        btnStop = self.findChild(QtWidgets.QPushButton, 'btnStop')
        btnClear = self.findChild(QtWidgets.QPushButton, 'btnClear')


        

        # Additional initialization code can go here
        spinGraph = self.findChild(pg.PlotWidget, 'graph1')
        tiltGraph = self.findChild(pg.PlotWidget, 'graph2')
        angleGraph = self.findChild(pg.PlotWidget, 'graph3')


        #Graph configurations

        #Spin Motor graph setup
        spinGraph.setTitle("Diagnostic Spin Graph")
        spinGraph.setLabel('left', 'Spin Rate', units='RPM')
        spinGraph.setLabel('bottom', 'Time', units='s')
        self.spinCurve = spinGraph.plot(xArray, spinArray, pen=pg.mkPen(color='b', width=2)) #Extra refrence allows to be manipulated in thread
        spinGraph.setYRange(0,620)
        spinGraph.setMouseEnabled(x=False, y=False)
        #Tilt Motor graph setup
        tiltGraph.setTitle("Diagnostic Tilt Graph")
        tiltGraph.setLabel('left', 'Tilt Angle', units='Degrees')
        tiltGraph.setLabel('bottom', 'Time', units='s')
        self.tiltCurve = tiltGraph.plot(xArray, tiltArray, pen=pg.mkPen(color='r', width=2)) #Extra refrence allows to be manipulated in thread
        tiltGraph.setYRange(0,100)
        tiltGraph.setMouseEnabled(x=False, y=False)
        #Angle Motor graph setup
        angleGraph.setTitle("Diagnostic Angle Graph")
        angleGraph.setLabel('left', 'Angle', units='Degrees')
        angleGraph.setLabel('bottom', 'Time', units='s')
        self.angleCurve = angleGraph.plot(xArray, angleArray, pen=pg.mkPen(color='g', width=2)) #Extra refrence allows to be manipulated in thread
        angleGraph.setYRange(0,50)
        angleGraph.setMouseEnabled(x=False, y=False)

        #Dial configurations
        self.spinDial = self.findChild(QtWidgets.QDial, 'dial')
        self.tiltDial = self.findChild(QtWidgets.QDial, 'dial_2')
        self.angleDial = self.findChild(QtWidgets.QDial, 'dial_3')
        
        # Simulate generating data in a separate thread
        
        # control flag: only update while active (set by HomePage)
        self.active = False

        btnStart.clicked.connect(lambda: toggle_Buttons())
        btnStop.clicked.connect(lambda: toggle_Buttons())
        btnClear.clicked.connect(lambda: clear_graphs())

        def toggle_Buttons():
            if not self.active:
                btnStart.setEnabled(False)
                btnStop.setEnabled(True)
                self.set_active(True)
            else:
                btnStart.setEnabled(True)
                btnStop.setEnabled(False)
                self.set_active(False)

        # public setter used by HomePage.on_tab_changed
        def set_active(v: bool):
            self.active = bool(v)
            if self.active: Motor.start()
            else : Motor.stop()
        self.set_active = set_active
        
        self._stop_event = threading.Event()

        def EStop():
            Motor.stop()
            clear_graphs()
            btnStart.setEnabled(True)
            btnStop.setEnabled(False)
            self.set_active(False)
        # expose EStop publicly so other modules can call: instance.EStop()
        self.EStop = EStop


        def _Generator():
            global spinArray, tiltArray, angleArray, xArray
            while not self._stop_event.is_set():

                # only update while the diagnostic tab/widget is active
                if not self.active:
                    time.sleep(0.25)
                    continue

                spinArray= np.append(spinArray, 600* 0.01 * self.spinDial.value()) #max rpm 400
                tiltArray= np.append(tiltArray, 90* 0.01*self.tiltDial.value()) #max tilt 90 degrees
                angleArray= np.append(angleArray,  45* 0.01 *self.angleDial.value()) #`max angle 45 degrees`
                xArray= np.append(xArray, xArray[-1]+0.25)

                Motor.changeSpeed(spinArray[-1])
                spinGraph.setXRange(max(0, xArray[-1]-3), xArray[-1])
                tiltGraph.setXRange(max(0, xArray[-1]-3), xArray[-1])
                angleGraph.setXRange(max(0, xArray[-1]-3), xArray[-1])

                # update the plotted curves
                self.spinCurve.setData(xArray, spinArray)
                self.tiltCurve.setData(xArray, tiltArray)
                self.angleCurve.setData(xArray, angleArray)

                time.sleep(0.25) # 4x a second
        def clear_graphs():
            global spinArray, tiltArray, angleArray, xArray
            spinArray = np.array([0.0])
            tiltArray = np.array([0.0])
            angleArray = np.array([0.0])
            xArray = np.array([0.0])
            self.spinCurve.setData(xArray, spinArray)
            self.tiltCurve.setData(xArray, tiltArray)
            self.angleCurve.setData(xArray, angleArray)

        t = threading.Thread(target=_Generator, daemon=True)
        t.start()




if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = DiagnosticModePage()
    window.setWindowTitle("Diagnostic Mode Page")
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())