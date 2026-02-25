from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
import os
import numpy as np
import pywt
import pyqtgraph as pg

from utils import get_series_defs, series_arrays, SmartDotDataPackage, MotorDataPackage

from .WavletHelperWidget import WavletHelperWidget

class WaveletDialog(QtWidgets.QDialog):
    """Dialog for displaying discrete-wavelet approximations on a tabbed plot.

    The dialog presents the same series checkboxes and range controls as
    ``AnalysisDialog`` but adds a QTabWidget, with one tab per selected
    wavelet plus a residual tab.  Each tab contains its own PlotWidget.  The
    underlying data is assumed to be a regular time sequence (caller must
    already have resampled if necessary).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'WaveletDialog.ui'), self)

        # controls
        self.tabAnalysis = self.findChild(QtWidgets.QTabWidget, 'tabAnalysis')
        self.lblHighlight = self.findChild(QtWidgets.QLabel, 'lblHighlight')
        self.spnRangeWidth = self.findChild(QtWidgets.QDoubleSpinBox, 'spnRangeWidth')
        self.btnRangeReset = self.findChild(QtWidgets.QPushButton, 'btnRangeReset')
        # previously there was a checkbox for detail vs approx; the dialog
        # now always shows detail coefficients
        self.dbbMain = self.findChild(QtWidgets.QDialogButtonBox, 'dbbMain')
        self.dbbMain.accepted.connect(self.accept)
        self.dbbMain.rejected.connect(self.reject)

        # series checkboxes (same names as analysis dialog)
        self.seriesChecks = {
            'accel_x': self.findChild(QtWidgets.QCheckBox, 'chkAccelX'),
            'accel_y': self.findChild(QtWidgets.QCheckBox, 'chkAccelY'),
            'accel_z': self.findChild(QtWidgets.QCheckBox, 'chkAccelZ'),
            'gyro_x': self.findChild(QtWidgets.QCheckBox, 'chkGyroX'),
            'gyro_y': self.findChild(QtWidgets.QCheckBox, 'chkGyroY'),
            'gyro_z': self.findChild(QtWidgets.QCheckBox, 'chkGyroZ'),
            'mag_x': self.findChild(QtWidgets.QCheckBox, 'chkMagX'),
            'mag_y': self.findChild(QtWidgets.QCheckBox, 'chkMagY'),
            'mag_z': self.findChild(QtWidgets.QCheckBox, 'chkMagZ'),
            'light': self.findChild(QtWidgets.QCheckBox, 'chkLight'),
            'motor_rpm': self.findChild(QtWidgets.QCheckBox, 'chkMotorRPM'),
            'motor_angle': self.findChild(QtWidgets.QCheckBox, 'chkMotorAngle'),
            'motor_tilt': self.findChild(QtWidgets.QCheckBox, 'chkMotorTilt'),
            'encoder_rpm': self.findChild(QtWidgets.QCheckBox, 'chkEncoderRPM'),
            'encoder_angle': self.findChild(QtWidgets.QCheckBox, 'chkEncoderAngle'),
            'encoder_tilt': self.findChild(QtWidgets.QCheckBox, 'chkEncoderTilt'),
        }

        # copy color definitions similar to AnalysisDialog so that
        # series_defs produced by get_series_defs have valid colors.
        self.accxColor = "#ff0000"  # red
        self.accyColor = "#00aa00"  # green
        self.acczColor = "#0000ff"  # blue
        self.gyroxColor = "#00ffff"  # cyan
        self.gyroyColor = "#ff00ff"  # magenta
        self.gyrozColor = "#ffff00"  # yellow
        self.magxColor = "#008080"  # teal
        self.magyColor = "#800000"  # maroon
        self.magzColor = "#800080"  # purple
        self.lightColor = "#777777"  # gray

        self.motorRPMColor = "#ff0000"  # red
        self.motorAngleColor = "#00aa00"  # green
        self.motorTiltColor = "#0000ff"  # blue
        self.encoderRPMColor = "#00ffff"  # cyan
        self.encoderAngleColor = "#ff00ff"  # magenta
        self.encoderTiltColor = "#ffff00"  # yellow

        self.seriesColors = getattr(parent, 'seriesColors', {})
        self.seriesDefs = get_series_defs(self)

        self.graphs = []             # list of PlotWidgets (one per tab)
        self.series_per_graph = {}    # graph -> {key: metadata}
        self.vlines = {}              # graph -> InfiniteLine or None
        # additional state for final "original" tab
        self.final_graph = None       # reference to the last tab's PlotWidget
        self.wave_checkboxes = {}     # wave_name -> QCheckBox added below graph
        self._wave_results = {}       # copy of most recent wavelet results

        self._bindSeriesCheckboxes()
        self._applySeriesStyles()
        self._initCursorAll()

        if self.spnRangeWidth is not None:
            self.spnRangeWidth.valueChanged.connect(self._applyWidth)
        if self.btnRangeReset is not None:
            self.btnRangeReset.clicked.connect(self._resetRange)
        if self.tabAnalysis is not None:
            self.tabAnalysis.currentChanged.connect(self._syncRangeControls)


    # ------------------------------------------------------------------
    # lower-level helpers
    # ------------------------------------------------------------------
    def _plotSeriesOnGraph(self, graph, key, name, x_values, y_values, color):
        if graph is None or x_values is None or y_values is None:
            return
        if len(x_values) == 0 or len(y_values) == 0:
            return
        checkbox = self.seriesChecks.get(key)
        if checkbox is None:
            return
        checkbox.setVisible(True)
        curve = graph.plot(x_values, y_values, pen=color, name=name)
        plot_item = graph.getPlotItem()
        marker = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(color))
        marker.setVisible(False)
        plot_item.addItem(marker)
        if not checkbox.isChecked():
            curve.setVisible(False)
        self.series_per_graph.setdefault(graph, {})[key] = {
            'x': np.asarray(x_values, dtype=np.float64),
            'y': np.asarray(y_values, dtype=np.float64),
            'marker': marker,
            'curve': curve,
            'name': name,
            'key': key,
        }

    def _prepareTabs(self):
        # clear existing graphs; tabs will be re-added by caller
        self.graphs.clear()
        self.series_per_graph.clear()
        self.vlines.clear()
        self.tabAnalysis.clear()
        # wipe any previous final-tab state too
        self.final_graph = None
        self.wave_checkboxes.clear()
        # do not clear _wave_results here; caller will update it after
        # hide all series checkboxes until we plot something
        for chk in self.seriesChecks.values():
            if chk is not None:
                chk.setVisible(False)

    def _addTab(self, title):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        graph = pg.PlotWidget()
        graph.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                             QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addWidget(graph)
        w.setLayout(layout)
        self.tabAnalysis.addTab(w, title)
        self.graphs.append(graph)
        # attach a vline for this graph
        self._initCursor(graph)
        return graph

    def _initCursor(self, graph):
        if graph is None:
            return
        plot_item = graph.getPlotItem()
        try:
            vline = pg.InfiniteLine(angle=90, movable=False,
                                    pen=pg.mkPen(color=(255,0,255), width=1,
                                                 style=pg.QtCore.Qt.PenStyle.DotLine))
            vline.setZValue(1000)
            vline.setVisible(False)
            plot_item.addItem(vline, ignoreBounds=True)
            self.vlines[graph] = vline
            graph.scene().sigMouseClicked.connect(lambda ev, g=graph: self._onGraphClick(ev, g))
        except Exception:
            self.vlines[graph] = None

    def _initCursorAll(self):
        for graph in self.graphs:
            self._initCursor(graph)

    def _onGraphClick(self, event, graph):
        vline = self.vlines.get(graph)
        if vline is None:
            return
        try:
            pos = event.scenePos()
            vb = graph.getPlotItem().getViewBox()
            data_point = vb.mapSceneToView(pos)
            x_click = float(data_point.x())
            vline.setVisible(True)
            vline.setPos(x_click)
            highlights = []
            series = self.series_per_graph.get(graph, {})
            for s in series.values():
                xs = s.get('x')
                ys = s.get('y')
                marker = s.get('marker')
                curve = s.get('curve')
                name = s.get('name')
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
                    color = self.seriesColors.get(s.get('key'), '#ffffff')
                    highlights.append(f"<span style='color:{color}'>{name}: x={xs[idx]:.3f}, y={ys[idx]:.3f}</span>")
            if self.lblHighlight is not None and highlights:
                self.lblHighlight.setText("Highlighted: " + " | ".join(highlights))
        except Exception:
            pass

    def _bindSeriesCheckboxes(self):
        for key, checkbox in self.seriesChecks.items():
            if checkbox is None:
                continue
            checkbox.toggled.connect(lambda checked, k=key: self._onSeriesToggled(k, checked))

    def _onSeriesToggled(self, key, checked):
        for graph in self.graphs:
            series = self.series_per_graph.get(graph, {})
            s = series.get(key)
            if s is None:
                continue
            curve = s.get('curve')
            marker = s.get('marker')
            if curve is not None:
                curve.setVisible(checked)
            if marker is not None and not checked:
                marker.setVisible(False)

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

    def _syncRangeControls(self):
        if self.spnRangeWidth is None:
            return
        graph = self.currentGraph()
        if graph is None:
            return
        view = graph.getViewBox().viewRange()
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
        graph = self.currentGraph()
        if graph is None:
            return
        view = graph.getViewBox().viewRange()
        x_min, x_max = view[0]
        center = (x_min + x_max) / 2.0
        half = width / 2.0
        graph.setXRange(center - half, center + half, padding=0)

    def _resetRange(self):
        graph = self.currentGraph()
        if graph is None:
            return
        graph.enableAutoRange(axis='x', enable=True)
        graph.autoRange()
        self._syncRangeControls()

    def _updateFinalGraph(self):
        graph = self.final_graph
        if graph is None:
            return
        series = self.series_per_graph.get(graph, {})
        # determine which waves are toggled
        active_waves = [w for w, chk in self.wave_checkboxes.items() if chk.isChecked()]
        for key, s in series.items():
            orig = s.get('orig_y')
            curve = s.get('curve')
            xs = s.get('x')
            if orig is None or curve is None or xs is None:
                continue
            y = orig.copy()
            # subtract each active wave detail if available
            for w in active_waves:
                details = self._wave_results.get(key, (None, {}))[1]
                detail = details.get(w)
                if detail is not None and len(detail) == len(y):
                    y = y - detail
            curve.setData(x=xs, y=y)
        # ensure the updated values are drawn immediately
        try:
            graph.repaint()
        except Exception:
            pass


    def _autoRangeAndSync(self):
        for graph in self.graphs:
            graph.enableAutoRange(axis='x', enable=True)
            graph.autoRange()
        self._syncRangeControls()

    def _format_wave_name(self, wave, order, isolate_high=False, isolate_low=False):
        # return a name suitable for labeling a tab or checkbox.  include
        # dyadic order annotations and optional isolation flags so that
        # callers can distinguish "db4@2" from "db4@2+high" etc.
        try:
            o = int(order)
        except Exception:
            o = 0
        if o <= 0:
            base = wave
        else:
            base = f"{wave}@{o}"
        if isolate_high:
            base += "+high"
        if isolate_low:
            base += "+low"
        return base

    def _computeWaveletDetail(self, arr, wave, order,isolate_high=False, isolate_low=False):
        # normalize parameters
        print(f"Computing wavelet detail: wave={wave}, order={order}, isolate_high={isolate_high}, isolate_low={isolate_low}")
        if arr is None or wave is None:
            return None, None
        name = self._format_wave_name(wave, order,isolate_high=isolate_high, isolate_low=isolate_low)
        try:
            coeffs = pywt.wavedec(arr, wave, level=order)
            print(len(coeffs), "coefficients computed for wavelet detail")
            print(f"  coeffs lengths: {[len(c) for c in coeffs]}")
            if not coeffs or len(coeffs) < 2:
                return name, None
            if isolate_high:
                for i in range(len(coeffs) - 1):
                    coeffs[i] = np.zeros_like(coeffs[i])
            if isolate_low:
                coeffs[-1] = np.zeros_like(coeffs[-1])
            output = pywt.waverec(coeffs, wave)
        except Exception as e:
            # log the error so callers (and tests) can see why we failed
            print(f"_computeWaveletDetail exception: {e}")
            output = None

        # normalize returned array length to match input
        if output is not None:
            out_arr = np.asarray(output, dtype=np.float64)
            if len(out_arr) > len(arr):
                out_arr = out_arr[: len(arr)]
            elif len(out_arr) < len(arr):
                out_arr = np.pad(out_arr, (0, len(arr) - len(out_arr)), mode='edge')
            output = out_arr
        return name, output

    def _parse_wavelet_input(self, wavelet):
        if wavelet is None:
            return None
        def to_order(val):
            # try to interpret as number
            try:
                fl = float(val)
            except Exception:
                return 0
            # if it's not a whole integer, treat it as legacy scale and map via log2
            if not float(fl).is_integer():
                try:
                    return max(0, int(round(np.log2(fl))))
                except Exception:
                    return 0
            # otherwise simply convert to int (clamp to non-negative)
            return max(0, int(fl))
        out = []
        if isinstance(wavelet, dict):
            w = wavelet.get('type') or wavelet.get('wave')
            if not w:
                return []
            if 'order' in wavelet:
                o = to_order(wavelet['order'])
            else:
                # legacy scale key
                o = to_order(wavelet.get('scale', 1))
            out.append({'type': w, 'order': o})
        elif isinstance(wavelet, (tuple, list)):
            if wavelet:
                w = wavelet[0]
                o = to_order(wavelet[1]) if len(wavelet) > 1 else 0
                out.append({'type': w, 'order': o})
        else:
            out.append({'type': wavelet, 'order': 0})
        return out


    def currentGraph(self):
        idx = self.tabAnalysis.currentIndex()
        if idx < 0 or idx >= len(self.graphs):
            return None
        return self.graphs[idx]


    # ------------------------------------------------------------------
    # public methods
    # ------------------------------------------------------------------
    def _computeWaveletResults(self, package, wave_list):
        # choose the correct series definitions for the package type
        if isinstance(package, SmartDotDataPackage):
            defs = self.seriesDefs['smartdot']
        elif isinstance(package, MotorDataPackage):
            defs = self.seriesDefs['motor']
            motor_time = getattr(package, defs['motor_rpm']['time'], [])
            if len(motor_time) == 0:
                self.setWindowTitle("No motor data available")
                return defs, {}, {}
        else:
            # fall back on attribute detection used previously
            if hasattr(package, 'accel_x'):
                defs = self.seriesDefs['smartdot']
            else:
                defs = self.seriesDefs['motor']
        
        series = series_arrays(package, defs)
        wave_results = {}

        for key, meta in defs.items():
            if key == 'light':
                continue
            times, values = series.get(key, (None, None))
            if times is None or values is None or len(values) == 0:
                continue
            arr = np.asarray(values, dtype=np.float64)
            details = {}
            for entry in wave_list:
                w = entry.get('type')
                order = entry.get('order', 0)
                high_flag = bool(entry.get('isolate_high', False))
                low_flag = bool(entry.get('isolate_low', False))
                name, detail = self._computeWaveletDetail(
                    arr, w, order,
                    isolate_high=high_flag,
                    isolate_low=low_flag
                )
                if name is None:
                    continue
                details[name] = detail
            if details:
                wave_results[key] = (times, details)

        return defs, series, wave_results

    def _plotWaveletResults(self, defs, series, wave_results, wave_list):
        if not wave_results:
            self._prepareTabs()
            graph = self._addTab('No data')
            graph.setTitle('No time series data available for wavelet analysis')
            return False

        # hide extreme series if necessary
        # compute peak magnitude per series, ignoring None entries
        peaks = {}
        for k, (_, dic) in wave_results.items():
            vals = []
            for w, arr in dic.items():
                if arr is None:
                    continue
                try:
                    vals.append(np.nanmax(np.abs(arr)))
                except Exception:
                    pass
            if vals:
                peaks[k] = max(vals)
            else:
                peaks[k] = 0
        if len(peaks) > 1:
            sorted_items = sorted(peaks.items(), key=lambda kv: kv[1], reverse=True)
            top_key, top_val = sorted_items[0]
            second_val = sorted_items[1][1]
            if second_val > 0 and top_val / second_val > 1000:
                chk = self.seriesChecks.get(top_key)
                if chk is not None and chk.isChecked():
                    chk.setChecked(False)

        self._prepareTabs()
        self._wave_results = wave_results
        # preserve isolation flags when generating labels for plot tabs
        wave_names = [self._format_wave_name(
                          e['type'], e.get('order', 0),
                          isolate_high=bool(e.get('isolate_high', False)),
                          isolate_low=bool(e.get('isolate_low', False)))
                      for e in wave_list]
        for wave_name in wave_names:
            graph = self._addTab(wave_name)
            for key, (t, dic) in wave_results.items():
                detail = dic.get(wave_name)
                if detail is None:
                    continue
                label = f"{defs[key]['label']} detail ({wave_name})"
                color = defs[key].get('color') or "#E5E7EB"
                self._plotSeriesOnGraph(graph, key, label, t, detail, color)

        # final original-data tab
        graph = self._addTab('Original')
        self.final_graph = graph
        for key, (t, vals) in series.items():
            if key == 'light':
                continue
            if t is None or vals is None:
                continue
            label = defs.get(key, {}).get('label', key)
            color = defs.get(key, {}).get('color') or "#E5E7EB"
            self._plotSeriesOnGraph(graph, key, label, t, vals, color)
            entry = self.series_per_graph.get(graph, {}).get(key)
            if entry is not None:
                entry['orig_y'] = np.asarray(vals, dtype=np.float64)
        tab_widget = self.tabAnalysis.widget(self.tabAnalysis.count() - 1)
        if tab_widget is not None:
            layout = tab_widget.layout()
            if layout is not None:
                hbox = QtWidgets.QHBoxLayout()
                for wave_name in wave_names:
                    chk = QtWidgets.QCheckBox(wave_name)
                    chk.setChecked(False)
                    chk.toggled.connect(lambda checked, w=wave_name: self._updateFinalGraph())
                    hbox.addWidget(chk)
                    self.wave_checkboxes[wave_name] = chk
                layout.addLayout(hbox)

        self._autoRangeAndSync()
        if self.tabAnalysis.count() > 0:
            self.tabAnalysis.setCurrentIndex(0)
        return True

    def _prepareWaveletList(self, wavelet):
        # explicit argument takes precedence
        if wavelet is not None:
            return self._parse_wavelet_input(wavelet) or []

        # otherwise prompt the user
        helper = WavletHelperWidget(self)
        if helper.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            self.setWindowTitle("Wavelet cancelled")
            return []
        lst = helper.get_list()
        if not lst:
            self.setWindowTitle("No wavelets selected")
            return []

        out = []
        for entry in lst:
            if entry.get('type'):
                entry_dict = {'type': entry['type'],
                              'order': int(entry.get('order', 0)),
                              'isolate_high': bool(entry.get('isolate_high', False)),
                              'isolate_low': bool(entry.get('isolate_low', False))}
                out.append(entry_dict)
                print("_prepareWaveletList entry:", entry_dict)
        if not out:
            self.setWindowTitle("No valid wavelets selected")
        return out

    def performWavelet(self, package, wavelet=None):
        self.current_package = package
        # always query for a fresh list; no caching of the previous choice
        wave_list = self._prepareWaveletList(wavelet)
        defs, series, wave_results = self._computeWaveletResults(package, wave_list)
        return self._plotWaveletResults(defs, series, wave_results, wave_list)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dlg = WaveletDialog()
    dlg.show()
    sys.exit(app.exec())
