from PyQt6 import QtWidgets, QtCore, uic
import os
from PyQt6.QtCore import pyqtSignal, QThread
import utils

from backend.smartdot.iSmartDot import iSmartDot
if utils.is_raspberry_pi():
    from backend.smartdot.ScanSmartDots import ScanSmartDot
    from backend.smartdot.MetaMotionS import MetaMotion
    from backend.smartdot.SimSmartDot import SimSmartDot

else:
    from backend.smartdot.SimSmartDot import SimSmartDot

from backend.smartdot.SubprocessScan import ProcessRunner
import ast

from BSC import bsc


class ConnectionWorker(QThread):
    """Worker thread to handle MetaMotion connection without blocking UI"""
    connectionComplete = pyqtSignal(object)  # Emits the connected smartdot object
    connectionFailed = pyqtSignal(str)  # Emits error message
    statusUpdate = pyqtSignal(str)  # Emits status update messages
    deviceDisconnected = pyqtSignal(str)  # Emits MAC address when device disconnects
    
    def __init__(self, mac_address, is_simulated=False):
        super().__init__()
        self.mac_address = mac_address
        self.is_simulated = is_simulated
    
    def run(self):
        try:
            if utils.is_raspberry_pi() and not self.is_simulated:
                # Create MetaMotion with autoConnect=False so we can handle retry status
                # Set up disconnect callback to emit signal when device disconnects
                smartdot = MetaMotion(self.mac_address, autoConnect=False, 
                                     disconnect_callback=lambda mac: self.deviceDisconnected.emit(mac))
                # Manually call connect with status callback to show retry status
                try:
                    # Pass status callback to connect() so it can notify us when retry happens
                    smartdot.connected = smartdot.connect(self.mac_address, status_callback=lambda msg: self.statusUpdate.emit(msg))
                except Exception as e:
                    # Re-raise to be caught by outer exception handler
                    raise
            else:
                smartdot = SimSmartDot(self.mac_address)
            
            if smartdot.connected:
                self.connectionComplete.emit(smartdot)
            else:
                self.connectionFailed.emit(f"Failed to connect to {self.mac_address}")
        except Exception as e:
            error_str = str(e)
            # If we get here after a timeout, it means the retry also failed
            if "Timed out" in error_str:
                self.connectionFailed.emit("Connection failed")
            else:
                self.connectionFailed.emit(f"Connection error: {error_str}")

class SmartDotConnectWidget(QtWidgets.QWidget):
    
    # if utils.is_raspberry_pi():
    #     signalSmartDotConnected = pyqtSignal(MetaMotion)
    # else:
    #     signalSmartDotConnected = pyqtSignal(SimSmartDot)

    signalSmartDotConnected = pyqtSignal(iSmartDot)
    signalDeviceDisconnected = pyqtSignal(str)  # Emits MAC address when device disconnects


    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'SmartDotConnectWidget.ui'), self, package='frontend')

        # Grab the connect button and status label created by the .ui file
        self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')
        self.lblStatus = self.findChild(QtWidgets.QLabel, 'lblStatus')
        self.lblStatus.setText("Not Connected")

        # Enable touch events on key interactive controls
        self.btnConnect.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.scanBtn.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
                
        # Grab the QScrollArea and the widget it contains.
        # The .ui defines the scroll area as 'conDevices' and the contained widget
        # is the scroll area's widget (named 'scrollAreaWidgetContents' in the .ui).
        self.conDevices = self.findChild(QtWidgets.QScrollArea, 'conDevices')
        # Use the scroll area's widget() accessor to get the contained QWidget.
        self.wDeviceList = self.conDevices.widget()
        self.Devices = []

        # Grab the disconnect QScrollArea and the widget it contains.
        # The .ui defines the scroll area as 'conDisconnectDevices' and the contained widget
        # is the scroll area's widget (named 'scrollAreaWidgetContentsDisconnect' in the .ui).
        self.conDisconnectDevices = self.findChild(QtWidgets.QScrollArea, 'conDisconnectDevices')
        # Use the scroll area's widget() accessor to get the contained QWidget.
        self.wDisconnectDeviceList = self.conDisconnectDevices.widget()

        self.process_runner = ProcessRunner()
        self.process_runner.outputReceived.connect(self.on_process_output)
        self.process_runner.errorReceived.connect(self.on_process_error)
        self.process_runner.finished.connect(self.on_process_finished)

        self.scanBtn = self.findChild(QtWidgets.QPushButton, "startScan")
        if self.scanBtn:
            self.scanBtn.clicked.connect(self.start_scan)

        # Track connection worker thread
        self.connection_worker = None

        #self.setFixedSize(300, 600)
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

        print(bsc.get_smartdotConnectionManager())
        
        # Update disconnect list to show any existing connections
        self.updateDisconnectList()
        
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
        # Update status to show connection attempt
        self.lblStatus.setText(f"Connecting to {text}...")
        
        # Check if this is a simulated device
        is_simulated = (text == "SI:MU:LA:TE:DD:OT" or not utils.is_raspberry_pi())

        #Check if we are already connected to this SmartDot
        for i in bsc.get_smartdotConnectionManager().get_connections():
            if i == text:
                self.lblStatus.setText(f"Already connected to {text}")
                return

        # Create and start connection worker thread
        self.connection_worker = ConnectionWorker(text, is_simulated)
        self.connection_worker.connectionComplete.connect(self.on_connection_success)
        self.connection_worker.connectionFailed.connect(self.on_connection_failed)
        self.connection_worker.statusUpdate.connect(self.on_status_update)
        self.connection_worker.deviceDisconnected.connect(self.on_device_disconnected)
        # Forward the disconnect signal to external listeners (like SmartDotViewer)
        self.connection_worker.deviceDisconnected.connect(self.signalDeviceDisconnected.emit)
        self.connection_worker.start()
    
    def on_connection_success(self, smartdot):
        """Called when connection succeeds"""
        self.smartdot = smartdot
        device_address = self.smartdot._MAC_ADDRESS if hasattr(self.smartdot, '_MAC_ADDRESS') else "device"
        self.lblStatus.setText(f"Connected to {device_address}")
        self.signalSmartDotConnected.emit(self.smartdot)

        #Add the connection to the manager upon successful connection
        bsc.get_smartdotConnectionManager().add_connection(self.smartdot._MAC_ADDRESS, self.smartdot)
        print(f"Connections: {bsc.get_smartdotConnectionManager().get_connections()}")
        
        # Update disconnect list to show the new connection
        self.updateDisconnectList()
    
    def on_status_update(self, status_message):
        """Called when status update is emitted"""
        self.lblStatus.setText(status_message)
    
    def on_device_disconnected(self, mac_address):
        """Called when device disconnects"""
        self.lblStatus.setText(f'Disconnected "{mac_address}"')

        #Remove the connection from the manager upon disconnection
        smartdot = bsc.get_smartdotConnectionManager().get_smartdot(mac_address)
        bsc.get_smartdotConnectionManager().remove_connection(mac_address, smartdot)
        print(f"Connections: {bsc.get_smartdotConnectionManager().get_connections()}")

        # Update disconnect list to reflect the disconnection
        self.updateDisconnectList()
    
    def on_connection_failed(self, error_message):
        """Called when connection fails"""
        self.lblStatus.setText(error_message)
        print(f"Connection failed: {error_message}")

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
            try:
                btn.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            except Exception:
                pass
            btn.clicked.connect(lambda _, d=device: self.connect_to_smartdot(d))

    def updateDisconnectList(self):
        """Update the list of disconnect buttons based on current connections"""
        # Get current connections from the manager
        connections = bsc.get_smartdotConnectionManager().get_connections()
        
        # Remove existing disconnect buttons
        layout = self.wDisconnectDeviceList.layout()
        if layout is not None:
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()
        
        # Clear existing buttons
        layout = self.wDisconnectDeviceList.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(self.wDisconnectDeviceList)
        
        # Create buttons for each connected device
        for mac_address in connections:
            btn = QtWidgets.QPushButton(mac_address)
            layout.addWidget(btn)
            try:
                btn.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            except Exception:
                pass
            btn.clicked.connect(lambda _, mac=mac_address: self.disconnect_from_smartdot(mac))
    
    def disconnect_from_smartdot(self, mac_address):
        """Disconnect from a SmartDot by MAC address"""
        # Get smartdot object from manager
        smartdot = bsc.get_smartdotConnectionManager().get_smartdot(mac_address)
        
        if smartdot is not None:
            # Call disconnect on the smartdot
            smartdot.disconnect()
            # Update status label
            self.lblStatus.setText(f"Disconnected from {mac_address}")
            # Remove connection from manager
            bsc.get_smartdotConnectionManager().remove_connection(mac_address, smartdot)
            # Update disconnect list to reflect the change
            self.updateDisconnectList()
            print(f"Disconnected from {mac_address}")
            print(f"Connections: {bsc.get_smartdotConnectionManager().get_connections()}")
        else:
            self.lblStatus.setText(f"Device {mac_address} not found")


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = SmartDotConnectWidget()
    widget.show()
    widget.setDeviceList(["SmartDot A", "SmartDot B", "SmartDot C"])

    widget.setDeviceList(["SmartDot D", "SmartDot E", "SmartDot F"])
    sys.exit(app.exec())