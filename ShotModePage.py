from PyQt6 import QtWidgets, QtCore, uic
from InputGraph import InputGraph


class ShotModePage(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (name matches file in repo)
        uic.loadUi('ShotModePage.ui', self)

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

        self.graph_rpm.set_bounds(0,1,0,400)
        self.graph_tilt.set_bounds(0,1,-45,45)
        self.graph_angle.set_bounds(0,1,-90,90)

        self.graph_rpm.set_default_endpoints(0,0)
        self.graph_angle.set_default_endpoints(0,0)
        self.graph_tilt.set_default_endpoints(0,0)

        self.graph_rpm.set_max_points(3)
        self.graph_tilt.set_max_points(3)
        self.graph_angle.set_max_points(3)


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
        print("Shot started!")
        # Todo implement shot logic here based on graph settings and duration.
        print(self.graph_rpm.get_polynomial_display())
        print(self.graph_tilt.get_polynomial_display())
        print(self.graph_angle.get_polynomial_display())

    def update_shot_duration_label(self, value):
        # value comes from QSlider.value() (int)
        self.lblShotDuration.setText(f"Shot Duration: {1 + 0.02 * value:.2f} sec")
        self.graph_rpm.set_bounds(0,1 + 0.02 * value,0,400)
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
