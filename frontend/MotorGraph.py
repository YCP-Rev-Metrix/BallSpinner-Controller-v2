from ctypes import cast
from unittest import case
from PyQt6 import QtWidgets, uic
import os
import pyqtgraph as pg
import numpy as np

# Module-level arrays used by the graph update. Kept as globals for minimal changes

class MotorGraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load the UI file.
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'MotorGraph.ui'), self, package='frontend')

        # Get references to UI elements
        self.graph = self.findChild(pg.PlotWidget, 'graphSmartDot')


        self.chkSpin = self.findChild(QtWidgets.QCheckBox, 'chkSpin')
        self.chkTilt = self.findChild(QtWidgets.QCheckBox, 'chkTilt')
        self.chkAngle = self.findChild(QtWidgets.QCheckBox, 'chkAngle')
        self.chkSpinData = self.findChild(QtWidgets.QCheckBox, 'chkSpinData')
        self.chkTiltData = self.findChild(QtWidgets.QCheckBox, 'chkTiltData')
        self.chkAngleData = self.findChild(QtWidgets.QCheckBox, 'chkAngleData')

        self.btnSelectAll = self.findChild(QtWidgets.QPushButton, 'btnSelectAll')
        self.btnDeselectAll = self.findChild(QtWidgets.QPushButton, 'btnDeselectAll')

        self.dsbLookBackSeconds = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbLookBackSeconds')
        self.cbolimitView = self.findChild(QtWidgets.QComboBox, 'cboLimitView')
        self.dsbMinXValue = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbMinX')
        self.dsbMaxXValue = self.findChild(QtWidgets.QDoubleSpinBox, 'dsbMaxX')
        self.lblXMax = self.findChild(QtWidgets.QLabel, 'lblXMax')
        self.lblXMin = self.findChild(QtWidgets.QLabel, 'lblXMin')

        self.cbolimitView.currentTextChanged.connect(self.limitViewBox)
        self.dsbMinXValue.valueChanged.connect(self.setRange)
        self.dsbMaxXValue.valueChanged.connect(self.setRange)
        self.dsbLookBackSeconds.valueChanged.connect(self.limitViewBox)
        # Hide limit view controls when not needed
        self.lblXMax.setVisible(False)
        self.lblXMin.setVisible(False)
        self.dsbLookBackSeconds.setVisible(False)
        self.dsbMinXValue.setVisible(False)
        self.dsbMaxXValue.setVisible(False)

        #Initialize graph
        self.graph.setTitle("Motor Data")
        self.graph.setLabel('left', 'Sensor Values', units='Units')
        self.graph.setLabel('bottom', 'Time', units='s')
        self.graph.setMouseEnabled(x=False, y=False)
        legend = self.graph.addLegend()
        legend.setColumnCount(3)

        # initalize storage for plot data
        self.MotorTime = np.array([0.0])
        self.SpinArray = np.array([0.0])
        self.TiltArray = np.array([0.0])
        self.AngleArray = np.array([0.0])

        self.DataTime = np.array([0.0])
        self.SpinDataArray = np.array([0.0])
        self.TiltDataArray = np.array([0.0])
        self.AngleDataArray = np.array([0.0])



        #Select/Deselect All buttons
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnDeselectAll.clicked.connect(self.deselect_all)
        # Print graph coordinates to terminal when user clicks on the graph
        # We map the scene position of the mouse click to the view (data) coordinates
        self.graph.scene().sigMouseClicked.connect(self._on_graph_click)

        # References to labels in the UI where we'll display the clicked values
        self.lblMotorData = self.findChild(QtWidgets.QLabel, 'lblMotorData')
        self.lblEncoderData = self.findChild(QtWidgets.QLabel, 'lblEncoderData')

        #connect checkbox changes to graph update
        self.chkSpin.stateChanged.connect(self.updateGraph)
        self.chkTilt.stateChanged.connect(self.updateGraph)
        self.chkAngle.stateChanged.connect(self.updateGraph)
        self.chkSpinData.stateChanged.connect(self.updateGraph)
        self.chkTiltData.stateChanged.connect(self.updateGraph)
        self.chkAngleData.stateChanged.connect(self.updateGraph)
        self.select_all()
        self.limitViewBox()

    def select_all(self):
        self.chkAngle.setChecked(True)
        self.chkTilt.setChecked(True)
        self.chkSpin.setChecked(True)
        self.chkAngleData.setChecked(True)
        self.chkTiltData.setChecked(True)
        self.chkSpinData.setChecked(True)
    def deselect_all(self):
        self.chkAngle.setChecked(False)
        self.chkTilt.setChecked(False)
        self.chkSpin.setChecked(False)
        self.chkAngleData.setChecked(False)
        self.chkTiltData.setChecked(False)
        self.chkSpinData.setChecked(False)
    #to change code outside of updateDataBetter
    def limitViewBox(self):
        try:
            last = max(self.MotorTime[-1], self.DataTime[-1])
        except Exception:
            last = 0
        match self.cbolimitView.currentText():
            case 'Scroll':
                self.lblXMax.setVisible(False)
                self.lblXMin.setVisible(False)
                self.dsbLookBackSeconds.setVisible(True)
                self.dsbMinXValue.setVisible(False)
                self.dsbMaxXValue.setVisible(False)
                self.graph.setXRange(last - self.dsbLookBackSeconds.value(), last)
            case 'View All':
                self.lblXMax.setVisible(False)
                self.lblXMin.setVisible(False)
                self.dsbLookBackSeconds.setVisible(False)
                self.dsbMinXValue.setVisible(False)
                self.dsbMaxXValue.setVisible(False)
                self.graph.enableAutoRange(axis='x')
            case "Range":
                self.lblXMax.setVisible(True)
                self.lblXMin.setVisible(True)
                self.dsbLookBackSeconds.setVisible(False)
                self.dsbMinXValue.setVisible(True)
                self.dsbMaxXValue.setVisible(True)
                self.graph.setXRange(self.dsbMinXValue.value(), self.dsbMaxXValue.value())
            case _:
                self.graph.enableAutoRange(axis='x')
    def setRange(self):
        self.graph.setXRange(self.dsbMinXValue.value(), self.dsbMaxXValue.value())

    def limit_view_change(self,last):
        match self.cbolimitView.currentText():
            case 'Scroll':
                self.graph.setXRange(last - self.dsbLookBackSeconds.value(), last)
            case 'View All':
                self.graph.enableAutoRange(axis='x')
            case "Range":
                self.graph.setXRange(self.dsbMinXValue.value(), self.dsbMaxXValue.value())
            case _:
                self.graph.enableAutoRange(axis='x')
    

    def _on_graph_click(self, event):
        """Handle mouse clicks on the plot scene and print mapped data coordinates.

        The event is a QGraphicsSceneMouseEvent. We convert the event's
        scene position into the view (data) coordinates using the plot's ViewBox.
        """
        try:
            # scenePos is in scene coordinates; map to view (data) coordinates
            pos = event.scenePos()
            vb = self.graph.getPlotItem().getViewBox()
            data_point = vb.mapSceneToView(pos)
            x_click = float(data_point.x())
            y_click = float(data_point.y())
            # Prepare formatting helper
            def _fmt(v):
                try:
                    return f"{float(v):.3f}"
                except Exception:
                    return "N/A"

            def _fmt_html(v, color):
                """Return an HTML span-wrapped formatted value using _fmt and a CSS color."""
                return f"<span style='color:{color}'>{_fmt(v)}</span>"

            # Helper to find nearest index
            def _nearest(time_arr, val):
                if time_arr is None or len(time_arr) == 0:
                    return None
                ta = np.asarray(time_arr)
                return int(np.argmin(np.abs(ta - val)))

            # Motor Data
            if self.MotorTime is not None and len(self.MotorTime) > 0:
                idx = _nearest(self.MotorTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.MotorTime)[idx])
                    spin = float(np.asarray(self.SpinArray)[idx]) if self.SpinArray is not None else None
                    tilt = float(np.asarray(self.TiltArray)[idx]) if self.TiltArray is not None else None
                    angle = float(np.asarray(self.AngleArray)[idx]) if self.AngleArray is not None else None
                    # Update label 
                    if self.lblMotorData is not None:
                        # colors match plotting pens: spin=red, tilt=green, angle=blue
                        spin_html = _fmt_html(spin, '#ff0000')
                        tilt_html = _fmt_html(tilt, '#00aa00')
                        angle_html = _fmt_html(angle, '#0000ff')
                        self.lblMotorData.setText(
                            f"Motor Data @ t={t:.3f} (idx={idx}): Spin={spin_html}, Tilt={tilt_html}, Angle={angle_html}"
                        )

            # Encoder Data
            if self.DataTime is not None and len(self.DataTime) > 0:
                idx = _nearest(self.DataTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.DataTime)[idx])
                    spin_data = float(np.asarray(self.SpinDataArray)[idx]) if self.SpinDataArray is not None else None
                    tilt_data = float(np.asarray(self.TiltDataArray)[idx]) if self.TiltDataArray is not None else None
                    angle_data = float(np.asarray(self.AngleDataArray)[idx]) if self.AngleDataArray is not None else None
                    # Update label 
                    if self.lblEncoderData is not None:
                        # colors match plotting pens: spin=red, tilt=green, angle=blue
                        spin_html = _fmt_html(spin_data, '#ff0000')
                        tilt_html = _fmt_html(tilt_data, '#00aa00')
                        angle_html = _fmt_html(angle_data, '#0000ff')
                        self.lblEncoderData.setText(
                            f"Encoder Data @ t={t:.3f} (idx={idx}): Spin={spin_html}, Tilt={tilt_html}, Angle={angle_html}"
                        )

        except Exception as e:
            # Fallback: print the exception to help debugging
            print("Error mapping graph click to data coords:", e)

 
    def updateDataBetter(self,MotorTime, SpinArray, TiltArray, AngleArray
                         ,DataTime, SpinDataArray, TiltDataArray, AngleDataArray):
        """Update the graph with new Smart Dot sensor data."""
        # Store data for click mapping
        self.MotorTime = MotorTime
        self.SpinArray = SpinArray
        self.TiltArray = TiltArray
        self.AngleArray = AngleArray

        self.DataTime = DataTime
        self.SpinDataArray = SpinDataArray
        self.TiltDataArray = TiltDataArray
        self.AngleDataArray = AngleDataArray

        # Plot data based on checkbox states
        self.updateGraph()

    def updateGraph(self):
        self.graph.clear()
        last = 0
        if self.chkSpin.isChecked():
            pen_spin = pg.mkPen(color=(255, 0, 0), width=2)  # Red pen for Spin
            self.graph.plot(self.MotorTime, self.SpinArray, pen=pen_spin, name="Spin")
        if self.chkTilt.isChecked():
            pen_tilt = pg.mkPen(color=(0, 170, 0), width=2)  # Green pen for Tilt
            self.graph.plot(self.MotorTime, self.TiltArray, pen=pen_tilt, name="Tilt")
        if self.chkAngle.isChecked():
            pen_angle = pg.mkPen(color=(0, 0, 255), width=2)  # Blue pen for Angle
            self.graph.plot(self.MotorTime, self.AngleArray, pen=pen_angle, name="Angle")
        if self.chkSpinData.isChecked():
            pen_spin_data = pg.mkPen(color=(255, 0, 0), width=1, style=pg.QtCore.Qt.PenStyle.DashLine)  # Red dashed pen for Spin Data
            self.graph.plot(self.DataTime, self.SpinDataArray, pen=pen_spin_data, name="Spin Data")
        if self.chkTiltData.isChecked():
            pen_tilt_data = pg.mkPen(color=(0, 170, 0), width=1, style=pg.QtCore.Qt.PenStyle.DashLine)  # Green dashed pen for Tilt Data
            self.graph.plot(self.DataTime, self.TiltDataArray, pen=pen_tilt_data, name="Tilt Data")
        if self.chkAngleData.isChecked():
            pen_angle_data = pg.mkPen(color=(0, 0, 255), width=1, style=pg.QtCore.Qt.PenStyle.DashLine)  # Blue dashed pen for Angle Data
            self.graph.plot(self.DataTime, self.AngleDataArray, pen=pen_angle_data, name="Angle Data")
        # Adjust view based on limit view setting
        last = max(self.MotorTime[-1], self.DataTime[-1])
        self.limit_view_change(last)

        
        
    

if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = MotorGraph()
    window.setWindowTitle("Motor Graph")
    window.show()

    #put in some sample data
    sampleTime = np.array([0,1,2,3,4,5,6,7,8,9,10])
    sampleSpin = np.array([0,100,200,300,400,500,600,500,400,300,200])
    sampleTilt = np.array([0,10,20,30,40,50,40,30,20,10,0])
    sampleAngle = np.array([0,-20,-40,-60,-80,-90,-80,-60,-40,-20,0])
    sampleSpinData = np.array([0,90,190,290,390,490,590,490,390,290,190])
    sampleTiltData = np.array([0,15,25,35,45,55,45,35,25,15,5])
    sampleAngleData = np.array([0,-25,-45,-65,-85,-95,-85,-65,-45,-25,5])

    window.updateDataBetter(sampleTime, sampleSpin, sampleTilt, sampleAngle,
                            sampleTime, sampleSpinData, sampleTiltData, sampleAngleData)

    # Start the event loop
    sys.exit(app.exec())