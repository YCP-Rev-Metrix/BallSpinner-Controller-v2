from PyQt6 import QtWidgets, uic
import os
import sys
from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCursor
import datetime as dt
import pyqtgraph as pg
from backend.models.EncoderData import EncoderDataInstance
from backend.models.HeatData import HeatDataInstance
from backend.models.SessionData import SessionData
from frontend.MotorTest import CharacterizeMotors, tune_duty_cycle_scale
from BSC import bsc


class MotorTestGraphDialog(QtWidgets.QDialog):
    """Display motor test results in a tabbed plot layout."""

    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Motor Test Results")
        self.resize(900, 650)

        layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        for r in results:
            speed = r.get("target_speed")
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)

            time_to_target = r.get("time_to_target")
            overshoot = r.get("overshoot")
            target_speed = r.get("target_speed")
            overshoot_pct = None
            if target_speed and target_speed != 0:
                # Show overshoot as percentage of the target speed.
                # (e.g., overshoot=181 on target=250 → 72.4%)
                overshoot_pct = (overshoot / target_speed) * 100

            def fmt_value(val):
                return f"{val:.2f}" if isinstance(val, (int, float)) else str(val)

            stats_items = []
            stats_items.append(
                f"Time to target: {fmt_value(time_to_target)}" if time_to_target is not None else "Time to target: n/a"
            )
            if overshoot is not None:
                stats_items.append(f"Overshoot: {fmt_value(overshoot)}")
            if overshoot_pct is not None:
                stats_items.append(f"Overshoot %: {fmt_value(overshoot_pct)}")

            analysis = r.get('analysis', {}) or {}
            if analysis:
                analysis_items = [
                    f"min_speed: {fmt_value(analysis.get('min_speed', 'n/a'))}",
                    f"max_speed: {fmt_value(analysis.get('max_speed', 'n/a'))}",
                    f"mean_speed: {fmt_value(analysis.get('mean_speed', 'n/a'))}",
                    f"median_speed: {fmt_value(analysis.get('median_speed', 'n/a'))}",
                    f"std_dev: {fmt_value(analysis.get('standard_deviation', 'n/a'))}",
                    f"variance: {fmt_value(analysis.get('variance', 'n/a'))}",
                    f"avg_error: {fmt_value(analysis.get('average_error', 'n/a'))}",
                    f"avg_abs_error: {fmt_value(analysis.get('average_abs_error', 'n/a'))}",
                    f"max_error: {fmt_value(analysis.get('max_error', 'n/a'))}",
                    f"min_error: {fmt_value(analysis.get('min_error', 'n/a'))}",
                ]
                stats_items.append("Analysis:")
                stats_items.extend(analysis_items)

            grouped_lines = []
            i = 0
            while i < len(stats_items):
                group = stats_items[i:i+5]
                if i == 0 and len(group) == 1 and group[0].startswith("Time to target"):
                    # Keep the first label alone for clarity when non-analysis only
                    grouped_lines.append(group[0])
                else:
                    # Combine up to 5 items per line
                    grouped_lines.append(" | ".join(group))
                i += 5

            stats_text = "\n".join(grouped_lines)
            stats_label = QtWidgets.QLabel(stats_text)
            stats_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            stats_label.setStyleSheet("font-weight: bold;")
            tab_layout.addWidget(stats_label)

            plot = pg.PlotWidget()
            plot.setBackground("w")
            plot.plot(
                r.get("timestamps", []),
                r.get("current_speeds", []),
                pen=pg.mkPen(color="#0077cc", width=2),
                name="Measured",
            )
            plot.plot(
                r.get("timestamps", []),
                r.get("target_speeds", []),
                pen=pg.mkPen(color="#cc0000", width=1, style=QtCore.Qt.PenStyle.DashLine),
                name="Target",
            )
            plot.setLabel("left", "Speed")
            plot.setLabel("bottom", "Time (s)")
            plot.addLegend()

            # Add cursor readout and an interactive vertical line + marker
            cursor_label = QtWidgets.QLabel("Cursor: t=N/A, measured=N/A, target=N/A")
            tab_layout.addWidget(cursor_label)

            plot_item = plot.getPlotItem()
            vline = pg.InfiniteLine(angle=90, movable=False,
                                     pen=pg.mkPen(color=(255, 0, 255), width=1, style=QtCore.Qt.PenStyle.DotLine))
            vline.setVisible(False)
            plot_item.addItem(vline, ignoreBounds=True)

            marker = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255, 0, 255))
            marker.setVisible(False)
            plot_item.addItem(marker)

            plot.scene().sigMouseClicked.connect(
                lambda event, p=plot, v=vline, m=marker, l=cursor_label,
                       ts=r.get("timestamps", []), cs=r.get("current_speeds", []),
                       tg=r.get("target_speeds", []): self._on_motor_test_graph_click(event, p, v, m, l, ts, cs, tg)
            )

            tab_layout.addWidget(plot)
            tabs.addTab(tab, f"{speed}")

        btn_export = QtWidgets.QPushButton("Export to PNG")
        btn_export.clicked.connect(self._export_to_png)
        layout.addWidget(btn_export)

        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _export_to_png(self):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select folder to export all graphs",
            "",
            QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )
        if not dir_path:
            return

        failed = []
        for idx in range(self.tabs.count()):
            tab_text = self.tabs.tabText(idx)
            tab = self.tabs.widget(idx)
            plot_widget = tab.findChild(pg.PlotWidget)
            if plot_widget is None:
                continue

            pixmap = plot_widget.grab()
            sanitized_speed = tab_text.replace('/', '_').replace(' ', '_')
            tab_filename = os.path.join(dir_path, f"motor_test_{sanitized_speed}.png")
            if not pixmap.save(tab_filename, 'PNG'):
                failed.append(tab_filename)

        # Save the whole dialog as well
        full_filename = os.path.join(dir_path, "motor_test_full_dialog.png")
        if not self.grab().save(full_filename, 'PNG'):
            failed.append(full_filename)

        if failed:
            QtWidgets.QMessageBox.warning(
                self,
                "Export Completed with Errors",
                f"Some files could not be saved:\n" + "\n".join(failed),
            )
        else:
            QtWidgets.QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {self.tabs.count()} graph images + full snapshot to {dir_path}",
            )

    def _on_motor_test_graph_click(self, event, plot, vline, marker, cursor_label, timestamps, current_speeds, target_speeds):
        try:
            pos = event.scenePos()
            vb = plot.getPlotItem().getViewBox()
            data_point = vb.mapSceneToView(pos)
            x_click = float(data_point.x())

            if not timestamps:
                return

            idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - x_click))
            t = timestamps[idx]
            measured = current_speeds[idx] if idx < len(current_speeds) else None
            target = target_speeds[idx] if idx < len(target_speeds) else None

            if measured is not None and target is not None:
                cursor_label.setText(f"Cursor: t={t:.3f}s, measured={measured:.2f}, target={target:.2f}")
            elif measured is not None:
                cursor_label.setText(f"Cursor: t={t:.3f}s, measured={measured:.2f}, target=N/A")
            else:
                cursor_label.setText(f"Cursor: t={t:.3f}s, measured=N/A, target=N/A")

            if vline is not None:
                vline.setPos(t)
                vline.setVisible(True)

            if marker is not None and measured is not None:
                marker.setData(x=[t], y=[measured])
                marker.setVisible(True)

        except Exception as e:
            print("MotorTestGraphDialog cursor error:", e)


class TuneScaleDialog(QtWidgets.QDialog):
    """Show tuning results (scale vs overshoot) in a simple graph."""

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duty Cycle Scale Tuning")
        self.resize(800, 600)

        layout = QtWidgets.QVBoxLayout(self)

        best = data.get("best")
        if best:
            best_label = QtWidgets.QLabel(
                f"Best scale: {best['scale']:.9f} | abs overshoot: {best['abs_overshoot']:.2f}"
            )
        else:
            best_label = QtWidgets.QLabel("No best scale found")
        best_label.setStyleSheet("font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(best_label)

        plot = pg.PlotWidget()
        plot.setBackground("w")
        plot.setLabel("bottom", "Scale")
        plot.setLabel("left", "Overshoot")

        scales = [r["scale"] for r in data.get("results", [])]
        overshoots = [r["overshoot"] for r in data.get("results", [])]
        abs_overshoots = [r["abs_overshoot"] for r in data.get("results", [])]

        plot.plot(scales, overshoots, pen=pg.mkPen(color="#0077cc", width=2), name="Overshoot")
        plot.plot(
            scales,
            abs_overshoots,
            pen=pg.mkPen(color="#cc0000", width=2, style=QtCore.Qt.PenStyle.DashLine),
            name="Abs Overshoot",
        )

        if best:
            plot.plot(
                [best["scale"]],
                [best["overshoot"]],
                pen=None,
                symbol="o",
                symbolBrush="#00aa00",
                symbolSize=12,
                name="Best",
            )

        plot.addLegend()
        layout.addWidget(plot)

        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class _PrintCapture(QtCore.QObject):
    """Capture stdout/stderr and emit it into a Qt signal."""

    newText = QtCore.pyqtSignal(str)

    def write(self, text: str):
        if text:
            self.newText.emit(text)

    def flush(self):
        pass


class MotorTestWorker(QtCore.QThread):
    """Worker thread that runs CharacterizeMotors() and streams output."""

    newText = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, bsc, hold_time=None, parent=None):
        super().__init__(parent)
        self._bsc = bsc
        self._hold_time = hold_time

    def run(self):
        old_out, old_err = sys.stdout, sys.stderr
        capture = _PrintCapture()
        capture.newText.connect(self.newText)
        sys.stdout = capture
        sys.stderr = capture

        try:
            results = CharacterizeMotors(None, self._bsc, hold_time=self._hold_time)
            self.finished.emit(results)
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            sys.stdout = old_out
            sys.stderr = old_err


class MotorTuneWorker(QtCore.QThread):
    """Worker thread that runs tune_duty_cycle_scale() and streams output."""

    newText = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, bsc, parent=None):
        super().__init__(parent)
        self._bsc = bsc

    def run(self):
        old_out, old_err = sys.stdout, sys.stderr
        capture = _PrintCapture()
        capture.newText.connect(self.newText)
        sys.stdout = capture
        sys.stderr = capture

        try:
            results = tune_duty_cycle_scale(None, self._bsc)
            self.finished.emit(results)
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            sys.stdout = old_out
            sys.stderr = old_err

class CloudTest(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'cloudTest.ui'), self, package='frontend')
        
        # Connect button signals to their respective functions (Hungarian names)
        self.findChild(QtWidgets.QPushButton, 'btnAskCloudForSix').clicked.connect(self.ask_cloud_for_6)
        self.findChild(QtWidgets.QPushButton, 'btnClearLabel').clicked.connect(self.clear_label)
        self.findChild(QtWidgets.QPushButton, 'btnGetSessions').clicked.connect(self.get_sessions)
        self.findChild(QtWidgets.QPushButton, 'btnPostSmartDotData').clicked.connect(self.post_smart_dot_data)
        self.findChild(QtWidgets.QPushButton, 'btnGetSmartDotData').clicked.connect(self.get_smart_dot_data)
        self.findChild(QtWidgets.QPushButton, 'btnGetDiagnosticData').clicked.connect(self.get_diagnostic_data)
        self.findChild(QtWidgets.QPushButton, 'btnPostDiagnosticData').clicked.connect(self.post_diagnostic_data)
        self.findChild(QtWidgets.QPushButton, 'btnPostShotScriptData').clicked.connect(self.post_shot_script_data)
        self.findChild(QtWidgets.QPushButton, 'btnGetShotScriptData').clicked.connect(self.get_shot_script_data)
        self.findChild(QtWidgets.QPushButton, 'btnPostEncoderData').clicked.connect(self.post_encoder_data)
        self.findChild(QtWidgets.QPushButton, 'btnGetEncoderData').clicked.connect(self.get_encoder_data)
        self.findChild(QtWidgets.QPushButton, 'btnPostHeatData').clicked.connect(self.post_heat_data)
        self.findChild(QtWidgets.QPushButton, 'btnGetHeatData').clicked.connect(self.get_heat_data)
        self.findChild(QtWidgets.QPushButton, 'btnSubmitAllData').clicked.connect(self.submit_all_data)
        self.findChild(QtWidgets.QPushButton, 'btnLoadSessionData').clicked.connect(self.load_session_data_from_cloud)
        self.errorButton = self.findChild(QtWidgets.QPushButton, 'btnGenError')
        self.errorButton.clicked.connect(self.generate_error)
        self.cloud_api = bsc.get_cloud_api()

        self.btnSpinDiagnosticData = self.findChild(QtWidgets.QPushButton, 'btnSpinDiag')
        self.btnSpinDiagnosticData.clicked.connect(self.spin_diagnostic_data)
        self.btnTuneScale = self.findChild(QtWidgets.QPushButton, 'btnTuneScale')
        self.btnTuneScale.clicked.connect(self.tune_duty_cycle_scale)
        self.btnStepperDiagnosticData = self.findChild(QtWidgets.QPushButton, 'btnStepDiag')
        self.btnStepperDiagnosticData.clicked.connect(self.stepper_diagnostic_data)

        # Motor parameter controls
        self.spnKp = self.findChild(QtWidgets.QDoubleSpinBox, 'spnKp')
        self.spnKi = self.findChild(QtWidgets.QDoubleSpinBox, 'spnKi')
        self.spnKd = self.findChild(QtWidgets.QDoubleSpinBox, 'spnKd')
        self.spnDutyScale = self.findChild(QtWidgets.QDoubleSpinBox, 'spnDutyScale')
        self.btnApplyMotorParams = self.findChild(QtWidgets.QPushButton, 'btnApplyMotorParams')
        self.btnApplyMotorParams.clicked.connect(self.apply_motor_params)

        # Default to the current motor1 configuration
        self.spnKp.setValue(bsc.motor1.Kp)
        self.spnKi.setValue(getattr(bsc.motor1, 'Ki', 0.0))
        self.spnKd.setValue(getattr(bsc.motor1, 'Kd', 0.0))
        self.spnDutyScale.setValue(bsc.motor1.duty_cycle_scale)

    def spin_diagnostic_data(self):
        """Run the motor diagnostic and show a live log dialog while it runs."""

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Spin Diagnostic Output")
        dialog.setMinimumSize(650, 400)

        layout = QtWidgets.QVBoxLayout(dialog)
        text_edit = QtWidgets.QTextEdit()
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        btn_close = QtWidgets.QPushButton("Close")
        btn_close.setEnabled(False)
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        test_duration = self.findChild(QtWidgets.QSpinBox, 'spnTestDuration').value()
        worker = MotorTestWorker(bsc, hold_time=test_duration, parent=self)
        worker.newText.connect(lambda t: text_edit.moveCursor(QTextCursor.MoveOperation.End) or text_edit.insertPlainText(t))

        def _fmt(value):
            return f"{value:.2f}" if isinstance(value, (int, float)) else str(value)

        def _on_finished(results):
            summary = f"Ran {len(results)} speeds, last runtime={results[-1]['runtime']:.2f}s\n"
            text_edit.append(summary)
            self.findChild(QtWidgets.QLabel, 'lblResponse').setText(summary)

            # Add per-speed analysis summary into popup text
            for r in results:
                analysis = r.get('analysis', {}) or {}
                if analysis:
                    analysis_str = (
                        f"Speed {r.get('target_speed')}: "
                        f"min={_fmt(analysis.get('min_speed', 'n/a'))} "
                        f"max={_fmt(analysis.get('max_speed', 'n/a'))} "
                        f"mean={_fmt(analysis.get('mean_speed', 'n/a'))} "
                        f"overshoot={_fmt(r.get('overshoot', 'n/a'))}\n"
                    )
                else:
                    analysis_str = (
                        f"Speed {r.get('target_speed')}: analysis not available\n"
                    )
                text_edit.append(analysis_str)

            btn_close.setEnabled(True)

            graph_dialog = MotorTestGraphDialog(results, parent=self)
            graph_dialog.exec()

        def _on_failed(error_text):
            text_edit.append(f"ERROR: {error_text}\n")
            btn_close.setEnabled(True)

        worker.finished.connect(_on_finished)
        worker.failed.connect(_on_failed)
        worker.start()

        dialog.exec()

    def tune_duty_cycle_scale(self):
        """Run the duty-cycle-scale tuning routine and show graphs + best result."""

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Scale Tuning Output")
        dialog.setMinimumSize(650, 400)

        layout = QtWidgets.QVBoxLayout(dialog)
        text_edit = QtWidgets.QTextEdit()
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        btn_close = QtWidgets.QPushButton("Close")
        btn_close.setEnabled(False)
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        worker = MotorTuneWorker(bsc, parent=self)
        worker.newText.connect(lambda t: text_edit.moveCursor(QTextCursor.MoveOperation.End) or text_edit.insertPlainText(t))

        def _on_finished(results):
            if not results:
                text_edit.append("No tuning results returned.\n")
                btn_close.setEnabled(True)
                return

            best = results.get("best")
            if best:
                text_edit.append(
                    f"Best scale: {best['scale']:.9f} (abs overshoot: {best['abs_overshoot']:.2f})\n"
                )

            graph_dialog = TuneScaleDialog(results, parent=self)
            graph_dialog.exec()

            btn_close.setEnabled(True)

        def _on_failed(error_text):
            text_edit.append(f"ERROR: {error_text}\n")
            btn_close.setEnabled(True)

        worker.finished.connect(_on_finished)
        worker.failed.connect(_on_failed)
        worker.start()

        dialog.exec()

    def stepper_diagnostic_data(self):
        print("Stepper Diagnostic Data clicked")
        # Simulate stepper diagnostic data by updating the label with changing values

    def apply_motor_params(self):
        """Apply Kp and duty cycle scale from the UI to motor1."""
        try:
            kp = self.spnKp.value()
            ki = self.spnKi.value()
            kd = self.spnKd.value()
            scale = self.spnDutyScale.value()
            bsc.motor1.Kp = kp
            if hasattr(bsc.motor1, 'Ki'):
                bsc.motor1.Ki = ki
            if hasattr(bsc.motor1, 'Kd'):
                bsc.motor1.Kd = kd
            bsc.motor1.duty_cycle_scale = scale
            self.findChild(QtWidgets.QLabel, 'lblResponse').setText(
                f"Applied Kp={kp:.3f}, Ki={ki:.3f}, Kd={kd:.3f}, duty_scale={scale:.9f}"
            )
        except Exception as e:
            self.findChild(QtWidgets.QLabel, 'lblResponse').setText(f"Error: {e}")
            print(e)


    def generate_error(self):
        """Handle the 'Generate Error' button click"""
        print("Generate Error clicked")
        # Intentionally cause a division by zero error to test error handling and logging
        raise ValueError("This is a test error generated by the 'Generate Error' button. \n This should be caught and logged by the application's error handling mechanism.")


    def ask_cloud_for_6(self):
        """Handle the 'Ask Cloud for 6' button click"""
        #Ask the cloud for the test data
        # status_code, data = self.cloud_api.api_get_test_data()
        data = SessionData(id=-1,timeStamp=dt.datetime.now().isoformat(), name="Test Session", isShotMode=True)
        

        result = self.cloud_api.post_session_data(data)
        print(result)
        # if status_code == 200:
        #     self.label.setText(str(data))
        # else:
        #     self.label.setText("Error: " + data)
    
    def clear_label(self):
        """Handle the 'Clear Label' button click"""
        # Clear the label text
        self.findChild(QtWidgets.QLabel, 'lblResponse').setText("Response")
        print("Label cleared")
    
    def get_sessions(self):
        """Handle the 'Get Sessions' button click"""
        #Get all sessions in the time range
        result = self.cloud_api.get_sessions_in_time_range(20251119,20251119)
        print("Get Sessions clicked")
        print(result)


    def post_smart_dot_data(self):
        """Handle the 'Post Smart Dot Data' button click"""
        print("Post Smart Dot Data clicked")
        result = self.cloud_api.post_smartdot_data(bsc.get_data_controller().get_smartdot_data(),1)
        print(result)
    
    def get_smart_dot_data(self):
        """Handle the 'Get Smart Dot Data' button click"""
        print("get diagnostic data")
        result = self.cloud_api.get_smartdot_data(1)
        print(result)
    
    def get_diagnostic_data(self):
        """Handle the 'Get Diagnostic Data' button click"""
        print("Get Diagnostic Data clicked")
        result = self.cloud_api.get_all_diagnostic_script_data_by_session(1)
        print(result)
    
    def post_diagnostic_data(self):
        """Handle the 'Post Diagnostic Data' button click"""
        print("Post Diagnostic Data clicked")
        result = self.cloud_api.post_diagnostic_script_data(bsc.get_data_controller().get_diagnostic_script_data(), 1)
        print(result)


    def post_shot_script_data(self):
        """Handle the 'Post Shot Script Data' button click"""
        print("Post Shot Script Data clicked")
        result = self.cloud_api.post_shot_script_data(bsc.get_data_controller().get_shot_script_data(), 1)
        print(result)
    
    def get_shot_script_data(self):
        """Handle the 'Get Shot Script Data' button click"""
        print("Get Shot Script Data clicked")
        result = self.cloud_api.get_shot_script_data_by_session(1)
        print(result)

    def post_encoder_data(self):
        print("Post Encoder Data clicked")

        artificial_encoder_data = [
                                    EncoderDataInstance(time=0.0, pulses=100, motor_id=1),
                                    EncoderDataInstance(time=0.1, pulses=200, motor_id=2),
                                    EncoderDataInstance(time=0.2, pulses=300, motor_id=3)
                                  ]
        # result = self.cloud_api.post_encoder_data(bsc.get_data_controller().get_encoder_data(), 1)
        result = self.cloud_api.post_encoder_data(artificial_encoder_data, 1)
        print(result)
    def get_encoder_data(self):
        print("Get Encoder Data clicked")
        result = self.cloud_api.get_encoder_data(1)
        print(result)
    def post_heat_data(self):
        print("Post Heat Data clicked")
        artificial_heat_data = [
                                HeatDataInstance(time=0.0, value=100, motor_id=1),
                                HeatDataInstance(time=0.1, value=200, motor_id=2),
                                HeatDataInstance(time=0.2, value=300, motor_id=3)
                              ]
    
        # result = self.cloud_api.post_heat_data(bsc.get_data_controller().get_heat_data(), 1)
        result = self.cloud_api.post_heat_data(artificial_heat_data, 1)
        print(result)
    def get_heat_data(self):
        print("Get Heat Data clicked")
        result = self.cloud_api.get_heat_data(1)
        print(result)

    def submit_all_data(self):
        print("Submit All Data clicked")
        bsc.get_data_controller().submit_session_data()
        print("All data submitted")

    def load_session_data_from_cloud(self):
        print("Load Session Data from Cloud clicked")
        session_id = self.findChild(QtWidgets.QSpinBox, 'spnSessionId').value()
        bsc.get_data_controller().load_session_data_from_cloud(SessionData(id=session_id, timeStamp=dt.datetime.now().isoformat(), name="Diagnostic Session", isShotMode=False))
        print("Session data loaded from cloud")

if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = CloudTest()
    window.setGeometry(100, 100, 800, 600) # x, y, width, height
    window.setWindowTitle("Cloud Test")
    window.show()
    sys.exit(app.exec())