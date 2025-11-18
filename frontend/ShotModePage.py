from PyQt6 import QtWidgets, QtCore, uic
import os
from .InputGraph import InputGraph
from PyQt6.QtCore import pyqtSignal

#Database related imports
from BSC import bsc
from backend.models.SessionData import SessionData
from backend.models.DataController import DataController
import datetime as dt


class ShotModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ShotModePage.ui'), self, package='frontend')

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



        self.sliderTime = self.findChild(QtWidgets.QSlider, 'sliderTime')
        self.lblShotDuration = self.findChild(QtWidgets.QLabel, 'lblShotDuration')

        self.sliderTime.setMaximum(100)  # set maximum to 100 for 1.00 sec max duration
        # connect slider change to label update if found and initialize label
        self.sliderTime.valueChanged.connect(self.update_shot_duration_label)
        self.update_shot_duration_label(self.sliderTime.value())

        # connect button to start shot action
        self.btnStartShot = self.findChild(QtWidgets.QPushButton, 'btnStartShot')
        self.btnStartShot.clicked.connect(self.start_shot)
    def start_shot(self):
        #When we start a shot, we need to create a new session data object and its associated data controller
        bsc.set_session(SessionData(id=-1, timeStamp=dt.datetime.now().isoformat(), name="Test Session", isShotMode=True))
        bsc.set_data_controller(DataController(bsc.get_session()))
        print(bsc.get_session())
        print(bsc.get_data_controller())

        print(self.graph_rpm.sample_spline_display(0.1))
        print(self.graph_tilt.sample_spline_display(0.1))
        print(self.graph_angle.sample_spline_display(0.1))

    def update_shot_duration_label(self, value):
        # value comes from QSlider.value() (int)
        self.lblShotDuration.setText(f"Shot Duration: {1 + 0.02 * value:.2f} sec")
        self.graph_rpm.set_bounds(0,1 + 0.02 * value,0,600)
        self.graph_tilt.set_bounds(0,1 + 0.02 * value,-45,45)
        self.graph_angle.set_bounds(0,1 + 0.02 * value,-90,90)
        


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    window = ShotModePage()
    window.setGeometry(100, 100, 800, 600)
    window.setWindowTitle("Shot Mode Page")
    window.show()
    sys.exit(app.exec())
