import time
from PyQt6 import QtWidgets, uic
import os
from PyQt6.QtCore import Qt, QTimer
import numpy as np

from .MotorGraph import MotorGraph
from .SmartDotGraph import SmartDotGraph
import math
from PyQt6.QtCore import pyqtSignal
from backend.models.SmartDotData import SmartDotDataInstance
import pyqtgraph as pg
from BSC import bsc 
import utils
from utils import PackageSmartDotData, SmartDotDataPackage, PackageMotorData, MotorDataPackage
from .PostDialog import PostDialog

class AnalysisDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, type: str = None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'AnalysisDialog.ui'), self, package='frontend')
        self.lblTitle = self.findChild(QtWidgets.QLabel, 'lblTitle')
        self.dbbMain = self.findChild(QtWidgets.QDialogButtonBox, 'dbbMain')
        self.dbbMain.accepted.connect(self.accept)
        self.dbbMain.rejected.connect(self.reject)
        self.graph = self.findChild(pg.PlotWidget, 'grphAnalysis')
        self.spnRangeWidth = self.findChild(QtWidgets.QDoubleSpinBox, 'spnRangeWidth')
        self.btnRangeReset = self.findChild(QtWidgets.QPushButton, 'btnRangeReset')
        self.chkAccelX = self.findChild(QtWidgets.QCheckBox, 'chkAccelX')
        self.chkAccelY = self.findChild(QtWidgets.QCheckBox, 'chkAccelY')
        self.chkAccelZ = self.findChild(QtWidgets.QCheckBox, 'chkAccelZ')
        self.chkGyroX = self.findChild(QtWidgets.QCheckBox, 'chkGyroX')
        self.chkGyroY = self.findChild(QtWidgets.QCheckBox, 'chkGyroY')
        self.chkGyroZ = self.findChild(QtWidgets.QCheckBox, 'chkGyroZ')
        self.chkMagX = self.findChild(QtWidgets.QCheckBox, 'chkMagX')
        self.chkMagY = self.findChild(QtWidgets.QCheckBox, 'chkMagY')
        self.chkMagZ = self.findChild(QtWidgets.QCheckBox, 'chkMagZ')
        self.chkLight = self.findChild(QtWidgets.QCheckBox, 'chkLight')
        self.chkMotorRPM = self.findChild(QtWidgets.QCheckBox, 'chkMotorRPM')
        self.chkMotorAngle = self.findChild(QtWidgets.QCheckBox, 'chkMotorAngle')
        self.chkMotorTilt = self.findChild(QtWidgets.QCheckBox, 'chkMotorTilt')
        self.chkEncoderRPM = self.findChild(QtWidgets.QCheckBox, 'chkEncoderRPM')
        self.chkEncoderAngle = self.findChild(QtWidgets.QCheckBox, 'chkEncoderAngle')
        self.chkEncoderTilt = self.findChild(QtWidgets.QCheckBox, 'chkEncoderTilt')
        self.lblHighlight = self.findChild(QtWidgets.QLabel, 'lblHighlight')

        self.setWindowTitle("Analysis Options")
        self.setModal(False)
        self.resize(1200, 900)

        self.accxColor = "#ff0000" # red
        self.accyColor = "#00aa00" # green
        self.acczColor = "#0000ff" # blue
        self.gyroxColor = "#00ffff" # cyan
        self.gyroyColor = "#ff00ff" # magenta
        self.gyrozColor = "#ffff00" # yellow
        self.magxColor = "#008080" # teal
        self.magyColor = "#800000" # maroon
        self.magzColor = "#800080" # purple
        self.lightColor = "#777777" # gray

        self.motorRPMColor = "#ff0000" # red
        self.motorAngleColor = "#00aa00" # green
        self.motorTiltColor = "#0000ff" # blue
        self.encoderRPMColor = "#00ffff" # cyan
        self.encoderAngleColor = "#ff00ff" # magenta
        self.encoderTiltColor = "#ffff00" # yellow

        self.series = {}
        self.seriesChecks = {
            "accel_x": self.chkAccelX,
            "accel_y": self.chkAccelY,
            "accel_z": self.chkAccelZ,
            "gyro_x": self.chkGyroX,
            "gyro_y": self.chkGyroY,
            "gyro_z": self.chkGyroZ,
            "mag_x": self.chkMagX,
            "mag_y": self.chkMagY,
            "mag_z": self.chkMagZ,
            "light": self.chkLight,
            "motor_rpm": self.chkMotorRPM,
            "motor_angle": self.chkMotorAngle,
            "motor_tilt": self.chkMotorTilt,
            "encoder_rpm": self.chkEncoderRPM,
            "encoder_angle": self.chkEncoderAngle,
            "encoder_tilt": self.chkEncoderTilt,
        }
        self.seriesColors = {
            "accel_x": self.accxColor,
            "accel_y": self.accyColor,
            "accel_z": self.acczColor,
            "gyro_x": self.gyroxColor,
            "gyro_y": self.gyroyColor,
            "gyro_z": self.gyrozColor,
            "mag_x": self.magxColor,
            "mag_y": self.magyColor,
            "mag_z": self.magzColor,
            "light": self.lightColor,
            "motor_rpm": self.motorRPMColor,
            "motor_angle": self.motorAngleColor,
            "motor_tilt": self.motorTiltColor,
            "encoder_rpm": self.encoderRPMColor,
            "encoder_angle": self.encoderAngleColor,
            "encoder_tilt": self.encoderTiltColor,
        }
        self.seriesDefs = {
            "smartdot": {
                "accel_x": {"label": "Accel X", "time": "time_accel", "data": "accel_x", "color": self.accxColor, "deriv": True, "fft": True},
                "accel_y": {"label": "Accel Y", "time": "time_accel", "data": "accel_y", "color": self.accyColor, "deriv": True, "fft": True},
                "accel_z": {"label": "Accel Z", "time": "time_accel", "data": "accel_z", "color": self.acczColor, "deriv": True, "fft": True},
                "gyro_x": {"label": "Gyro X", "time": "time_gyro", "data": "gyro_x", "color": self.gyroxColor, "deriv": True, "fft": True},
                "gyro_y": {"label": "Gyro Y", "time": "time_gyro", "data": "gyro_y", "color": self.gyroyColor, "deriv": True, "fft": True},
                "gyro_z": {"label": "Gyro Z", "time": "time_gyro", "data": "gyro_z", "color": self.gyrozColor, "deriv": True, "fft": True},
                "mag_x": {"label": "Mag X", "time": "time_mag", "data": "mag_x", "color": self.magxColor, "deriv": True, "fft": True},
                "mag_y": {"label": "Mag Y", "time": "time_mag", "data": "mag_y", "color": self.magyColor, "deriv": True, "fft": True},
                "mag_z": {"label": "Mag Z", "time": "time_mag", "data": "mag_z", "color": self.magzColor, "deriv": True, "fft": True},
                "light": {"label": "Light", "time": "time_light", "data": "light", "color": self.lightColor, "deriv": False, "fft": False},
            },
            "motor": {
                "motor_rpm": {"label": "Motor RPM", "time": "time_rpm", "data": "motor_rpm", "color": self.motorRPMColor, "deriv": True, "fft": True},
                "motor_angle": {"label": "Motor Angle", "time": "time_angle", "data": "motor_angleDeg", "color": self.motorAngleColor, "deriv": True, "fft": True},
                "motor_tilt": {"label": "Motor Tilt", "time": "time_tilt", "data": "motor_tiltDeg", "color": self.motorTiltColor, "deriv": True, "fft": True},
                "encoder_rpm": {"label": "Encoder RPM", "time": "time_encoder_rpm", "data": "encoder_rpm", "color": self.encoderRPMColor, "deriv": True, "fft": True},
                "encoder_angle": {"label": "Encoder Angle", "time": "time_encoder_angle", "data": "encoder_angle", "color": self.encoderAngleColor, "deriv": True, "fft": True},
                "encoder_tilt": {"label": "Encoder Tilt", "time": "time_encoder_tilt", "data": "encoder_tilt", "color": self.encoderTiltColor, "deriv": True, "fft": True},
            },
        }

        self._applySeriesStyles()
        self._bindSeriesCheckboxes()
        self._initCursor()
        if self.graph is not None:
            self.graph.scene().sigMouseClicked.connect(self._onGraphClick)

        if self.spnRangeWidth is not None:
            self.spnRangeWidth.valueChanged.connect(self._applyWidth)
        if self.btnRangeReset is not None:
            self.btnRangeReset.clicked.connect(self._resetRange)

    def _safeGradient(self, values, times):
        if values is None or times is None:
            return None
        if len(values) < 2 or len(times) < 2:
            return None
        return np.gradient(values, times)

    def _prepareGraph(self):
        self.graph.clear()
        self.graph.addLegend()
        self.series = {}
        self._hideAllSeriesCheckboxes()
        self._initCursor()

    def _seriesArrays(self, package, defs):
        series = {}
        for key, meta in defs.items():
            time_values = np.array(getattr(package, meta["time"], []), dtype=np.float64)
            data_values = np.array(getattr(package, meta["data"], []), dtype=np.float64)
            series[key] = (time_values, data_values)
        return series

    def _ordinalSuffix(self, order):
        return "1st" if order == 1 else "2nd"

    def _bindSeriesCheckboxes(self):
        for key, checkbox in self.seriesChecks.items():
            if checkbox is None:
                continue
            checkbox.toggled.connect(lambda checked, k=key: self._onSeriesToggled(k, checked))

    def _applySeriesStyles(self):
        styles = []
        for key, checkbox in self.seriesChecks.items():
            if checkbox is None:
                continue
            color = self.seriesColors.get(key)
            if not color:
                continue
            styles.append(f"QCheckBox#{checkbox.objectName()} {{ color: {color}; }}")
        if styles:
            self.setStyleSheet("\n".join(styles))

    def _setSeriesCheckboxVisible(self, key, visible):
        checkbox = self.seriesChecks.get(key)
        if checkbox is None:
            return
        checkbox.setVisible(visible)

    def _hideAllSeriesCheckboxes(self):
        for key in self.seriesChecks.keys():
            self._setSeriesCheckboxVisible(key, False)

    def _onSeriesToggled(self, key, checked):
        series = self.series.get(key)
        if series is None:
            return
        curve = series.get("curve")
        marker = series.get("marker")
        if curve is not None:
            curve.setVisible(checked)
        if marker is not None and not checked:
            marker.setVisible(False)

    def _plotSeries(self, key, name, x_values, y_values, color):
        if x_values is None or y_values is None:
            return
        if len(x_values) == 0 or len(y_values) == 0:
            return
        self._setSeriesCheckboxVisible(key, True)
        curve = self.graph.plot(x_values, y_values, pen=color, name=name)
        plot_item = self.graph.getPlotItem()
        marker = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(color))
        marker.setVisible(False)
        plot_item.addItem(marker)
        checkbox = self.seriesChecks.get(key)
        if checkbox is not None and not checkbox.isChecked():
            curve.setVisible(False)
        self.series[key] = {
            "x": np.asarray(x_values, dtype=np.float64),
            "y": np.asarray(y_values, dtype=np.float64),
            "marker": marker,
            "curve": curve,
            "name": name,
            "key": key,
        }

    def _initCursor(self):
        plot_item = self.graph.getPlotItem() if self.graph is not None else None
        self.vline = None
        if plot_item is None:
            return
        try:
            self.vline = pg.InfiniteLine(
                angle=90,
                movable=False,
                pen=pg.mkPen(color=(255, 0, 255), width=1, style=pg.QtCore.Qt.PenStyle.DotLine)
            )
            self.vline.setZValue(1000)
            self.vline.setVisible(False)
            plot_item.addItem(self.vline, ignoreBounds=True)
        except Exception:
            self.vline = None

    def _onGraphClick(self, event):
        if self.vline is None:
            return
        try:
            pos = event.scenePos()
            vb = self.graph.getPlotItem().getViewBox()
            data_point = vb.mapSceneToView(pos)
            x_click = float(data_point.x())
            self.vline.setVisible(True)
            self.vline.setPos(x_click)
            highlights = []
            for series in self.series.values():
                xs = series.get("x")
                ys = series.get("y")
                marker = series.get("marker")
                curve = series.get("curve")
                name = series.get("name")
                if xs is None or ys is None or marker is None:
                    continue
                if curve is not None and not curve.isVisible():
                    marker.setVisible(False)
                    continue
                if len(xs) == 0:
                    continue
                idx = np.searchsorted(xs, x_click)
                if idx <= 0:
                    idx = 0
                elif idx >= len(xs):
                    idx = len(xs) - 1
                else:
                    left = idx - 1
                    right = idx
                    if abs(xs[left] - x_click) <= abs(xs[right] - x_click):
                        idx = left
                marker.setData(x=[xs[idx]], y=[ys[idx]])
                marker.setVisible(True)
                if name is not None:
                    color = self.seriesColors.get(series.get("key"), None)
                    color = color or "#ffffff"
                    highlights.append(
                        f"<span style='color:{color}'>"
                        f"{name}: x={xs[idx]:.3f}, y={ys[idx]:.3f}</span>"
                    )
            if self.lblHighlight is not None and highlights:
                self.lblHighlight.setText("Highlighted: " + " | ".join(highlights))
        except Exception:
            pass

    def _syncRangeControls(self):
        if self.spnRangeWidth is None:
            return
        view = self.graph.getViewBox().viewRange()
        x_min, x_max = view[0]
        width = max(0.0, x_max - x_min)
        self.spnRangeWidth.blockSignals(True)
        self.spnRangeWidth.setValue(width)
        self.spnRangeWidth.blockSignals(False)

    def _applyWidth(self):
        if self.spnRangeWidth is None:
            return
        width = self.spnRangeWidth.value()
        if width <= 0:
            return
        view = self.graph.getViewBox().viewRange()
        x_min, x_max = view[0]
        center = (x_min + x_max) / 2.0
        half = width / 2.0
        self.graph.setXRange(center - half, center + half, padding=0)

    def _resetRange(self):
        self.graph.enableAutoRange(axis='x', enable=True)
        self.graph.autoRange()
        self._syncRangeControls()

    def _autoRangeAndSync(self):
        self.graph.enableAutoRange(axis='x', enable=True)
        self.graph.autoRange()
        self._syncRangeControls()

    def performDerivative(self, package, order=1):
        self._prepareGraph()
        if isinstance(package, SmartDotDataPackage):
            defs = self.seriesDefs["smartdot"]
            series = self._seriesArrays(package, defs)
        elif isinstance(package, MotorDataPackage):
            defs = self.seriesDefs["motor"]
            series = self._seriesArrays(package, defs)
            motor_time = series["motor_rpm"][0]
            if len(motor_time) == 0:
                self.graph.setTitle("No motor data available")
                return
        else:
            return

        suffix = f"{self._ordinalSuffix(order)} Deriv"
        for key, meta in defs.items():
            if not meta.get("deriv"):
                continue
            times, values = series.get(key, (None, None))
            deriv = self._safeGradient(values, times)
            if order == 2:
                deriv = self._safeGradient(deriv, times)
            if deriv is None:
                continue
            label = f"{meta['label']} {suffix}"
            self._plotSeries(key, label, times, deriv, meta["color"])

        self._autoRangeAndSync()

    def performFFT(self, package, order=1):
        self._prepareGraph()
        if isinstance(package, SmartDotDataPackage):
            defs = self.seriesDefs["smartdot"]
        elif isinstance(package, MotorDataPackage):
            defs = self.seriesDefs["motor"]
        else:
            return

        series = self._seriesArrays(package, defs)
        if defs is self.seriesDefs["motor"]:
            motor_time = series["motor_rpm"][0]
            if len(motor_time) == 0:
                self.graph.setTitle("No motor data available")
                return

        for key, meta in defs.items():
            if not meta.get("fft"):
                continue
            times, values = series.get(key, (None, None))
            if times is None or values is None:
                continue
            if len(times) <= 1:
                continue
            dt = times[1] - times[0]
            if dt == 0:
                continue
            fft_values = np.fft.rfft(values - np.mean(values))
            freqs = np.fft.rfftfreq(len(times), d=dt)
            label = f"{meta['label']} FFT"
            self._plotSeries(key, label, freqs, np.abs(fft_values), meta["color"])

        self._autoRangeAndSync()
            
        








class AnalysisModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the UI file (module-relative path).
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'AnalysisModePage.ui'), self, package='frontend')
        self.smartDotGraph = self.findChild(SmartDotGraph, 'grphSmartDot')
        self.motorGraph = self.findChild(MotorGraph, 'MotorGraph')
        self.smartDotGraph.setView(0)  # Set SmartDotGraph to show all data
        self.motorGraph.setView(0)     # Set MotorGraph to show all data

        self.btnSave = self.findChild(QtWidgets.QPushButton, 'btnSave')
        self.btnSave.clicked.connect(self.openPostDialog)
        
        self.btnMotorFFT = self.findChild(QtWidgets.QPushButton, 'btnMotorFFT')
        self.btnSmartDotFFT = self.findChild(QtWidgets.QPushButton, 'btnSDFFT')
        self.btnMotorFirstDerivative = self.findChild(QtWidgets.QPushButton, 'btnMotor1DER')
        self.btnSmartDotFirstDerivative = self.findChild(QtWidgets.QPushButton, 'btnSD1DER')
        self.btnMotorSecondDerivative = self.findChild(QtWidgets.QPushButton, 'btnMotor2DER')
        self.btnSmartDotSecondDerivative = self.findChild(QtWidgets.QPushButton, 'btnSD2DER')

        self.btnMotorFFT.clicked.connect(lambda: self.openAnalysisDialog("Motor FFT"))
        self.btnSmartDotFFT.clicked.connect(lambda: self.openAnalysisDialog("SmartDot FFT"))
        self.btnMotorFirstDerivative.clicked.connect(lambda: self.openAnalysisDialog("Motor 1st Derivative"))
        self.btnSmartDotFirstDerivative.clicked.connect(lambda: self.openAnalysisDialog("SmartDot 1st Derivative"))
        self.btnMotorSecondDerivative.clicked.connect(lambda: self.openAnalysisDialog("Motor 2nd Derivative"))
        self.btnSmartDotSecondDerivative.clicked.connect(lambda: self.openAnalysisDialog("SmartDot 2nd Derivative"))

        self.analysisDialog = None
        
        
        
    def openAnalysisDialog(self, type: str):
        if self.analysisDialog is None:
            self.analysisDialog = AnalysisDialog(self, type)
        dialog = self.analysisDialog
        dialog.setWindowTitle(type)
        if dialog.lblTitle is not None:
            dialog.lblTitle.setText(type)

        actions = {
            "Motor FFT": (PackageMotorData, "fft", None),
            "SmartDot FFT": (PackageSmartDotData, "fft", None),
            "Motor 1st Derivative": (PackageMotorData, "deriv", 1),
            "SmartDot 1st Derivative": (PackageSmartDotData, "deriv", 1),
            "Motor 2nd Derivative": (PackageMotorData, "deriv", 2),
            "SmartDot 2nd Derivative": (PackageSmartDotData, "deriv", 2),
        }
        action = actions.get(type)
        if action is None:
            return
        package_cls, mode, order = action
        data_package = package_cls(self, bsc)
        if mode == "fft":
            dialog.performFFT(data_package)
        else:
            dialog.performDerivative(data_package, order=order)
        
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()


    def openPostDialog(self):
        
        dialog = PostDialog(self)
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            print("User accepted the dialog.")
            session_name = dialog.getSessionName()
            print(f"Session Name: {session_name}")
            bsc.get_data_controller().set_session_name(session_name)
            print("Submitting data to cloud")
            bsc.get_data_controller().submit_session_data()
            print("Data submitted to cloud")
            # Handle acceptance (e.g., save data)
        else:
            print("User rejected the dialog.")
            # Handle rejection (e.g., cancel operation)

    def loadData(self):
        dc = bsc.get_data_controller()
        # Update SmartDot graph
        smartdot_package = utils.PackageSmartDotData(self, bsc)
        self.smartDotGraph.updateDataBetter(
            smartdot_package.time_accel, smartdot_package.accel_x, smartdot_package.accel_y, smartdot_package.accel_z,
            smartdot_package.time_gyro, smartdot_package.gyro_x, smartdot_package.gyro_y, smartdot_package.gyro_z,
            smartdot_package.time_mag, smartdot_package.mag_x, smartdot_package.mag_y, smartdot_package.mag_z,
            smartdot_package.time_light, smartdot_package.light
        )

        # Update Motor graph
        motor_package = utils.PackageMotorData(self, bsc)
        self.motorGraph.updateDataDiagnostic(
            motor_package.time_rpm, motor_package.motor_rpm,
            motor_package.time_angle, motor_package.motor_angleDeg,
            motor_package.time_tilt, motor_package.motor_tiltDeg,
            motor_package.time_encoder_rpm, motor_package.encoder_rpm,
            motor_package.time_encoder_angle, motor_package.encoder_angle,
            motor_package.time_encoder_tilt, motor_package.encoder_tilt
        )

if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # Create and show the main window
    window = AnalysisModePage()
    window.setBaseSize(1920, 1080)
    window.setWindowTitle("Analysis Mode Page")
    window.show()

    # Start the event loop
    sys.exit(app.exec())
