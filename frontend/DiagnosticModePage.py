from PyQt6 import QtWidgets, uic
#from backend.motors.USBBDCMotor import USBBDCMotor
#from backend.motors.SimMotor import SimMotor
from backend.drivers.DiagnosticScript import DiagnosticScript
import pyqtgraph as pg
import numpy as np
import threading
import time
import os
import io
import utils
from array import array
from PyQt6.QtCore import pyqtSignal

#Database related imports
from BSC import bsc
from backend.models.SessionData import SessionData
from backend.models.DataController import DataController
from backend.models.DiagnosticScriptData import DiagnosticScriptDataInstance

import datetime as dt


spinArray = array('f', [0.0])
tiltArray = array('f', [0.0])
angleArray = array('f', [0.0])

#X is the time array
timeArray = array('d', [0.0])


class DiagnosticModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        

        # Check if pi, if not then run sim motor
        '''commenting out motor stuff to test diagnostic
        if utils.is_raspberry_pi():
            Motor = BDCMotor(26)
        else :
            Motor = SimMotor(26)
            '''

        # Load the UI file (module-relative path).
        import os
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'DiagnosticModePage.ui'), self, package='frontend')

        # Initialize diagnostic script object with fake motors (switch when BSC object works)
        '''motor1 = USBBDCMotor()
        sim_motor2 = SimMotor(2)
        sim_motor3 = SimMotor(3)'''
        self.diagnostic_script = DiagnosticScript(bsc.motor1, bsc.motor2, bsc.motor3)
        self.diagnostic_script.start_motors([1,2,3])

        #Buttons
        btnStart = self.findChild(QtWidgets.QPushButton, 'btnStart')
        btnStop = self.findChild(QtWidgets.QPushButton, 'btnStop')
        btnClear = self.findChild(QtWidgets.QPushButton, 'btnClear')

        # Additional initialization code can go here
        spinGraph = self.findChild(pg.PlotWidget, 'graph1')
        tiltGraph = self.findChild(pg.PlotWidget, 'graph2')
        angleGraph = self.findChild(pg.PlotWidget, 'graph3')

        #label configurations
        labelSpin = self.findChild(QtWidgets.QLabel, 'lblSpin')
        labelTilt = self.findChild(QtWidgets.QLabel, 'lblTilt')
        labelAngle = self.findChild(QtWidgets.QLabel, 'lblAngle')


        #Graph configurations

        #Spin Motor graph setup
        spinGraph.setTitle("Diagnostic Spin Graph")
        spinGraph.setLabel('left', 'Spin Rate', units='RPM')
        spinGraph.setLabel('bottom', 'Time', units='s')
        self.spinCurve = spinGraph.plot(timeArray, spinArray, pen=pg.mkPen(color='b', width=2)) #Extra refrence allows to be manipulated in thread
        spinGraph.setYRange(0,620)
        spinGraph.setMouseEnabled(x=False, y=False)
        #Tilt Motor graph setup
        tiltGraph.setTitle("Diagnostic Tilt Graph")
        tiltGraph.setLabel('left', 'Tilt Angle', units='Degrees')
        tiltGraph.setLabel('bottom', 'Time', units='s')
        self.tiltCurve = tiltGraph.plot(timeArray, tiltArray, pen=pg.mkPen(color='r', width=2)) #Extra refrence allows to be manipulated in thread
        tiltGraph.setYRange(-100,100)
        tiltGraph.setMouseEnabled(x=False, y=False)
        #Angle Motor graph setup
        angleGraph.setTitle("Diagnostic Angle Graph")
        angleGraph.setLabel('left', 'Angle', units='Degrees')
        angleGraph.setLabel('bottom', 'Time', units='s')
        self.angleCurve = angleGraph.plot(timeArray, angleArray, pen=pg.mkPen(color='g', width=2)) #Extra refrence allows to be manipulated in thread
        angleGraph.setYRange(-50,50)
        angleGraph.setMouseEnabled(x=False, y=False)

        #Dial configurations
        self.spinDial = self.findChild(QtWidgets.QDial, 'dial')
        self.tiltDial = self.findChild(QtWidgets.QDial, 'dial_2')
        self.angleDial = self.findChild(QtWidgets.QDial, 'dial_3')
        self.spinDial.setRange(0, 600)  # Set dial range from 0 to 600
        self.tiltDial.setRange(-90, 90)  # Set dial range from -90 to 90
        self.angleDial.setRange(-45, 45)  # Set dial range from -45 to 45

        
        # control flag: only update while active (set by BSCMainWindow)
        self.active = False

        btnStart.clicked.connect(lambda: toggle_Buttons())
        btnStop.clicked.connect(lambda: toggle_Buttons())
        btnClear.clicked.connect(lambda: clear_graphs())

        def toggle_Buttons():
            if not self.active:
                #This is the start function
                btnStart.setEnabled(False)
                btnStop.setEnabled(True)
                self.set_active(True)
                self.diagnostic_script.start_motors([1,2,3])

                #Initialize the Session
                bsc.set_session(SessionData(id=-1, timeStamp=dt.datetime.now().isoformat(), name="Diagnostic Session", isShotMode=False))
                bsc.set_data_controller(DataController(bsc.get_session()))
            else:
                #This is the stop function
                btnStart.setEnabled(True)
                btnStop.setEnabled(False)
                self.set_active(False)
                self.diagnostic_script.stop_motors([1,2,3])


        # public setter used by BSCMainWindow.on_tab_changed
        def set_active(v: bool):
            self.active = bool(v)
            # if self.active: #Motor.start() UNCOMMENT WHEN MOTOR WORKING AGAIN
            #This is Brandon. I moved stuff to toggle_buttons instead. You might want to use your motorstart in there instead of here

                
          
        self.set_active = set_active
        
        self._stop_event = threading.Event()

        def EStop():
            #Motor.stop() uncomment when motor works
            self.diagnostic_script.stop_motors([1,2,3])
            clear_graphs()
            btnStart.setEnabled(True)
            btnStop.setEnabled(False)
            self.set_active(False)
        # expose EStop publicly so other modules can call: instance.EStop()
        self.EStop = EStop

        def reset(self):
            self.active = False
            clear_graphs()
            self.spinDial.setValue(0)
            self.tiltDial.setValue(0)
            self.angleDial.setValue(0)
        def add_diag_data_instance_to_data_controller(time: float, motor_id: int, instruction: float):
            dc: DataController = bsc.get_data_controller()
            data = DiagnosticScriptDataInstance(
                time=time,
                motor_id=motor_id,
                instruction=instruction
            )
            dc.add_diagnostic_script_data(data)

        def _Generator():
            #timeArray is the time array
            global spinArray, tiltArray, angleArray, timeArray
            while not self._stop_event.is_set():

                # only update while the diagnostic tab/widget is active
                if not self.active:
                    time.sleep(0.25)
                    continue

                spinArray.append(self.spinDial.value()) #max rpm 400
                tiltArray.append(self.tiltDial.value()) #max tilt 90 degrees
                angleArray.append(self.angleDial.value()) #`max angle 45 degrees`
                timeArray.append(timeArray[-1]+0.25)
                #use labels to show current values
                labelSpin.setText(f"Spin Rate: {self.spinDial.value():.2f} RPM")
                labelTilt.setText(f"Tilt Angle: {self.tiltDial.value():.2f} Degrees")
                labelAngle.setText(f"Angle: {self.angleDial.value():.2f} Degrees")

                #These if statements add changes in motor values to the Diagnostic Script and DataController.
                self.diagnostic_script.change_speed(0, spinArray[-1])
                if(spinArray[-1]!=spinArray[-2]):
                    add_diag_data_instance_to_data_controller(timeArray[-1], 0, spinArray[-1])
                if(tiltArray[-1]!=tiltArray[-2]):
                    add_diag_data_instance_to_data_controller(timeArray[-1], 1, tiltArray[-1])
                    self.diagnostic_script.change_speed(1, tiltArray[-1])
                if(angleArray[-1]!=angleArray[-2]):
                    add_diag_data_instance_to_data_controller(timeArray[-1], 2, angleArray[-1])
                    self.diagnostic_script.change_speed(2, angleArray[-1])
                    

                spinGraph.setXRange(max(0, timeArray[-1]-3), timeArray[-1])
                tiltGraph.setXRange(max(0, timeArray[-1]-3), timeArray[-1])
                angleGraph.setXRange(max(0, timeArray[-1]-3), timeArray[-1])

                # update the plotted curves
                # convert to numpy arrays for plotting API
                # plotting API accepts array.array directly
                self.spinCurve.setData(timeArray, spinArray)
                self.tiltCurve.setData(timeArray, tiltArray)
                self.angleCurve.setData(timeArray, angleArray)

                time.sleep(0.05) # 20x a second
        def clear_graphs():
            global spinArray, tiltArray, angleArray, timeArray
            spinArray = array('f', [0.0])
            tiltArray = array('f', [0.0])
            angleArray = array('f', [0.0])
            timeArray = array('d', [0.0])
            self.spinCurve.setData(timeArray, spinArray)
            self.tiltCurve.setData(timeArray, tiltArray)
            self.angleCurve.setData(timeArray, angleArray)

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