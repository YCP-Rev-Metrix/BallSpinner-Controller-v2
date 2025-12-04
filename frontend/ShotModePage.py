from PyQt6 import QtWidgets, QtCore, uic
import os

from .InputGraph import InputGraph
from PyQt6.QtCore import pyqtSignal
from backend.drivers.ShotScript import ShotScript
#from backend.motors.SimMotor import SimMotor
#from backend.motors.USBBDCMotor import USBBDCMotor
import time

#Database related imports
from BSC import bsc, MotorData
from backend.models.SessionData import SessionData
from backend.models.DataController import DataController
from frontend.SmartDotConnectWidget import SmartDotConnectWidget
from backend.models.ShotScriptData import ShotScriptDataInstance

import datetime as dt
from backend.smartdot.iSmartDot import iSmartDot



class ShotModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)
    # motor1 = USBBDCMotor() # first motor instantiation
    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ShotModePage.ui'), self, package='frontend')

        # Initialize shot script object with motors (currently sim, change to BSC motor reference or some motor object instantiated in BSC global class)
        '''sim_motor2 = SimMotor(2)
        sim_motor3 = SimMotor(3)
        self.shot_script = ShotScript(self.motor1, sim_motor2, sim_motor3)'''
        # Grab the three InputGraph widgets created by the .ui file and store references
        # The object names come from the .ui: 'inputGraph_RPM', 'InputGraph_Tilt', 'InputGraph_Angle'

        self.graph_rpm = self.findChild(InputGraph, 'inputGraph_RPM')
        self.graph_tilt = self.findChild(InputGraph, 'InputGraph_Tilt')
        self.graph_angle = self.findChild(InputGraph, 'InputGraph_Angle')

        self.graph_rpm.set_graph_title("RPM Input Graph")
        self.graph_tilt.set_graph_title("Tilt Input Graph")
        self.graph_angle.set_graph_title("Angle Input Graph")

        self.graph_rpm.hide_controls()
        self.graph_tilt.hide_controls()
        self.graph_angle.hide_controls()

        self.graph_rpm.set_bounds(0,1,0,600)
        self.graph_tilt.set_bounds(0,1,-45,45)
        self.graph_angle.set_bounds(0,1,-90,90)

        self.graph_rpm.set_default_endpoints(0,0,True)
        self.graph_angle.set_default_endpoints(0,0,True)
        self.graph_tilt.set_default_endpoints(0,0,True)

        self.graph_rpm.set_max_points(10)
        self.graph_tilt.set_max_points(3)
        self.graph_angle.set_max_points(3)

        self.graph_rpm.reset_view_and_clear()
        self.graph_tilt.reset_view_and_clear()
        self.graph_angle.reset_view_and_clear()

        self.graph_rpm.set_x_units("sec")
        self.graph_tilt.set_x_units("sec")
        self.graph_angle.set_x_units("sec")

        self.graph_rpm.set_y_units("RPM")
        self.graph_tilt.set_y_units("°")
        self.graph_angle.set_y_units("°")

        self.SmartDotConnectWidget = self.findChild(SmartDotConnectWidget, 'SmartDotConnectWidget')
        self.SmartDotConnectWidget.signalSmartDotConnected.connect(self.CheckButtons)


        self.sliderTime = self.findChild(QtWidgets.QSlider, 'sliderTime')
        self.lblShotDuration = self.findChild(QtWidgets.QLabel, 'lblShotDuration')

# Make the slider more touch-friendly: larger hit area, bigger handle,
# accept touch events, and coarser page steps so it's easier to move on
# a touchscreen.
        self.sliderTime.setMaximum(100)  # set maximum to 100 for 1.00 sec max duration
        self.sliderTime.setSingleStep(1)
        self.sliderTime.setPageStep(5)
        self.sliderTime.setTickInterval(5)
        self.sliderTime.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)

        # Increase the widget height so the groove + handle are easier to touch
        self.sliderTime.setFixedHeight(44)
        self.sliderTime.setTracking(True)
        self.sliderTime.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        
        # Larger handle and groove via stylesheet for better touch interaction
        self.sliderTime.setStyleSheet("""
QSlider::groove:horizontal { height: 14px; border-radius: 7px; background: #e6e6e6; }
QSlider::sub-page:horizontal { background: #66a3ff; border-radius: 7px; }
QSlider::add-page:horizontal { background: #e6e6e6; border-radius: 7px; }
QSlider::handle:horizontal { width: 34px; height: 34px; margin: -10px 0; border-radius: 17px; background: #4285F4; }
""")

        # connect slider change to label update if found and initialize label
        self.sliderTime.valueChanged.connect(self.update_shot_duration_label)
        self.update_shot_duration_label(self.sliderTime.value())

        # connect button to start shot action
        self.btnStartShot = self.findChild(QtWidgets.QPushButton, 'btnStartShot')
        self.CheckButtons()

        self.btnStartShot.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        self.btnStartShot.clicked.connect(self.start_shot)

    def start_shot(self):
        print("Shot started!")
        # Todo implement shot logic here based on graph settings and duration.
        print(self.graph_rpm.sample_spline_display(0.1))
        print(self.graph_tilt.sample_spline_display(0.1))
        print(self.graph_angle.sample_spline_display(0.1))
        # Assume we have some method or data structure to get the current motor values.
        # For this example, let's get hypothetical current values for each motor:
        '''all of the code below this comment in this function is experimental just for testing my script

        motor_rpm = self.graph_rpm.sample_spline_display(0.025)  # Get the RPM graph value(s)
        motor_tilt = self.graph_tilt.sample_spline_display(0.025)  # Get the Tilt graph value(s)
        motor_angle = self.graph_angle.sample_spline_display(0.025)  # Get the Angle graph value(s)
        runtime = 0
        '''
        # Call shot_script.start_motors before the while loop with the correct motor values
        # self.shot_script.start_motors([0, 1, 2])
        '''
        i = 0
        try:
            for Time in motor_rpm:
                # In the loop, set the speed of each motor to the motor value itself
                new_rpm = motor_rpm[i]
                new_tilt = motor_tilt[i]
                new_angle = motor_angle[i]
                
                self.shot_script.change_speed([new_rpm, new_tilt, new_angle])
                # To prevent freezing, typically you'd have a QEventLoop or sleep, omitted for brevity
                runtime += 0.025
                i += 1
                time.sleep(0.024)
            # After the while loop, call stop_motors
        finally:
            self.shot_script.stop_motors()'''
        #When we start a shot, we need to create a new session data object and its associated data controller
        bsc.set_session(SessionData(id=-1, timeStamp=dt.datetime.now().isoformat(), name="Shot Session", isShotMode=True))
        bsc.set_data_controller(DataController(bsc.get_session()))

        #Access the data controller's ShotModeData and add the three motors 
        sample_interval = 0.050 # 50 ms sample interval, 25 was too short
        rpm_array = self.graph_rpm.sample_spline_display(sample_interval)
        tilt_array = self.graph_tilt.sample_spline_display(sample_interval)
        angle_array = self.graph_angle.sample_spline_display(sample_interval)

        data_controller: DataController = bsc.get_data_controller()
        for i in range(0,len(rpm_array)):
            data_controller.add_shot_script_data(ShotScriptDataInstance(
                time=i*sample_interval,
                rpm=rpm_array[i],
                angleDeg=angle_array[i],
                tiltDeg=tilt_array[i]
            ))

        # print(bsc.get_session())
        print(bsc.get_data_controller())

        # print(self.graph_rpm.sample_spline_display(sample_interval))
        # print(self.graph_tilt.sample_spline_display(sample_interval))
        # print(self.graph_angle.sample_spline_display(sample_interval))

        self.GraphsData = MotorData(
            dt=sample_interval,
            length=1 + 0.02 * self.sliderTime.value(),
            spin=rpm_array,
            tilt=tilt_array,
            angle=angle_array
        )
        self.changePage.emit(6, self.GraphsData)

    def update_shot_duration_label(self, value):
        # value comes from QSlider.value() (int)
        self.lblShotDuration.setText(f"Shot Duration: {1 + 0.02 * value:.2f} sec")
        self.graph_rpm.set_bounds(0,1 + 0.02 * value,0,600)
        self.graph_tilt.set_bounds(0,1 + 0.02 * value,-45,45)
        self.graph_angle.set_bounds(0,1 + 0.02 * value,-90,90)

    def CheckButtons(self):
        if(bsc.smartdotConnectionManager.get_connections):
            self.btnStartShot.setEnabled(True)
            print("SmartDot connected, enabling Start Shot button.")
        else:
            self.btnStartShot.setEnabled(False)
            print("No SmartDot connected, disabling Start Shot button.")
        print("SmartDot list:",bsc.smartdotConnectionManager.get_connections())

    def reset(self):
        self.graph_rpm.reset_view_and_clear()
        self.graph_tilt.reset_view_and_clear()
        self.graph_angle.reset_view_and_clear()
        self.sliderTime.setValue(0)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    window = ShotModePage()
    window.setGeometry(100, 100, 800, 600)
    window.setWindowTitle("Shot Mode Page")
    window.show()
    sys.exit(app.exec())
