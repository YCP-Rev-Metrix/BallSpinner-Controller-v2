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
        self.SpinTime = np.array([0.0])
        self.TiltTime = np.array([0.0])
        self.AngleTime = np.array([0.0])
        self.SpinArray = np.array([0.0])
        self.TiltArray = np.array([0.0])
        self.AngleArray = np.array([0.0])

        self.DataTime = np.array([0.0])
        self.SpinDataArray = np.array([0.0])
        self.TiltDataArray = np.array([0.0])
        self.AngleDataArray = np.array([0.0])

        # motor time (single reference for motor series) used for click mapping
        self.MotorTime = np.array([0.0])

        # Cursor and markers will be created on first click (lazy)

        # Cursor and markers will be created on first click (lazy)
        self.vline = None
        self.marker_spin = None
        self.marker_tilt = None
        self.marker_angle = None
        self.marker_spin_data = None
        self.marker_tilt_data = None
        self.marker_angle_data = None

        #Select/Deselect All buttons
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnDeselectAll.clicked.connect(self.deselect_all)
        # #print graph coordinates to terminal when user clicks on the graph
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
            last = max(self.SpinTime[-1], self.TiltTime[-1], self.AngleTime[-1], self.DataTime[-1])
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
        """Handle mouse clicks on the plot scene and #print mapped data coordinates.

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

            # Motor Data - use SpinTime as canonical motor-time reference
            if self.SpinTime is not None and len(self.SpinTime) > 0:
                idx = _nearest(self.SpinTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.SpinTime)[idx])
                    spin = float(np.asarray(self.SpinArray)[idx]) if (self.SpinArray is not None and len(self.SpinArray) > idx) else None
                    tilt = float(np.asarray(self.TiltArray)[idx]) if (self.TiltArray is not None and len(self.TiltArray) > idx) else None
                    angle = float(np.asarray(self.AngleArray)[idx]) if (self.AngleArray is not None and len(self.AngleArray) > idx) else None
                    # Update label 
                    if self.lblMotorData is not None:
                        # colors match plotting pens: spin=red, tilt=green, angle=blue
                        spin_html = _fmt_html(spin, '#ff0000')
                        tilt_html = _fmt_html(tilt, '#00aa00')
                        angle_html = _fmt_html(angle, '#0000ff')
                        self.lblMotorData.setText(
                            f"Motor Data @ t={t:.3f} (idx={idx}): Spin={spin_html}, Tilt={tilt_html}, Angle={angle_html}"
                        )
                    # move vertical cursor to the exact clicked x coordinate
                    # create vline on first click if needed, then position it at exact clicked x
                    try:
                        if self.vline is None:
                            self.vline = pg.InfiniteLine(
                                angle=90,
                                movable=False,
                                pen=pg.mkPen(color=(255,0,255), width=1, style=pg.QtCore.Qt.PenStyle.DotLine)
                            )
                            self.vline.setZValue(1000)
                            try:
                                vb.addItem(self.vline)
                            except Exception:
                                try:
                                    self.graph.addItem(self.vline, ignoreBounds=True)
                                except Exception:
                                    pass
                        else:
                            self.vline.setPos(x_click)
                        # ensure cursor is set to exact click
                        self.vline.setPos(x_click)
                    except Exception:
                        pass
                    # create markers on first click if needed, then set their positions (snap to nearest t)
                    try:
                        plotItem = self.graph.getPlotItem()
                        if self.marker_spin is None:
                            self.marker_spin = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255,0,0), pen=pg.mkPen(None))
                            self.marker_spin.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_spin)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_spin)
                                except Exception:
                                    pass
                        if self.marker_tilt is None:
                            self.marker_tilt = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(0,170,0), pen=pg.mkPen(None))
                            self.marker_tilt.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_tilt)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_tilt)
                                except Exception:
                                    pass
                        if self.marker_angle is None:
                            self.marker_angle = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(0,0,255), pen=pg.mkPen(None))
                            self.marker_angle.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_angle)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_angle)
                                except Exception:
                                    pass

                        if spin is not None:
                            self.marker_spin.setData(x=[t], y=[spin])
                        else:
                            self.marker_spin.setData(x=[], y=[])
                        if tilt is not None:
                            self.marker_tilt.setData(x=[t], y=[tilt])
                        else:
                            self.marker_tilt.setData(x=[], y=[])
                        if angle is not None:
                            self.marker_angle.setData(x=[t], y=[angle])
                        else:
                            self.marker_angle.setData(x=[], y=[])
                    except Exception:
                        pass

            # Encoder Data
            if self.DataTime is not None and len(self.DataTime) > 0:
                idx = _nearest(self.DataTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.DataTime)[idx])
                    spin_data = float(np.asarray(self.SpinDataArray)[idx]) if (self.SpinDataArray is not None and len(self.SpinDataArray) > idx) else None
                    tilt_data = float(np.asarray(self.TiltDataArray)[idx]) if (self.TiltDataArray is not None and len(self.TiltDataArray) > idx) else None
                    angle_data = float(np.asarray(self.AngleDataArray)[idx]) if (self.AngleDataArray is not None and len(self.AngleDataArray) > idx) else None
                    # Update label 
                    if self.lblEncoderData is not None:
                        # colors match plotting pens: spin=red, tilt=green, angle=blue
                        spin_html = _fmt_html(spin_data, '#ff0000')
                        tilt_html = _fmt_html(tilt_data, '#00aa00')
                        angle_html = _fmt_html(angle_data, '#0000ff')
                        self.lblEncoderData.setText(
                            f"Encoder Data @ t={t:.3f} (idx={idx}): Spin={spin_html}, Tilt={tilt_html}, Angle={angle_html}"
                        )
                    # place data-series markers at the data-time location
                    try:
                        # if motor cursor wasn't placed above, snap it to this data time
                        try:
                            # ensure vline exists and set to exact clicked x
                            if self.vline is None:
                                self.vline = pg.InfiniteLine(
                                    angle=90,
                                    movable=False,
                                    pen=pg.mkPen(color=(255,0,255), width=1, style=pg.QtCore.Qt.PenStyle.DotLine)
                                )
                                self.vline.setZValue(1000)
                                try:
                                    vb.addItem(self.vline)
                                except Exception:
                                    try:
                                        self.graph.addItem(self.vline, ignoreBounds=True)
                                    except Exception:
                                        pass
                            self.vline.setPos(x_click)

                            plotItem = self.graph.getPlotItem()
                            if self.marker_spin_data is None:
                                self.marker_spin_data = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,0,0), pen=pg.mkPen(None))
                                self.marker_spin_data.setZValue(200)
                                try:
                                    plotItem.addItem(self.marker_spin_data)
                                except Exception:
                                    try:
                                        self.graph.addItem(self.marker_spin_data)
                                    except Exception:
                                        pass
                            if self.marker_tilt_data is None:
                                self.marker_tilt_data = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(0,170,0), pen=pg.mkPen(None))
                                self.marker_tilt_data.setZValue(200)
                                try:
                                    plotItem.addItem(self.marker_tilt_data)
                                except Exception:
                                    try:
                                        self.graph.addItem(self.marker_tilt_data)
                                    except Exception:
                                        pass
                            if self.marker_angle_data is None:
                                self.marker_angle_data = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(0,0,255), pen=pg.mkPen(None))
                                self.marker_angle_data.setZValue(200)
                                try:
                                    plotItem.addItem(self.marker_angle_data)
                                except Exception:
                                    try:
                                        self.graph.addItem(self.marker_angle_data)
                                    except Exception:
                                        pass

                            if spin_data is not None:
                                self.marker_spin_data.setData(x=[t], y=[spin_data])
                            else:
                                self.marker_spin_data.setData(x=[], y=[])
                            if tilt_data is not None:
                                self.marker_tilt_data.setData(x=[t], y=[tilt_data])
                            else:
                                self.marker_tilt_data.setData(x=[], y=[])
                            if angle_data is not None:
                                self.marker_angle_data.setData(x=[t], y=[angle_data])
                            else:
                                self.marker_angle_data.setData(x=[], y=[])
                        except Exception:
                            pass
                    except Exception:
                        pass

        except Exception as e:
            # Fallback: #print the exception to help debugging
            #print("Error mapping graph click to data coords:", e)

 
    def updateDataBetter(self,MotorTime, SpinArray, TiltArray, AngleArray
                         ,DataTime, SpinDataArray, TiltDataArray, AngleDataArray):
        """Update the graph with new Smart Dot sensor data."""
        # Store data for click mapping
        self.SpinTime = MotorTime
        self.TiltTime = MotorTime
        self.AngleTime = MotorTime
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
            self.graph.plot(self.SpinTime, self.SpinArray, pen=pen_spin, name="Spin")
        if self.chkTilt.isChecked():
            pen_tilt = pg.mkPen(color=(0, 170, 0), width=2)  # Green pen for Tilt
            self.graph.plot(self.TiltTime, self.TiltArray, pen=pen_tilt, name="Tilt")
        if self.chkAngle.isChecked():
            pen_angle = pg.mkPen(color=(0, 0, 255), width=2)  # Blue pen for Angle
            self.graph.plot(self.AngleTime, self.AngleArray, pen=pen_angle, name="Angle")
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
        last = max(self.SpinTime[-1], self.TiltTime[-1], self.AngleTime[-1], self.DataTime[-1])
        self.limit_view_change(last)
        # Re-add cursor and markers so they persist after clear()
        try:
            vb = self.graph.getPlotItem().getViewBox()
            plotItem = self.graph.getPlotItem()
            if self.vline is not None:
                try:
                    vb.addItem(self.vline)
                except Exception:
                    try:
                        self.graph.addItem(self.vline, ignoreBounds=True)
                    except Exception:
                        pass
            if self.marker_spin is not None:
                try:
                    plotItem.addItem(self.marker_spin)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_spin)
                    except Exception:
                        pass
            if self.marker_tilt is not None:
                try:
                    plotItem.addItem(self.marker_tilt)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_tilt)
                    except Exception:
                        pass
            if self.marker_angle is not None:
                try:
                    plotItem.addItem(self.marker_angle)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_angle)
                    except Exception:
                        pass
            if self.marker_spin_data is not None:
                try:
                    plotItem.addItem(self.marker_spin_data)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_spin_data)
                    except Exception:
                        pass
            if self.marker_tilt_data is not None:
                try:
                    plotItem.addItem(self.marker_tilt_data)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_tilt_data)
                    except Exception:
                        pass
            if self.marker_angle_data is not None:
                try:
                    plotItem.addItem(self.marker_angle_data)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_angle_data)
                    except Exception:
                        pass
        except Exception:
            pass

    def updateDataDiagnostic(self, Spin_time, Spin_array, angle_time, angle_array, tilt_time, tilt_array, DataTime, SpinDataArray, TiltDataArray, AngleDataArray):
        """Update the graph with new Diagnostic data."""
        # Store data for click mapping
        self.SpinTime = Spin_time
        self.SpinArray = Spin_array
        self.AngleTime = angle_time
        self.AngleArray = angle_array
        self.TiltTime = tilt_time
        self.TiltArray = tilt_array

        self.DataTime = DataTime
        self.SpinDataArray = SpinDataArray
        self.TiltDataArray = TiltDataArray
        self.AngleDataArray = AngleDataArray

        # Plot data based on checkbox states
        self.updateGraph()
        
    def setView(self,viewIndex:int):
        self.cbolimitView.setCurrentIndex(viewIndex)
    

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