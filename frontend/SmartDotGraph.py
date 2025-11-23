from ctypes import cast
from unittest import case
from PyQt6 import QtWidgets, uic
import os
import pyqtgraph as pg
import numpy as np 
from array import array

# Module-level arrays used by the graph update. Kept as globals for minimal changes

class SmartDotGraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load the UI file (module-relative path).
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'SmartDotGraph.ui'), self, package='frontend')

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
        # Redraw using updateDataBetter when any checkbox is toggled
        try:
            self.chkAccelerometer_X.toggled.connect(self._on_checkbox_toggled)
            self.chkAccelerometer_Y.toggled.connect(self._on_checkbox_toggled)
            self.chkAccelerometer_Z.toggled.connect(self._on_checkbox_toggled)
            self.chkGyroscope_X.toggled.connect(self._on_checkbox_toggled)
            self.chkGyroscope_Y.toggled.connect(self._on_checkbox_toggled)
            self.chkGyroscope_Z.toggled.connect(self._on_checkbox_toggled)
            self.chkMagnetometer_X.toggled.connect(self._on_checkbox_toggled)
            self.chkMagnetometer_Y.toggled.connect(self._on_checkbox_toggled)
            self.chkMagnetometer_Z.toggled.connect(self._on_checkbox_toggled)
            self.chkLight.toggled.connect(self._on_checkbox_toggled)
        except Exception:
            pass
        # Hide limit view controls when not needed
        self.lblXMax.setVisible(False)
        self.lblXMin.setVisible(False)
        self.dsbLookBackSeconds.setVisible(False)
        self.dsbMinXValue.setVisible(False)
        self.dsbMaxXValue.setVisible(False)

        #Initialize graph
        self.graph.setTitle("Smart Dot Sensor Data")
        self.graph.setLabel('left', 'Sensor Values', units='Units')
        self.graph.setLabel('bottom', 'Time', units='s')
        self.graph.setMouseEnabled(x=False, y=False)
        legend = self.graph.addLegend()
        legend.setColumnCount(2)

        # Create pens and persistent plot curves to avoid recreating plot items on every update
        self.pens = {
            'acc_x': pg.mkPen(color='r', width=2),
            'acc_y': pg.mkPen(color='g', width=2),
            'acc_z': pg.mkPen(color='b', width=2),
            'gyro_x': pg.mkPen(color='c', width=2),
            'gyro_y': pg.mkPen(color='m', width=2),
            'gyro_z': pg.mkPen(color='y', width=2),
            'mag_x': pg.mkPen(color='#008080', width=2),
            'mag_y': pg.mkPen(color='#800000', width=2),
            'mag_z': pg.mkPen(color='#800080', width=2),
            'light': pg.mkPen(color='w', width=2),
        }

        # Create persistent curves (PlotDataItem) for each series and keep them in a dict
        self.curves = {}
        self.curves['acc_x'] = self.graph.plot([], [], pen=self.pens['acc_x'], name='Accelerometer_X')
        self.curves['acc_y'] = self.graph.plot([], [], pen=self.pens['acc_y'], name='Accelerometer_Y')
        self.curves['acc_z'] = self.graph.plot([], [], pen=self.pens['acc_z'], name='Accelerometer_Z')
        self.curves['gyro_x'] = self.graph.plot([], [], pen=self.pens['gyro_x'], name='Gyroscope_X')
        self.curves['gyro_y'] = self.graph.plot([], [], pen=self.pens['gyro_y'], name='Gyroscope_Y')
        self.curves['gyro_z'] = self.graph.plot([], [], pen=self.pens['gyro_z'], name='Gyroscope_Z')
        self.curves['mag_x'] = self.graph.plot([], [], pen=self.pens['mag_x'], name='Magnetometer_X')
        self.curves['mag_y'] = self.graph.plot([], [], pen=self.pens['mag_y'], name='Magnetometer_Y')
        self.curves['mag_z'] = self.graph.plot([], [], pen=self.pens['mag_z'], name='Magnetometer_Z')
        self.curves['light'] = self.graph.plot([], [], pen=self.pens['light'], name='Light')

        # Create persistent cursor and scatter markers (added to the plotItem once)
        plotItem = self.graph.getPlotItem()
        try:
            self.vline = pg.InfiniteLine(
                angle=90,
                movable=False,
                pen=pg.mkPen(color=(255,0,255), width=1, style=pg.QtCore.Qt.PenStyle.DotLine)
            )
            self.vline.setZValue(1000)
            self.vline.setVisible(False)
            plotItem.addItem(self.vline, ignoreBounds=True)
        except Exception:
            # In case adding fails, keep vline set but invisible
            self.vline = None

        # brushes for scatter markers
        self.brushes = {
            'acc_x': pg.mkBrush(255,0,0),
            'acc_y': pg.mkBrush(0,170,0),
            'acc_z': pg.mkBrush(0,0,255),
            'gyro_x': pg.mkBrush(0,255,255),
            'gyro_y': pg.mkBrush(255,0,255),
            'gyro_z': pg.mkBrush(255,255,0),
            'mag_x': pg.mkBrush(0,128,128),
            'mag_y': pg.mkBrush(128,0,0),
            'mag_z': pg.mkBrush(128,0,128),
            'light': pg.mkBrush(200,200,200),
        }

        # create scatter markers and add them to the plot; keep invisible until used
        try:
            self.marker_acc_x = pg.ScatterPlotItem(size=7, brush=self.brushes['acc_x'])
            self.marker_acc_y = pg.ScatterPlotItem(size=7, brush=self.brushes['acc_y'])
            self.marker_acc_z = pg.ScatterPlotItem(size=7, brush=self.brushes['acc_z'])
            self.marker_gyro_x = pg.ScatterPlotItem(size=7, brush=self.brushes['gyro_x'])
            self.marker_gyro_y = pg.ScatterPlotItem(size=7, brush=self.brushes['gyro_y'])
            self.marker_gyro_z = pg.ScatterPlotItem(size=7, brush=self.brushes['gyro_z'])
            self.marker_mag_x = pg.ScatterPlotItem(size=7, brush=self.brushes['mag_x'])
            self.marker_mag_y = pg.ScatterPlotItem(size=7, brush=self.brushes['mag_y'])
            self.marker_mag_z = pg.ScatterPlotItem(size=7, brush=self.brushes['mag_z'])
            self.marker_light = pg.ScatterPlotItem(size=7, brush=self.brushes['light'])
            for m in (self.marker_acc_x, self.marker_acc_y, self.marker_acc_z,
                      self.marker_gyro_x, self.marker_gyro_y, self.marker_gyro_z,
                      self.marker_mag_x, self.marker_mag_y, self.marker_mag_z,
                      self.marker_light):
                m.setVisible(False)
                plotItem.addItem(m)
        except Exception:
            # If adding markers fails, keep marker variables defined above as None or existing
            pass

        # initalize storage for plot data
        self.accelerometerTime = array('d', [0.0])
        self.accelerometerX = array('f', [0.0])
        self.accelerometerY = array('f', [0.0])
        self.accelerometerZ = array('f', [0.0])
        self.gyroscopeTime = array('d', [0.0])
        self.gyroscopeX = array('f', [0.0])
        self.gyroscopeY = array('f', [0.0])
        self.gyroscopeZ = array('f', [0.0])
        self.magnetometerTime = array('d', [0.0])
        self.magnetometerX = array('f', [0.0])
        self.magnetometerY = array('f', [0.0])
        self.magnetometerZ = array('f', [0.0])
        self.lightTime = array('d', [0.0])
        self.lightValue = array('f', [0.0])
        # Cursor and markers created above and will be reused
        self.select_all()
        self.limitViewBox()


        #Select/Deselect All buttons
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnDeselectAll.clicked.connect(self.deselect_all)
        # Print graph coordinates to terminal when user clicks on the graph
        # We map the scene position of the mouse click to the view (data) coordinates
        self.graph.scene().sigMouseClicked.connect(self._on_graph_click)

        # References to labels in the UI where we'll display the clicked values
        self.lblAccelerometer = self.findChild(QtWidgets.QLabel, 'lblAccelerometer')
        self.lblGyroscopeData = self.findChild(QtWidgets.QLabel, 'lblGyroscopeData')
        self.lblMagnomaterData = self.findChild(QtWidgets.QLabel, 'lblMagnomaterData')
        self.lblLightData = self.findChild(QtWidgets.QLabel, 'lblLightData')
    def select_all(self):
        self.chkAccelerometer_X.setChecked(True)
        self.chkAccelerometer_Y.setChecked(True)
        self.chkAccelerometer_Z.setChecked(True)
        self.chkGyroscope_X.setChecked(True)
        self.chkGyroscope_Y.setChecked(True)
        self.chkGyroscope_Z.setChecked(True)
        self.chkMagnetometer_X.setChecked(True)
        self.chkMagnetometer_Y.setChecked(True)
        self.chkMagnetometer_Z.setChecked(True)
        self.chkLight.setChecked(True)
        # trigger redraw via updateDataBetter with current arrays
        try:
            self._on_checkbox_toggled(True)
        except Exception:
            pass
    def deselect_all(self):
        self.chkAccelerometer_X.setChecked(False)
        self.chkAccelerometer_Y.setChecked(False)
        self.chkAccelerometer_Z.setChecked(False)
        self.chkGyroscope_X.setChecked(False)
        self.chkGyroscope_Y.setChecked(False)
        self.chkGyroscope_Z.setChecked(False)
        self.chkMagnetometer_X.setChecked(False)
        self.chkMagnetometer_Y.setChecked(False)
        self.chkMagnetometer_Z.setChecked(False)
        self.chkLight.setChecked(False)
        # trigger redraw via updateDataBetter with current arrays
        try:
            self._on_checkbox_toggled(False)
        except Exception:
            pass
    #to change code outside of updateDataBetter
    def limitViewBox(self):
        if( len(self.accelerometerTime)>0 and len(self.gyroscopeTime)>0 and len(self.magnetometerTime)>0 and len(self.lightTime)>0):
            last = max(self.accelerometerTime[-1], self.gyroscopeTime[-1], self.magnetometerTime[-1], self.lightTime[-1])
        else:
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
                # Use searchsorted for sorted time arrays (faster than argmin on abs diff)
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

            # Accelerometer
            if self.accelerometerTime is not None and len(self.accelerometerTime) > 0:
                idx = _nearest(self.accelerometerTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.accelerometerTime)[idx])
                    ax = float(np.asarray(self.accelerometerX)[idx]) if self.accelerometerX is not None else None
                    ay = float(np.asarray(self.accelerometerY)[idx]) if self.accelerometerY is not None else None
                    az = float(np.asarray(self.accelerometerZ)[idx]) if self.accelerometerZ is not None else None
                    # Update label instead of printing, color values to match plot lines
                    if self.lblAccelerometer is not None:
                        # colors match plotting pens: x=red, y=green, z=blue
                        ax_html = _fmt_html(ax, '#ff0000')
                        ay_html = _fmt_html(ay, '#00aa00')
                        az_html = _fmt_html(az, '#0000ff')
                        self.lblAccelerometer.setText(
                            f"Accelerometer @ t={t:.3f} (idx={idx}): x={ax_html}, y={ay_html}, z={az_html}"
                        )
                    # Show and position the persistent cursor/markers (created in __init__)
                    try:
                        if self.vline is not None:
                            self.vline.setVisible(True)
                            self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        if getattr(self, 'marker_acc_x', None) is not None:
                            if ax is not None:
                                self.marker_acc_x.setData(x=[t], y=[ax])
                                self.marker_acc_x.setVisible(True)
                            else:
                                self.marker_acc_x.setData(x=[], y=[])
                                self.marker_acc_x.setVisible(False)
                        if getattr(self, 'marker_acc_y', None) is not None:
                            if ay is not None:
                                self.marker_acc_y.setData(x=[t], y=[ay])
                                self.marker_acc_y.setVisible(True)
                            else:
                                self.marker_acc_y.setData(x=[], y=[])
                                self.marker_acc_y.setVisible(False)
                        if getattr(self, 'marker_acc_z', None) is not None:
                            if az is not None:
                                self.marker_acc_z.setData(x=[t], y=[az])
                                self.marker_acc_z.setVisible(True)
                            else:
                                self.marker_acc_z.setData(x=[], y=[])
                                self.marker_acc_z.setVisible(False)
                    except Exception:
                        pass

            # Gyroscope
            if self.gyroscopeTime is not None and len(self.gyroscopeTime) > 0:
                idx = _nearest(self.gyroscopeTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.gyroscopeTime)[idx])
                    gx = float(np.asarray(self.gyroscopeX)[idx]) if self.gyroscopeX is not None else None
                    gy = float(np.asarray(self.gyroscopeY)[idx]) if self.gyroscopeY is not None else None
                    gz = float(np.asarray(self.gyroscopeZ)[idx]) if self.gyroscopeZ is not None else None
                    if self.lblGyroscopeData is not None:
                        # gyro colors: x=cyan, y=magenta, z=yellow
                        gx_html = _fmt_html(gx, '#00ffff')
                        gy_html = _fmt_html(gy, '#ff00ff')
                        gz_html = _fmt_html(gz, '#ffff00')
                        self.lblGyroscopeData.setText(
                            f"Gyroscope @ t={t:.3f} (idx={idx}): x={gx_html}, y={gy_html}, z={gz_html}"
                        )
                    try:
                        if self.vline is not None:
                            self.vline.setVisible(True)
                            self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        if getattr(self, 'marker_gyro_x', None) is not None:
                            if gx is not None:
                                self.marker_gyro_x.setData(x=[t], y=[gx])
                                self.marker_gyro_x.setVisible(True)
                            else:
                                self.marker_gyro_x.setData(x=[], y=[])
                                self.marker_gyro_x.setVisible(False)
                        if getattr(self, 'marker_gyro_y', None) is not None:
                            if gy is not None:
                                self.marker_gyro_y.setData(x=[t], y=[gy])
                                self.marker_gyro_y.setVisible(True)
                            else:
                                self.marker_gyro_y.setData(x=[], y=[])
                                self.marker_gyro_y.setVisible(False)
                        if getattr(self, 'marker_gyro_z', None) is not None:
                            if gz is not None:
                                self.marker_gyro_z.setData(x=[t], y=[gz])
                                self.marker_gyro_z.setVisible(True)
                            else:
                                self.marker_gyro_z.setData(x=[], y=[])
                                self.marker_gyro_z.setVisible(False)
                    except Exception:
                        pass

            # Magnetometer
            if self.magnetometerTime is not None and len(self.magnetometerTime) > 0:
                idx = _nearest(self.magnetometerTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.magnetometerTime)[idx])
                    mx = float(np.asarray(self.magnetometerX)[idx]) if self.magnetometerX is not None else None
                    my = float(np.asarray(self.magnetometerY)[idx]) if self.magnetometerY is not None else None
                    mz = float(np.asarray(self.magnetometerZ)[idx]) if self.magnetometerZ is not None else None
                    if self.lblMagnomaterData is not None:
                        # magnetometer colors match plot hex codes used earlier
                        mx_html = _fmt_html(mx, '#008080')
                        my_html = _fmt_html(my, '#800000')
                        mz_html = _fmt_html(mz, '#800080')
                        self.lblMagnomaterData.setText(
                            f"Magnetometer @ t={t:.3f} (idx={idx}): x={mx_html}, y={my_html}, z={mz_html}"
                        )
                    try:
                        if self.vline is not None:
                            self.vline.setVisible(True)
                            self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        if getattr(self, 'marker_mag_x', None) is not None:
                            if mx is not None:
                                self.marker_mag_x.setData(x=[t], y=[mx])
                                self.marker_mag_x.setVisible(True)
                            else:
                                self.marker_mag_x.setData(x=[], y=[])
                                self.marker_mag_x.setVisible(False)
                        if getattr(self, 'marker_mag_y', None) is not None:
                            if my is not None:
                                self.marker_mag_y.setData(x=[t], y=[my])
                                self.marker_mag_y.setVisible(True)
                            else:
                                self.marker_mag_y.setData(x=[], y=[])
                                self.marker_mag_y.setVisible(False)
                        if getattr(self, 'marker_mag_z', None) is not None:
                            if mz is not None:
                                self.marker_mag_z.setData(x=[t], y=[mz])
                                self.marker_mag_z.setVisible(True)
                            else:
                                self.marker_mag_z.setData(x=[], y=[])
                                self.marker_mag_z.setVisible(False)
                    except Exception:
                        pass

            # Light
            if self.lightTime is not None and len(self.lightTime) > 0:
                idx = _nearest(self.lightTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.lightTime)[idx])
                    lv = float(np.asarray(self.lightValue)[idx]) if self.lightValue is not None else None
                    if self.lblLightData is not None:
                        # light uses a neutral gray color
                        lv_html = _fmt_html(lv, '#777777')
                        self.lblLightData.setText(
                            f"Light @ t={t:.3f} (idx={idx}): value={lv_html}"
                        )
                    try:
                        if self.vline is not None:
                            self.vline.setVisible(True)
                            self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        if getattr(self, 'marker_light', None) is not None:
                            if lv is not None:
                                self.marker_light.setData(x=[t], y=[lv])
                                self.marker_light.setVisible(True)
                            else:
                                self.marker_light.setData(x=[], y=[])
                                self.marker_light.setVisible(False)
                    except Exception:
                        pass

        except Exception as e:
            # Fallback: print the exception to help debugging
            print("Error mapping graph click to data coords:", e)

    def _on_checkbox_toggled(self, checked):
        """Handler for any checkbox toggle: call updateDataBetter with stored arrays
        so the plotting logic (which lives in updateDataBetter) re-runs using
        the currently stored sensor arrays."""
        try:
            # Call updateDataBetter with the current arrays stored on the instance.
            # This will clear & redraw plots according to the checkbox states.
            self.updateDataBetter(
                self.accelerometerTime, self.accelerometerX, self.accelerometerY, self.accelerometerZ,
                self.gyroscopeTime, self.gyroscopeX, self.gyroscopeY, self.gyroscopeZ,
                self.magnetometerTime, self.magnetometerX, self.magnetometerY, self.magnetometerZ,
                self.lightTime, self.lightValue
            )
        except Exception:
            # Swallow exceptions to avoid UI breakage from toggle handlers
            pass

 
    def updateDataBetter(self,
                        acclerometerTime, acclerometerX, accelerometerY, accelerometerZ,
                        gyroscoperTime, gyroscopeX, gyroscopeY, gyroscopeZ,
                        magnometerTime, 
                        magnetometerX, magnetometerY, magnetometerZ,
                        lightTime, lightValue):
        # Store incoming data as NumPy arrays (do conversion once)
        # Make explicit copies to avoid sharing buffers with producer arrays
        self.accelerometerTime = np.array(acclerometerTime, dtype=np.float64, copy=True) if acclerometerTime is not None else np.array([])
        self.accelerometerX = np.array(acclerometerX, dtype=np.float32, copy=True) if acclerometerX is not None else np.array([])
        self.accelerometerY = np.array(accelerometerY, dtype=np.float32, copy=True) if accelerometerY is not None else np.array([])
        self.accelerometerZ = np.array(accelerometerZ, dtype=np.float32, copy=True) if accelerometerZ is not None else np.array([])
        self.gyroscopeTime = np.array(gyroscoperTime, dtype=np.float64, copy=True) if gyroscoperTime is not None else np.array([])
        self.gyroscopeX = np.array(gyroscopeX, dtype=np.float32, copy=True) if gyroscopeX is not None else np.array([])
        self.gyroscopeY = np.array(gyroscopeY, dtype=np.float32, copy=True) if gyroscopeY is not None else np.array([])
        self.gyroscopeZ = np.array(gyroscopeZ, dtype=np.float32, copy=True) if gyroscopeZ is not None else np.array([])
        self.magnetometerTime = np.array(magnometerTime, dtype=np.float64, copy=True) if magnometerTime is not None else np.array([])
        self.magnetometerX = np.array(magnetometerX, dtype=np.float32, copy=True) if magnetometerX is not None else np.array([])
        self.magnetometerY = np.array(magnetometerY, dtype=np.float32, copy=True) if magnetometerY is not None else np.array([])
        self.magnetometerZ = np.array(magnetometerZ, dtype=np.float32, copy=True) if magnetometerZ is not None else np.array([])
        self.lightTime = np.array(lightTime, dtype=np.float64, copy=True) if lightTime is not None else np.array([])
        self.lightValue = np.array(lightValue, dtype=np.float32, copy=True) if lightValue is not None else np.array([])

        # Update persistent curves instead of clearing & re-creating them
        self.drawAccelerometer()
        self.drawGyroscope()
        self.drawMagnetometer()
        self.drawLight()
        if( len(self.accelerometerTime)>0 and len(self.gyroscopeTime)>0 and len(self.magnetometerTime)>0 and len(self.lightTime)>0):
            last = max(self.accelerometerTime[-1], self.gyroscopeTime[-1], self.magnetometerTime[-1], self.lightTime[-1])
        else:
            last = 0
        self.limit_view_change(last)
        # Persistent cursor/markers are created in __init__ and reused; nothing to re-add here.
    def updateAccelerometer(self, time, x, y, z):
        # store latest accelerometer arrays for click lookup
        # copy inputs to avoid referencing external buffers that may be mutated
        self.accelerometerTime = np.array(time, dtype=np.float64, copy=True)
        self.accelerometerX = np.array(x, dtype=np.float32, copy=True)
        self.accelerometerY = np.array(y, dtype=np.float32, copy=True)
        self.accelerometerZ = np.array(z, dtype=np.float32, copy=True)
        self.drawAccelerometer()
        if self.accelerometerTime.size:
            self.limit_view_change(float(self.accelerometerTime[-1]))
    def updateGyroscope(self, time, x, y, z):
        # store latest gyroscope arrays for click lookup
        self.gyroscopeTime = np.array(time, dtype=np.float64, copy=True)
        self.gyroscopeX = np.array(x, dtype=np.float32, copy=True)
        self.gyroscopeY = np.array(y, dtype=np.float32, copy=True)
        self.gyroscopeZ = np.array(z, dtype=np.float32, copy=True)
        self.drawGyroscope()
        if self.gyroscopeTime.size:
            self.limit_view_change(float(self.gyroscopeTime[-1]))
    def updateMagnetometer(self, time, x, y, z):
        # store latest magnetometer arrays for click lookup
        self.magnetometerTime = np.array(time, dtype=np.float64, copy=True)
        self.magnetometerX = np.array(x, dtype=np.float32, copy=True)
        self.magnetometerY = np.array(y, dtype=np.float32, copy=True)
        self.magnetometerZ = np.array(z, dtype=np.float32, copy=True)
        self.drawMagnetometer()
        if self.magnetometerTime.size:
            self.limit_view_change(float(self.magnetometerTime[-1]))
    def updateLight(self, time, value):
        # store latest light arrays for click lookup
        self.lightTime = np.array(time, dtype=np.float64, copy=True)
        self.lightValue = np.array(value, dtype=np.float32, copy=True)
        self.drawLight()
        if self.lightTime.size:
            self.limit_view_change(float(self.lightTime[-1]))
    def setMode(self, mode):

    
        match mode:
            case 'Accelerometer':
                self.chkAccelerometer_X.setVisible(True)
                self.chkAccelerometer_Y.setVisible(True)
                self.chkAccelerometer_Z.setVisible(True)
                self.chkGyroscope_X.setVisible(False)
                self.chkGyroscope_Y.setVisible(False)
                self.chkGyroscope_Z.setVisible(False)
                self.chkMagnetometer_X.setVisible(False)
                self.chkMagnetometer_Y.setVisible(False)
                self.chkMagnetometer_Z.setVisible(False)
                self.chkLight.setVisible(False)
                # uncheck all other checkboxes
                self.deselect_all()
            case 'Gyroscope':
                self.chkAccelerometer_X.setVisible(False)
                self.chkAccelerometer_Y.setVisible(False)
                self.chkAccelerometer_Z.setVisible(False)
                self.chkGyroscope_X.setVisible(True)
                self.chkGyroscope_Y.setVisible(True)
                self.chkGyroscope_Z.setVisible(True)
                self.chkMagnetometer_X.setVisible(False)
                self.chkMagnetometer_Y.setVisible(False)
                self.chkMagnetometer_Z.setVisible(False)
                self.chkLight.setVisible(False)
                # uncheck all other checkboxes
                self.deselect_all()
            case 'Magnetometer':
                self.chkAccelerometer_X.setVisible(False)
                self.chkAccelerometer_Y.setVisible(False)
                self.chkAccelerometer_Z.setVisible(False)
                self.chkGyroscope_X.setVisible(False)
                self.chkGyroscope_Y.setVisible(False)
                self.chkGyroscope_Z.setVisible(False)
                self.chkMagnetometer_X.setVisible(True)
                self.chkMagnetometer_Y.setVisible(True)
                self.chkMagnetometer_Z.setVisible(True)
                self.chkLight.setVisible(False)
                 # uncheck all other checkboxes
                self.deselect_all()
            case 'Light':
                self.chkAccelerometer_X.setVisible(False)
                self.chkAccelerometer_Y.setVisible(False)
                self.chkAccelerometer_Z.setVisible(False)
                self.chkGyroscope_X.setVisible(False)
                self.chkGyroscope_Y.setVisible(False)
                self.chkGyroscope_Z.setVisible(False)
                self.chkMagnetometer_X.setVisible(False)
                self.chkMagnetometer_Y.setVisible(False)
                self.chkMagnetometer_Z.setVisible(False)
                self.chkLight.setVisible(True)
                 # uncheck all other checkboxes
                self.deselect_all()
            case _:
                # Show all checkboxes
                self.chkAccelerometer_X.setVisible(True)
                self.chkAccelerometer_Y.setVisible(True)
                self.chkAccelerometer_Z.setVisible(True)
                self.chkGyroscope_X.setVisible(True)
                self.chkGyroscope_Y.setVisible(True)
                self.chkGyroscope_Z.setVisible(True)
                self.chkMagnetometer_X.setVisible(True)
                self.chkMagnetometer_Y.setVisible(True)
                self.chkMagnetometer_Z.setVisible(True)
                self.chkLight.setVisible(True)
    def drawAccelerometer(self) :
        # Use persistent PlotDataItems and update their data/visibility
        try:
            if self.chkAccelerometer_X.isChecked():
                self.curves['acc_x'].setData(self.accelerometerTime, self.accelerometerX)
                self.curves['acc_x'].setVisible(True)
            else:
                self.curves['acc_x'].setVisible(False)
            if self.chkAccelerometer_Y.isChecked():
                self.curves['acc_y'].setData(self.accelerometerTime, self.accelerometerY)
                self.curves['acc_y'].setVisible(True)
            else:
                self.curves['acc_y'].setVisible(False)
            if self.chkAccelerometer_Z.isChecked():
                self.curves['acc_z'].setData(self.accelerometerTime, self.accelerometerZ)
                self.curves['acc_z'].setVisible(True)
            else:
                self.curves['acc_z'].setVisible(False)
        except Exception:
            # Fallback to no-op if curves aren't available
            pass
    def drawGyroscope(self) :
        try:
            if self.chkGyroscope_X.isChecked():
                self.curves['gyro_x'].setData(self.gyroscopeTime, self.gyroscopeX)
                self.curves['gyro_x'].setVisible(True)
            else:
                self.curves['gyro_x'].setVisible(False)
            if self.chkGyroscope_Y.isChecked():
                self.curves['gyro_y'].setData(self.gyroscopeTime, self.gyroscopeY)
                self.curves['gyro_y'].setVisible(True)
            else:
                self.curves['gyro_y'].setVisible(False)
            if self.chkGyroscope_Z.isChecked():
                self.curves['gyro_z'].setData(self.gyroscopeTime, self.gyroscopeZ)
                self.curves['gyro_z'].setVisible(True)
            else:
                self.curves['gyro_z'].setVisible(False)
        except Exception:
            pass
    def drawMagnetometer(self) :
        try:
            if self.chkMagnetometer_X.isChecked():
                self.curves['mag_x'].setData(self.magnetometerTime, self.magnetometerX)
                self.curves['mag_x'].setVisible(True)
            else:
                self.curves['mag_x'].setVisible(False)
            if self.chkMagnetometer_Y.isChecked():
                self.curves['mag_y'].setData(self.magnetometerTime, self.magnetometerY)
                self.curves['mag_y'].setVisible(True)
            else:
                self.curves['mag_y'].setVisible(False)
            if self.chkMagnetometer_Z.isChecked():
                self.curves['mag_z'].setData(self.magnetometerTime, self.magnetometerZ)
                self.curves['mag_z'].setVisible(True)
            else:
                self.curves['mag_z'].setVisible(False)
        except Exception:
            pass
    def drawLight(self) :
        try:
            if self.chkLight.isChecked():
                self.curves['light'].setData(self.lightTime, self.lightValue)
                self.curves['light'].setVisible(True)
            else:
                self.curves['light'].setVisible(False)
        except Exception:
            pass
    def setView(self, viewIndex: int):
        self.cbolimitView.setCurrentIndex(viewIndex)



if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = SmartDotGraph()
    window.setWindowTitle("Smart Dot Graph")
    window.show()

 
    
    # Start the event loop
    sys.exit(app.exec())