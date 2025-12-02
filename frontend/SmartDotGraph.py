from ctypes import cast
from unittest import case
from PyQt6 import QtWidgets, uic
import os
import pyqtgraph as pg
import numpy as np 

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

        # initalize storage for plot data
        self.accelerometerTime = np.array([0.0])
        self.accelerometerX = np.array([0.0])
        self.accelerometerY = np.array([0.0])
        self.accelerometerZ = np.array([0.0])
        self.gyroscopeTime = np.array([0.0])
        self.gyroscopeX = np.array([0.0])
        self.gyroscopeY = np.array([0.0])
        self.gyroscopeZ = np.array([0.0])
        self.magnetometerTime = np.array([0.0])
        self.magnetometerX = np.array([0.0])
        self.magnetometerY = np.array([0.0])
        self.magnetometerZ = np.array([0.0])
        self.lightTime = np.array([0.0])
        self.lightValue = np.array([0.0])
        # Cursor and markers will be created on first click (lazy)
        self.vline = None
        self.marker_acc_x = None
        self.marker_acc_y = None
        self.marker_acc_z = None
        self.marker_gyro_x = None
        self.marker_gyro_y = None
        self.marker_gyro_z = None
        self.marker_mag_x = None
        self.marker_mag_y = None
        self.marker_mag_z = None
        self.marker_light = None
        self.select_all()
        self.limitViewBox()


        #Select/Deselect All buttons
        self.btnSelectAll.clicked.connect(self.select_all)
        self.btnDeselectAll.clicked.connect(self.deselect_all)
        # #print graph coordinates to terminal when user clicks on the graph
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

            # Accelerometer
            if self.accelerometerTime is not None and len(self.accelerometerTime) > 0:
                idx = _nearest(self.accelerometerTime, x_click)
                if idx is not None:
                    t = float(np.asarray(self.accelerometerTime)[idx])
                    ax = float(np.asarray(self.accelerometerX)[idx]) if self.accelerometerX is not None else None
                    ay = float(np.asarray(self.accelerometerY)[idx]) if self.accelerometerY is not None else None
                    az = float(np.asarray(self.accelerometerZ)[idx]) if self.accelerometerZ is not None else None
                    # Update label instead of #printing, color values to match plot lines
                    if self.lblAccelerometer is not None:
                        # colors match plotting pens: x=red, y=green, z=blue
                        ax_html = _fmt_html(ax, '#ff0000')
                        ay_html = _fmt_html(ay, '#00aa00')
                        az_html = _fmt_html(az, '#0000ff')
                        self.lblAccelerometer.setText(
                            f"Accelerometer @ t={t:.3f} (idx={idx}): x={ax_html}, y={ay_html}, z={az_html}"
                        )
                    # ensure cursor exists and set it to exact clicked x; create markers lazily
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
                        self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        plotItem = self.graph.getPlotItem()
                        if self.marker_acc_x is None:
                            self.marker_acc_x = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,0,0))
                            self.marker_acc_x.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_acc_x)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_acc_x)
                                except Exception:
                                    pass
                        if self.marker_acc_y is None:
                            self.marker_acc_y = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(0,170,0))
                            self.marker_acc_y.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_acc_y)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_acc_y)
                                except Exception:
                                    pass
                        if self.marker_acc_z is None:
                            self.marker_acc_z = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(0,0,255))
                            self.marker_acc_z.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_acc_z)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_acc_z)
                                except Exception:
                                    pass

                        if ax is not None:
                            self.marker_acc_x.setData(x=[t], y=[ax])
                        else:
                            self.marker_acc_x.setData(x=[], y=[])
                        if ay is not None:
                            self.marker_acc_y.setData(x=[t], y=[ay])
                        else:
                            self.marker_acc_y.setData(x=[], y=[])
                        if az is not None:
                            self.marker_acc_z.setData(x=[t], y=[az])
                        else:
                            self.marker_acc_z.setData(x=[], y=[])
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
                    # ensure cursor exists and set it to exact clicked x; create gyro markers lazily
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
                        self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        plotItem = self.graph.getPlotItem()
                        if self.marker_gyro_x is None:
                            self.marker_gyro_x = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(0,255,255))
                            self.marker_gyro_x.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_gyro_x)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_gyro_x)
                                except Exception:
                                    pass
                        if self.marker_gyro_y is None:
                            self.marker_gyro_y = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,0,255))
                            self.marker_gyro_y.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_gyro_y)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_gyro_y)
                                except Exception:
                                    pass
                        if self.marker_gyro_z is None:
                            self.marker_gyro_z = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,255,0))
                            self.marker_gyro_z.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_gyro_z)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_gyro_z)
                                except Exception:
                                    pass

                        if gx is not None:
                            self.marker_gyro_x.setData(x=[t], y=[gx])
                        else:
                            self.marker_gyro_x.setData(x=[], y=[])
                        if gy is not None:
                            self.marker_gyro_y.setData(x=[t], y=[gy])
                        else:
                            self.marker_gyro_y.setData(x=[], y=[])
                        if gz is not None:
                            self.marker_gyro_z.setData(x=[t], y=[gz])
                        else:
                            self.marker_gyro_z.setData(x=[], y=[])
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
                    # ensure cursor exists and set it to exact clicked x; create magnetometer markers lazily
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
                        self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        plotItem = self.graph.getPlotItem()
                        if self.marker_mag_x is None:
                            self.marker_mag_x = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(0,128,128))
                            self.marker_mag_x.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_mag_x)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_mag_x)
                                except Exception:
                                    pass
                        if self.marker_mag_y is None:
                            self.marker_mag_y = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(128,0,0))
                            self.marker_mag_y.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_mag_y)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_mag_y)
                                except Exception:
                                    pass
                        if self.marker_mag_z is None:
                            self.marker_mag_z = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(128,0,128))
                            self.marker_mag_z.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_mag_z)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_mag_z)
                                except Exception:
                                    pass

                        if mx is not None:
                            self.marker_mag_x.setData(x=[t], y=[mx])
                        else:
                            self.marker_mag_x.setData(x=[], y=[])
                        if my is not None:
                            self.marker_mag_y.setData(x=[t], y=[my])
                        else:
                            self.marker_mag_y.setData(x=[], y=[])
                        if mz is not None:
                            self.marker_mag_z.setData(x=[t], y=[mz])
                        else:
                            self.marker_mag_z.setData(x=[], y=[])
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
                    # ensure cursor exists and set it to exact clicked x; create light marker lazily
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
                        self.vline.setPos(x_click)
                    except Exception:
                        pass
                    try:
                        plotItem = self.graph.getPlotItem()
                        if self.marker_light is None:
                            self.marker_light = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(200,200,200))
                            self.marker_light.setZValue(200)
                            try:
                                plotItem.addItem(self.marker_light)
                            except Exception:
                                try:
                                    self.graph.addItem(self.marker_light)
                                except Exception:
                                    pass
                        if lv is not None:
                            self.marker_light.setData(x=[t], y=[lv])
                        else:
                            self.marker_light.setData(x=[], y=[])
                    except Exception:
                        pass

        except Exception as e:
            # Fallback: #print the exception to help debugging
            #print("Error mapping graph click to data coords:", e)

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
        self.graph.clear()  # Clear existing plots
        #store data in class variables
        self.accelerometerTime = acclerometerTime
        self.accelerometerX = acclerometerX
        self.accelerometerY = accelerometerY    
        self.accelerometerZ = accelerometerZ
        self.gyroscopeTime = gyroscoperTime
        self.gyroscopeX = gyroscopeX
        self.gyroscopeY = gyroscopeY
        self.gyroscopeZ = gyroscopeZ
        self.magnetometerTime = magnometerTime
        self.magnetometerX = magnetometerX
        self.magnetometerY = magnetometerY
        self.magnetometerZ = magnetometerZ
        self.lightTime = lightTime
        self.lightValue = lightValue

        # Plot data based on checkbox states
        self.drawAccelerometer()
        self.drawGyroscope()
        self.drawMagnetometer()
        self.drawLight()
        if( len(self.accelerometerTime)>0 and len(self.gyroscopeTime)>0 and len(self.magnetometerTime)>0 and len(self.lightTime)>0):
            last = max(self.accelerometerTime[-1], self.gyroscopeTime[-1], self.magnetometerTime[-1], self.lightTime[-1])
        else:
            last = 0
        self.limit_view_change(last)
        # re-add cursor and markers so they persist after clear()
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
            if self.marker_acc_x is not None:
                try:
                    plotItem.addItem(self.marker_acc_x)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_acc_x)
                    except Exception:
                        pass
            if self.marker_acc_y is not None:
                try:
                    plotItem.addItem(self.marker_acc_y)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_acc_y)
                    except Exception:
                        pass
            if self.marker_acc_z is not None:
                try:
                    plotItem.addItem(self.marker_acc_z)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_acc_z)
                    except Exception:
                        pass
            if self.marker_gyro_x is not None:
                try:
                    plotItem.addItem(self.marker_gyro_x)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_gyro_x)
                    except Exception:
                        pass
            if self.marker_gyro_y is not None:
                try:
                    plotItem.addItem(self.marker_gyro_y)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_gyro_y)
                    except Exception:
                        pass
            if self.marker_gyro_z is not None:
                try:
                    plotItem.addItem(self.marker_gyro_z)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_gyro_z)
                    except Exception:
                        pass
            if self.marker_mag_x is not None:
                try:
                    plotItem.addItem(self.marker_mag_x)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_mag_x)
                    except Exception:
                        pass
            if self.marker_mag_y is not None:
                try:
                    plotItem.addItem(self.marker_mag_y)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_mag_y)
                    except Exception:
                        pass
            if self.marker_mag_z is not None:
                try:
                    plotItem.addItem(self.marker_mag_z)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_mag_z)
                    except Exception:
                        pass
            if self.marker_light is not None:
                try:
                    plotItem.addItem(self.marker_light)
                except Exception:
                    try:
                        self.graph.addItem(self.marker_light)
                    except Exception:
                        pass
        except Exception:
            pass
    def updateAccelerometer(self, time, x, y, z):
        # store latest accelerometer arrays for click lookup
        self.accelerometerTime = np.asarray(time)
        self.accelerometerX = np.asarray(x)
        self.accelerometerY = np.asarray(y)
        self.accelerometerZ = np.asarray(z)
        self.drawAccelerometer()
        self.limit_view_change(time[-1])
    def updateGyroscope(self, time, x, y, z):
        # store latest gyroscope arrays for click lookup
        self.gyroscopeTime = np.asarray(time)
        self.gyroscopeX = np.asarray(x)
        self.gyroscopeY = np.asarray(y)
        self.gyroscopeZ = np.asarray(z)
        self.drawGyroscope()
        self.limit_view_change(time[-1])
    def updateMagnetometer(self, time, x, y, z):
        # store latest magnetometer arrays for click lookup
        self.magnetometerTime = np.asarray(time)
        self.magnetometerX = np.asarray(x)
        self.magnetometerY = np.asarray(y)
        self.magnetometerZ = np.asarray(z)
        self.drawMagnetometer()
        self.limit_view_change(time[-1])
    def updateLight(self, time, value):
        # store latest light arrays for click lookup
        self.lightTime = np.asarray(time)
        self.lightValue = np.asarray(value)
        self.drawLight()
        self.limit_view_change(time[-1])
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
        if self.chkAccelerometer_X.isChecked():
            self.graph.plot(self.accelerometerTime, self.accelerometerX, pen=pg.mkPen(color='r', width=2), name='Accelerometer_X')
        if self.chkAccelerometer_Y.isChecked():
            self.graph.plot(self.accelerometerTime, self.accelerometerY, pen=pg.mkPen(color='g', width=2), name='Accelerometer_Y')
        if self.chkAccelerometer_Z.isChecked():
            self.graph.plot(self.accelerometerTime, self.accelerometerZ, pen=pg.mkPen(color='b', width=2), name='Accelerometer_Z')
    def drawGyroscope(self) :
        if self.chkGyroscope_X.isChecked():
            self.graph.plot(self.gyroscopeTime, self.gyroscopeX, pen=pg.mkPen(color='c', width=2), name='Gyroscope_X')
        if self.chkGyroscope_Y.isChecked():
            self.graph.plot(self.gyroscopeTime, self.gyroscopeY, pen=pg.mkPen(color='m', width=2), name='Gyroscope_Y')
        if self.chkGyroscope_Z.isChecked():
            self.graph.plot(self.gyroscopeTime, self.gyroscopeZ, pen=pg.mkPen(color='y', width=2), name='Gyroscope_Z')   
    def drawMagnetometer(self) :
        if self.chkMagnetometer_X.isChecked():
            self.graph.plot(self.magnetometerTime, self.magnetometerX, pen=pg.mkPen(color="#008080", width=2), name='Magnetometer_X')
        if self.chkMagnetometer_Y.isChecked():
            self.graph.plot(self.magnetometerTime, self.magnetometerY, pen=pg.mkPen(color="#800000", width=2), name='Magnetometer_Y')
        if self.chkMagnetometer_Z.isChecked():
            self.graph.plot(self.magnetometerTime, self.magnetometerZ, pen=pg.mkPen(color='#800080', width=2), name='Magnetometer_Z')
    def drawLight(self) :
        if self.chkLight.isChecked():
            self.graph.plot(self.lightTime, self.lightValue, pen=pg.mkPen(color='w', width=2), name='Light')
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