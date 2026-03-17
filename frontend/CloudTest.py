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
from frontend.MotorTest import CharacterizeMotors
from BSC import bsc


class MotorTestGraphDialog(QtWidgets.QDialog):
    """Display motor test results in a tabbed plot layout."""

    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Motor Test Results")
        self.resize(900, 650)

        layout = QtWidgets.QVBoxLayout(self)
        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)

        for r in results:
            speed = r.get("target_speed")
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)

            time_to_target = r.get("time_to_target")
            overshoot = r.get("overshoot")
            target_speed = r.get("target_speed")
            overshoot_pct = None
            if target_speed and target_speed != 0:
                overshoot_pct = (overshoot + target_speed) / target_speed

            stats_str = (
                f"Time to target: {time_to_target:.2f}s" if time_to_target is not None else "Time to target: n/a"
            )
            if overshoot is not None:
                stats_str += f" | Overshoot: {overshoot:.2f}"
            if overshoot_pct is not None:
                stats_str += f" | Overshoot %: {overshoot_pct:.2f}"

            stats_label = QtWidgets.QLabel(stats_str)
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
            tab_layout.addWidget(plot)

            tabs.addTab(tab, f"{speed}")

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
            results = CharacterizeMotors(None, self._bsc)
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
        self.btnStepperDiagnosticData = self.findChild(QtWidgets.QPushButton, 'btnStepDiag')
        self.btnStepperDiagnosticData.clicked.connect(self.stepper_diagnostic_data)
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

        worker = MotorTestWorker(bsc, parent=self)
        worker.newText.connect(lambda t: text_edit.moveCursor(QTextCursor.MoveOperation.End) or text_edit.insertPlainText(t))

        def _on_finished(results):
            summary = f"Ran {len(results)} speeds, last runtime={results[-1]['runtime']:.2f}s\n"
            text_edit.append(summary)
            self.findChild(QtWidgets.QLabel, 'lblResponse').setText(summary)
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

    def stepper_diagnostic_data(self):
        print("Stepper Diagnostic Data clicked")
        # Simulate stepper diagnostic data by updating the label with changing values


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