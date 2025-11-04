from PyQt6 import QtWidgets, QtCore, uic
from PyQt6.QtCore import pyqtSignal
import utils
if utils.is_raspberry_pi():
    from backend.smartdot.ScanSmartDots import ScanSmartDot
    from backend.smartdot.MetaMotionS import MetaMotion
else:
    from backend.smartdot.SimSmartDot import SimSmartDot


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

        self.setFixedSize(300, 600)
        if utils.is_raspberry_pi():
            self.scanner = ScanSmartDot()
            self.scanner.scan10Seconds()
            self.setDeviceList(self.scanner.devices)
        else:
            self.smartdot = SimSmartDot()
            self.setDeviceList(["SI:MU:LA:TE:D1:!!:!!"])
        

    def connect_to_smartdot(self, text):
        # Simulate connection logic
        self.smartdot = MetaMotion(text)
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