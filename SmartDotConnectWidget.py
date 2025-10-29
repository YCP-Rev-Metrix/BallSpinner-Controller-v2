from PyQt6 import QtWidgets, QtCore, uic

class SmartDotConnectWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (name matches file in repo)
        uic.loadUi('SmartDotConnectWidget.ui', self)

        # Grab the connect button and status label created by the .ui file
        self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')

        # Grab the QScrollArea and the widget it contains.
        # The .ui defines the scroll area as 'conDevices' and the contained widget
        # is the scroll area's widget (named 'scrollAreaWidgetContents' in the .ui).
        self.conDevices = self.findChild(QtWidgets.QScrollArea, 'conDevices')
        # Use the scroll area's widget() accessor to get the contained QWidget.
        self.wDeviceList = self.conDevices.widget()
        self.Devices = []

        self.setFixedSize(200, 600)
        
        """
        self.Devices = ["SmartDot Device 1", "SmartDot Device 2", "SmartDot Device 3"]

        # Create UI elements for each device and add them to the scroll area's layout.
        self.deviceButtons = []
        layout = self.wDeviceList.layout()
        if layout is None:
            # If the contained widget does not have a layout in the .ui, create one.
            layout = QtWidgets.QVBoxLayout(self.wDeviceList)

        for device in self.Devices:
            btn = QtWidgets.QPushButton(f"Connect to {device}")
            layout.addWidget(btn)
            btn.clicked.connect(lambda _, d=device: self.connect_to_smartdot(d))
        """
        

    def connect_to_smartdot(self, text):
        # Simulate connection logic
        print(text)

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