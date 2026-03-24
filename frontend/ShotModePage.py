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
from utils import notify_user



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

        self.graph_rpm = self.findChild(InputGraph, 'grphInputRpm')
        self.graph_tilt = self.findChild(InputGraph, 'grphInputTilt')
        self.graph_angle = self.findChild(InputGraph, 'grphInputAngle')

        # Configure RPM graph
        self.graph_rpm.set_graph_title("RPM Input Graph")
        self.graph_rpm.hide_controls()
        self.graph_rpm.set_bounds(0,1,0,600)
        self.graph_rpm.set_default_endpoints(0,0,True)
        self.graph_rpm.set_max_points(10)
        self.graph_rpm.reset_view_and_clear()
        self.graph_rpm.set_x_units("sec")
        self.graph_rpm.set_y_units("RPM")
        self.graph_rpm.setStepSize(10)  # Set step size to 10 RPM for easier snapping to increments of 10

        # Configure Tilt graph
        self.graph_tilt.set_graph_title("Tilt Input Graph")
        self.graph_tilt.hide_controls()
        self.graph_tilt.set_bounds(0,1,-45,45)
        self.graph_tilt.set_default_endpoints(0,0,True)
        self.graph_tilt.set_max_points(3)
        self.graph_tilt.reset_view_and_clear()
        self.graph_tilt.set_x_units("sec")
        self.graph_tilt.set_y_units("°")
        self.graph_tilt.setStepSize(0.5)  # Set step size to 0.5 degrees for easier snapping to increments of 0.5
        # Configure Angle graph
        self.graph_angle.set_graph_title("Angle Input Graph")
        self.graph_angle.hide_controls()
        self.graph_angle.set_bounds(0,1,-90,90)
        self.graph_angle.set_default_endpoints(0,0,True)
        self.graph_angle.set_max_points(3)
        self.graph_angle.reset_view_and_clear()
        self.graph_angle.set_x_units("sec")
        self.graph_angle.set_y_units("°")
        self.graph_angle.setStepSize(1)  # Set step size to 1 degrees for easier snapping to increments of 1

        self.SmartDotConnectWidget = self.findChild(SmartDotConnectWidget, 'wgtSmartDotConnect')
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
        # Use minimum height instead of fixed to allow scaling with parent container
        self.sliderTime.setMinimumHeight(44)
        self.sliderTime.setTracking(True)
        self.sliderTime.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        
        # Slider visual styling handled in QSS

        # connect slider change to label update if found and initialize label
        self.sliderTime.valueChanged.connect(self.update_shot_duration_label)
        self.update_shot_duration_label(self.sliderTime.value())

        # connect button to start shot action
        self.btnStartShot = self.findChild(QtWidgets.QPushButton, 'btnStartShot')
        self.CheckButtons()
        self.btnStartShot.clicked.connect(self.start_shot)

    def start_shot(self):
        print("Shot started!")
        #When we start a shot, we need to create a new session data object and its associated data controller
        bsc.set_session(
            SessionData(
                id=-1,
                timeStamp=dt.datetime.now().isoformat(), 
                name="Shot Session", 
                isShotMode=True, 
                Spin_Instruction_Points=self.graph_rpm.get_current_points(), 
                Angle_Instruction_Points=self.graph_angle.get_current_points(), 
                Tilt_Instruction_Points=self.graph_tilt.get_current_points()
                )
        )
        bsc.set_data_controller(DataController(bsc.get_session()))
        print(f"Debug: {bsc.get_session().Spin_Instruction_Points}")  # Debug print to verify session data is set correctly

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
        self.session = bsc.get_session()
        self.graph_rpm.reset_view_and_clear()
        self.graph_tilt.reset_view_and_clear()
        self.graph_angle.reset_view_and_clear()
        self.sliderTime.setValue(0)
        if self.session is None:
            print("No session found in BSC when resetting ShotModePage.")
            return
        if self.session.id != -1:
            spinPoints = self.session.get_spin_instruction_points()
            anglePoints = self.session.get_angle_instruction_points()
            tiltPoints = self.session.get_tilt_instruction_points()
            if spinPoints == [] or anglePoints == [] or tiltPoints == []:
                notify_user("Failed to load session instruction points, shot can not be edited.")
                return
            self.graph_rpm.set_current_points(self.session.get_spin_instruction_points())
            self.graph_tilt.set_current_points(self.session.get_tilt_instruction_points())
            self.graph_angle.set_current_points(self.session.get_angle_instruction_points())
            #Print the points for debugging
            print("RPM points:", self.session.Spin_Instruction_Points)
            print("Tilt points:", self.session.Tilt_Instruction_Points)
            print("Angle points:", self.session.Angle_Instruction_Points)

            # Use the time of the last shot script data entry as the final time.
            # Guard against empty shot script data so we don't crash on [-1].
            self.motorData = bsc.get_data_controller().get_shot_script_data() or []
            if self.motorData:
                self.FinalTime = self.motorData[-1].get_time()
            else:
                self.FinalTime = 0.0

            # Convert final time back to slider units (duration = 1 + 0.02 * slider_value)
            if self.FinalTime <= 1.0:
                slider_value = 0
            else:
                slider_value = round((self.FinalTime - 1.0) / 0.02)

            # clamp to slider valid range
            slider_value = max(0, min(self.sliderTime.maximum(), slider_value))
            self.sliderTime.setValue(slider_value)

        

            
       


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    window = ShotModePage()
    window.setGeometry(100, 100, 800, 600)
    window.setWindowTitle("Shot Mode Page")
    window.show()
    sys.exit(app.exec())
