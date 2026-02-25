from ctypes import cast
from unittest import case
from PyQt6 import QtWidgets, uic
import os
import pyqtgraph as pg
import numpy as np
from array import array

# Module-level arrays used by the graph update. Kept as globals for minimal changes

class MotorGraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load the UI file.
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'MotorGraph.ui'), self, package='frontend')

        # Get references to UI elements
        self.graph = self.findChild(pg.PlotWidget, 'grphSmartDot')


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

        # Create pens and persistent plot curves to avoid recreating plot items on every update
        # motor curves use RPM=red, Angle=green, Tilt=blue
        # encoder/data overlays use analysis colors: RPM=cyan, Angle=magenta, Tilt=yellow
        self.pens = {
            'spin': pg.mkPen(color=(255, 0, 0), width=2),
            'tilt': pg.mkPen(color=(0, 170, 0), width=2),
            'angle': pg.mkPen(color=(0, 0, 255), width=2),
            'spin_data': pg.mkPen(color=(0, 255, 255), width=1, style=pg.QtCore.Qt.PenStyle.DashLine),  # cyan
            'tilt_data': pg.mkPen(color=(255, 0, 255), width=1, style=pg.QtCore.Qt.PenStyle.DashLine),  # magenta
            'angle_data': pg.mkPen(color=(255, 255, 0), width=1, style=pg.QtCore.Qt.PenStyle.DashLine),  # yellow
        }

        # persistent curves
        self.curves = {}
        self.curves['spin'] = self.graph.plot([], [], pen=self.pens['spin'], name='Spin')
        self.curves['tilt'] = self.graph.plot([], [], pen=self.pens['tilt'], name='Tilt')
        self.curves['angle'] = self.graph.plot([], [], pen=self.pens['angle'], name='Angle')
        self.curves['spin_data'] = self.graph.plot([], [], pen=self.pens['spin_data'], name='Spin Data')
        self.curves['tilt_data'] = self.graph.plot([], [], pen=self.pens['tilt_data'], name='Tilt Data')
        self.curves['angle_data'] = self.graph.plot([], [], pen=self.pens['angle_data'], name='Angle Data')

        # Create persistent cursor and markers
        plotItem = self.graph.getPlotItem()
        try:
            self.vline = pg.InfiniteLine(angle=90, movable=False,
                                         pen=pg.mkPen(color=(255,0,255), width=1, style=pg.QtCore.Qt.PenStyle.DotLine))
            self.vline.setZValue(1000)
            self.vline.setVisible(False)
            plotItem.addItem(self.vline, ignoreBounds=True)
        except Exception:
            self.vline = None

        # scatter markers
        try:
            self.marker_spin = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255,0,0))
            self.marker_tilt = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(0,170,0))
            self.marker_angle = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(0,0,255))
            # encoder markers use cyan/magenta/yellow
            self.marker_spin_data = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(0,255,255))
            self.marker_tilt_data = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,0,255))
            self.marker_angle_data = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,255,0))
            for m in (self.marker_spin, self.marker_tilt, self.marker_angle,
                      self.marker_spin_data, self.marker_tilt_data, self.marker_angle_data):
                m.setVisible(False)
                plotItem.addItem(m)
        except Exception:
            pass

        # initalize storage for plot data
        self.SpinTime = array('d', [0.0])
        self.TiltTime = array('d', [0.0])
        self.AngleTime = array('d', [0.0])
        self.SpinArray = array('f', [0.0])
        self.TiltArray = array('f', [0.0])
        self.AngleArray = array('f', [0.0])

        self.DataTime = array('d', [0.0])
        self.SpinDataArray = array('f', [0.0])
        self.TiltDataArray = array('f', [0.0])
        self.AngleDataArray = array('f', [0.0])

        # motor time (single reference for motor series) used for click mapping
        self.MotorTime = array('d', [0.0])

        # Cursor and markers created above and will be reused

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

            # Helper to find nearest index (use searchsorted for sorted arrays)
            def _nearest(time_arr, val):
                if time_arr is None or len(time_arr) == 0:
                    return None
                ta = np.asarray(time_arr)
                idx = np.searchsorted(ta, val)
                if idx == 0:
                    return 0
                if idx >= len(ta):
                    return len(ta) - 1
                left = idx - 1
                right = idx
                if abs(ta[left] - val) <= abs(ta[right] - val):
                    return int(left)
                return int(right)

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
                    # Show and position persistent cursor/markers
                    try:
                        if self.vline is not None:
                            self.vline.setVisible(True)
                            self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        if getattr(self, 'marker_spin', None) is not None:
                            if spin is not None:
                                self.marker_spin.setData(x=[t], y=[spin])
                                self.marker_spin.setVisible(True)
                            else:
                                self.marker_spin.setData(x=[], y=[])
                                self.marker_spin.setVisible(False)
                        if getattr(self, 'marker_tilt', None) is not None:
                            if tilt is not None:
                                self.marker_tilt.setData(x=[t], y=[tilt])
                                self.marker_tilt.setVisible(True)
                            else:
                                self.marker_tilt.setData(x=[], y=[])
                                self.marker_tilt.setVisible(False)
                        if getattr(self, 'marker_angle', None) is not None:
                            if angle is not None:
                                self.marker_angle.setData(x=[t], y=[angle])
                                self.marker_angle.setVisible(True)
                            else:
                                self.marker_angle.setData(x=[], y=[])
                                self.marker_angle.setVisible(False)
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
                        # encoder RPM uses cyan
                        spin_html = _fmt_html(spin_data, '#00ffff')
                        self.lblEncoderData.setText(f"Encoder Data @ t={t:.3f}: Spin={spin_html}")
                    try:
                        if getattr(self, 'marker_spin_data', None) is not None:
                            if spin_data is not None:
                                self.marker_spin_data.setData(x=[t], y=[spin_data])
                                self.marker_spin_data.setVisible(True)
                            else:
                                self.marker_spin_data.setData(x=[], y=[])
                                self.marker_spin_data.setVisible(False)
                    except Exception:
                        pass
            # angle
            if self.AngleDataTime is not None and len(self.AngleDataTime) > 0:
                idx = _nearest(self.AngleDataTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.AngleDataTime)[idx])
                    angle_data = float(np.asarray(self.AngleDataArray)[idx]) if (self.AngleDataArray is not None and len(self.AngleDataArray) > idx) else None
                    if self.lblEncoderData is not None:
                        # encoder Angle uses magenta
                        angle_html = _fmt_html(angle_data, '#ff00ff')
                        existing = self.lblEncoderData.text() if self.lblEncoderData is not None else ''
                        self.lblEncoderData.setText(existing + f" Angle={angle_html}")
                    try:
                        if getattr(self, 'marker_angle_data', None) is not None:
                            if angle_data is not None:
                                self.marker_angle_data.setData(x=[t], y=[angle_data])
                                self.marker_angle_data.setVisible(True)
                            else:
                                self.marker_angle_data.setData(x=[], y=[])
                                self.marker_angle_data.setVisible(False)
                    except Exception:
                        pass
            # tilt
            if self.TiltDataTime is not None and len(self.TiltDataTime) > 0:
                idx = _nearest(self.TiltDataTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.TiltDataTime)[idx])
                    tilt_data = float(np.asarray(self.TiltDataArray)[idx]) if (self.TiltDataArray is not None and len(self.TiltDataArray) > idx) else None
                    if self.lblEncoderData is not None:
                        # encoder Tilt uses yellow
                        tilt_html = _fmt_html(tilt_data, '#ffff00')
                        existing = self.lblEncoderData.text() if self.lblEncoderData is not None else ''
                        self.lblEncoderData.setText(existing + f" Tilt={tilt_html}")
                    try:
                        if getattr(self, 'marker_tilt_data', None) is not None:
                            if tilt_data is not None:
                                self.marker_tilt_data.setData(x=[t], y=[tilt_data])
                                self.marker_tilt_data.setVisible(True)
                            else:
                                self.marker_tilt_data.setData(x=[], y=[])
                                self.marker_tilt_data.setVisible(False)
                    except Exception:
                        pass

        except Exception as e:
            # Fallback: print the exception to help debugging
            print("Error mapping graph click to data coords:", e)

 
    def updateDataBetter(self,MotorTime, SpinArray, TiltArray, AngleArray
                         ,DataTime, SpinDataArray, TiltDataArray, AngleDataArray):
        """Update the graph with new Smart Dot sensor data."""
        # Store data for click mapping
        # copy inputs to numpy arrays to avoid sharing buffers
        self.SpinTime = np.array(MotorTime, dtype=np.float64, copy=True) if MotorTime is not None else np.array([])
        self.TiltTime = self.SpinTime
        self.AngleTime = self.SpinTime
        self.SpinArray = np.array(SpinArray, dtype=np.float32, copy=True) if SpinArray is not None else np.array([])
        self.TiltArray = np.array(TiltArray, dtype=np.float32, copy=True) if TiltArray is not None else np.array([])
        self.AngleArray = np.array(AngleArray, dtype=np.float32, copy=True) if AngleArray is not None else np.array([])

        self.DataTime = np.array(DataTime, dtype=np.float64, copy=True) if DataTime is not None else np.array([])
        self.SpinDataArray = np.array(SpinDataArray, dtype=np.float32, copy=True) if SpinDataArray is not None else np.array([])
        self.TiltDataArray = np.array(TiltDataArray, dtype=np.float32, copy=True) if TiltDataArray is not None else np.array([])
        self.AngleDataArray = np.array(AngleDataArray, dtype=np.float32, copy=True) if AngleDataArray is not None else np.array([])

        # Update plot using persistent curves
        self.updateGraph()

    def updateGraph(self):
        # Update persistent curves using setData and setVisible
        try:
            if self.chkSpin.isChecked():
                self.curves['spin'].setData(self.SpinTime, self.SpinArray)
                self.curves['spin'].setVisible(True)
            else:
                self.curves['spin'].setVisible(False)
            if self.chkTilt.isChecked():
                self.curves['tilt'].setData(self.TiltTime, self.TiltArray)
                self.curves['tilt'].setVisible(True)
            else:
                self.curves['tilt'].setVisible(False)
            if self.chkAngle.isChecked():
                self.curves['angle'].setData(self.AngleTime, self.AngleArray)
                self.curves['angle'].setVisible(True)
            else:
                self.curves['angle'].setVisible(False)
            if self.chkSpinData.isChecked():
                self.curves['spin_data'].setData(self.DataTime, self.SpinDataArray)
                self.curves['spin_data'].setVisible(True)
            else:
                self.curves['spin_data'].setVisible(False)
            if self.chkTiltData.isChecked():
                self.curves['tilt_data'].setData(self.DataTime, self.TiltDataArray)
                self.curves['tilt_data'].setVisible(True)
            else:
                self.curves['tilt_data'].setVisible(False)
            if self.chkAngleData.isChecked():
                self.curves['angle_data'].setData(self.DataTime, self.AngleDataArray)
                self.curves['angle_data'].setVisible(True)
            else:
                self.curves['angle_data'].setVisible(False)
        except Exception:
            pass

        # Adjust view based on limit view setting
        try:
            if len(self.SpinTime) and len(self.DataTime):
                last = max(self.SpinTime[-1], self.TiltTime[-1], self.AngleTime[-1], self.DataTime[-1])
            else:
                last = 0
        except Exception:
            last = 0
        self.limit_view_change(last)

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
    from array import array
    sampleTime = array('d', [0,1,2,3,4,5,6,7,8,9,10])
    sampleSpin = array('f', [0,100,200,300,400,500,600,500,400,300,200])
    sampleTilt = array('f', [0,10,20,30,40,50,40,30,20,10,0])
    sampleAngle = array('f', [0,-20,-40,-60,-80,-90,-80,-60,-40,-20,0])
    sampleSpinData = array('f', [0,90,190,290,390,490,590,490,390,290,190])
    sampleTiltData = array('f', [0,15,25,35,45,55,45,35,25,15,5])
    sampleAngleData = array('f', [0,-25,-45,-65,-85,-95,-85,-65,-45,-25,5])

    window.updateDataBetter(sampleTime, sampleSpin, sampleTilt, sampleAngle,
                            sampleTime, sampleSpinData, sampleTiltData, sampleAngleData)

    # Start the event loop
    sys.exit(app.exec())