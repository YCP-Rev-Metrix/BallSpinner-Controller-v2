from PyQt6 import QtWidgets, QtCore, uic
from PyQt6.QtCore import pyqtSignal
import utils
if utils.is_raspberry_pi():
    from backend.smartdot.ScanSmartDots import ScanSmartDot
    from backend.smartdot.MetaMotionS import MetaMotion
else:
    from backend.smartdot.SimSmartDot import SimSmartDot

from backend.smartdot.SubprocessScan import ProcessRunner
import ast

class SmartDotConnectWidget(QtWidgets.QWidget):
    
    if utils.is_raspberry_pi():
        signalSmartDotConnected = pyqtSignal(MetaMotion)
    else:
        signalSmartDotConnected = pyqtSignal(SimSmartDot)


    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (name matches file in repo)
        uic.loadUi('SmartDotConnectWidget.ui', self)

        # Grab the connect button and status label created by the .ui file
        self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')
        self.lblStatus = self.findChild(QtWidgets.QLabel, 'lblStatus')
        self.lblStatus.setText("Not Connected")

        # Grab the QScrollArea and the widget it contains.
        # The .ui defines the scroll area as 'conDevices' and the contained widget
        # is the scroll area's widget (named 'scrollAreaWidgetContents' in the .ui).
        self.conDevices = self.findChild(QtWidgets.QScrollArea, 'conDevices')
        # Use the scroll area's widget() accessor to get the contained QWidget.
        self.wDeviceList = self.conDevices.widget()
        self.Devices = []

        self.process_runner = ProcessRunner()
        self.process_runner.outputReceived.connect(self.on_process_output)
        self.process_runner.errorReceived.connect(self.on_process_error)
        self.process_runner.finished.connect(self.on_process_finished)

        self.scanBtn = self.findChild(QtWidgets.QPushButton, "startScan")
        if self.scanBtn:
            self.scanBtn.clicked.connect(self.start_scan)


        self.setFixedSize(300, 600)
        if utils.is_raspberry_pi():
            # self.scanner = ScanSmartDot()
            pass
            # #TODO: IN thread 
            # self.scanner.scan10Seconds()
            # self.scanner.devices.append("SI:MU:LA:TE:DD:OT")
            # self.setDeviceList(self.scanner.devices)

        else:
            self.smartdot = SimSmartDot()
            self.setDeviceList(["SI:MU:LA:TE:DD:OT"])
        
    def start_scan(self):
        """Starts the ScanSmartDots.py script using ProcessRunner"""
        self.lblStatus.setText("Scanning for SmartDots...")
        print("Starting scan subprocess...")

        # You can pass absolute or relative path to ScanSmartDots.py
        self.process_runner.start("python3", ["-u", "backend/smartdot/ScanSmartDots.py"])
    # Handlers for ProcessRunner signals
    def on_process_output(self, text: str):
        print("[Scan Output]", text)

        if "Found devices:" in text:
            try:
                # Extract everything after the colon
                list_part = text.split("Found devices:")[1].strip()

                # Safely parse the list using ast.literal_eval
                devices = ast.literal_eval(list_part)
                devices.append("SI:MU:LA:TE:DD:OT")


                if isinstance(devices, list):
                    print("Parsed device list:", devices)
                    self.lblStatus.setText(f"Found {len(devices)} devices")
                    self.setDeviceList(devices)
                else:
                    print("Unexpected format for devices:", list_part)
                    self.lblStatus.setText("Scan complete (no valid devices found)")
            except Exception as e:
                print("Error parsing device list:", e)
                self.lblStatus.setText("Error parsing scan output")

        else:
            # Generic live output update
            self.lblStatus.setText(f"Scan running... {text}")

    def on_process_error(self, text: str):
        print("[Scan Error]", text)
        self.lblStatus.setText(f"Error: {text}")

    def on_process_finished(self, code: int, status: int):
        print(f"Scan finished (code={code}, status={status})")
        self.lblStatus.setText("Scan complete")
        # You could reload the device list here if the scan outputs it to a file or stdout

    def connect_to_smartdot(self, text):
        # Simulate connection logic
        if utils.is_raspberry_pi():
            self.smartdot = MetaMotion(text)
        else:
            self.smartdot = SimSmartDot(text)
        if(self.smartdot.connected):
            self.lblStatus.setText(f"Connected to {text}")
        self.signalSmartDotConnected.emit(self.smartdot)

    def setDeviceList(self, devices):
        #remove existing buttons
        layout = self.wDeviceList.layout()
        if layout is not None:
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()
        # Update the device list in the scroll area
        self.Devices = devices
        # Clear existing buttons
        layout = self.wDeviceList.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(self.wDeviceList)

        for device in self.Devices:
            btn = QtWidgets.QPushButton(f"Connect to {device}")
            layout.addWidget(btn)
            btn.clicked.connect(lambda _, d=device: self.connect_to_smartdot(d))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = SmartDotConnectWidget()
    widget.show()
    widget.setDeviceList(["SmartDot A", "SmartDot B", "SmartDot C"])

    widget.setDeviceList(["SmartDot D", "SmartDot E", "SmartDot F"])
    sys.exit(app.exec())