import logging

from PyQt6 import QtWidgets, QtCore, uic
import os
from PyQt6.QtCore import pyqtSignal, QThread
import utils

logger = logging.getLogger(__name__)
from backend.smartdot.iSmartDot import iSmartDot
if utils.is_raspberry_pi():
    from backend.smartdot.ScanSmartDots import ScanSmartDot
    from backend.smartdot.MetaMotionS import MetaMotion
    from backend.smartdot.SimSmartDot import SimSmartDot

else:
    from backend.smartdot.SimSmartDot import SimSmartDot

from backend.smartdot.SubprocessScan import ProcessRunner
from frontend.LoadingOverlay import LoadingOverlay
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
        logger.debug(f"ConnectionWorker.run() start: mac={self.mac_address}, simulated={self.is_simulated}")
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
                    logger.exception(f"MetaMotion connect exception for {self.mac_address}")
                    # Re-raise to be caught by outer exception handler
                    raise
            else:
                smartdot = SimSmartDot(self.mac_address)
            
            if smartdot.connected:
                logger.info(f"ConnectionWorker connected: {self.mac_address}")
                self.connectionComplete.emit(smartdot)
            else:
                logger.warning(f"ConnectionWorker failed (no connected flag): {self.mac_address}")
                self.connectionFailed.emit(f"Failed to connect to {self.mac_address}")
        except Exception as e:
            error_str = str(e)
            # If we get here after a timeout, it means the retry also failed
            if "Timed out" in error_str:
                self.connectionFailed.emit(f"Connection failed: {error_str}")
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

        # connection retry state
        self.last_connect_target = None
        self.retry_attempts = 0
        self.max_retry_attempts = 3
        self._connection_attempt_active = False

        # set a smaller font for all buttons in this widget (including dynamically created ones)
        # using Qt style sheet ensures the size applies globally here
        self.setStyleSheet("QPushButton { font-size: 10pt; }")

        # Grab the collapse button
        self.collapseBtn = self.findChild(QtWidgets.QPushButton, 'btnCollapse')
        self.collapseBtn.clicked.connect(self.toggle_collapse)
        
        # Grab the connect button and status label created by the .ui file
        self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')
        self.lblStatus = self.findChild(QtWidgets.QLabel, 'lblStatus')
        self.lblStatus.setText("Not Connected")

        # Grab the QScrollArea and the widget it contains.
        # The .ui defines the scroll area as 'conDevices' and the contained widget
        # is the scroll area's widget (named 'scrollAreaWidgetContents' in the .ui).
        self.conDevices = self.findChild(QtWidgets.QScrollArea, 'conDevices')
        self.conDevices.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.conDevices.setWidgetResizable(True)
        # Use the scroll area's widget() accessor to get the contained QWidget.
        self.wDeviceList = self.conDevices.widget()
        self.Devices = []

        # Grab the disconnect QScrollArea and the widget it contains.
        # The .ui defines the scroll area as 'conDisconnectDevices' and the contained widget
        # is the scroll area's widget (named 'scrollAreaWidgetContentsDisconnect' in the .ui).
        self.conDisconnectDevices = self.findChild(QtWidgets.QScrollArea, 'conDisconnectDevices')
        self.conDisconnectDevices.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.conDisconnectDevices.setWidgetResizable(True)
        # Use the scroll area's widget() accessor to get the contained QWidget.
        self.wDisconnectDeviceList = self.conDisconnectDevices.widget()
        
        # Track collapse state
        self.is_collapsed = False

        self.process_runner = ProcessRunner()
        self.process_runner.outputReceived.connect(self.on_process_output)
        self.process_runner.errorReceived.connect(self.on_process_error)
        self.process_runner.finished.connect(self.on_process_finished)
        self.loadingOverlay = None

        self.scanBtn = self.findChild(QtWidgets.QPushButton, "btnStartScan")
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
        logger.debug(f"Connection manager at init: {bsc.get_smartdotConnectionManager()}")
        
        # Update disconnect list to show any existing connections
        self.updateDisconnectList()
        
        # Store original width for collapse/expand
        self.expanded_width = max(self.width(), 430)
        self.setMinimumWidth(self.expanded_width)
        self.setMaximumWidth(self.expanded_width)
    
    def toggle_collapse(self):
        """Toggle collapse/expand state of the widget"""
        self.is_collapsed = not self.is_collapsed
        
        # Hide/show content
        self.scanBtn.setVisible(not self.is_collapsed)
        self.conDevices.setVisible(not self.is_collapsed)
        self.lblStatus.setVisible(not self.is_collapsed)
        self.conDisconnectDevices.setVisible(not self.is_collapsed)
        
        # Get header labels and hide them too
        lblHeader = self.findChild(QtWidgets.QLabel, 'lblHeader')
        lblDisconnectHeader = self.findChild(QtWidgets.QLabel, 'lblDisconnectHeader')
        if lblHeader:
            lblHeader.setVisible(not self.is_collapsed)
        if lblDisconnectHeader:
            lblDisconnectHeader.setVisible(not self.is_collapsed)
        
        # Adjust width
        if self.is_collapsed:
            self.setMaximumWidth(80)  # Narrow width when collapsed
            self.setMinimumWidth(80)
            self.resize(80, self.height())  # Force resize to narrow width
        else:
            self.setMaximumWidth(self.expanded_width)
            self.setMinimumWidth(self.expanded_width)
            self.resize(self.expanded_width, self.height())  # Force resize to expanded width
        
        # Update button text
        self.collapseBtn.setText("▶" if self.is_collapsed else "▼")
        
    
    def start_scan(self):
        """Starts the ScanSmartDots.py script using ProcessRunner"""
        self.lblStatus.setText("Scanning for SmartDots...")
        self._show_loading("Scanning for SmartDots...")
        print("Starting scan subprocess...")
        logger.info("Starting scan subprocess")

        # You can pass absolute or relative path to ScanSmartDots.py
        self.process_runner.start("python3", ["-u", "backend/smartdot/ScanSmartDots.py"])
    # Handlers for ProcessRunner signals
    def on_process_output(self, text: str):
        print("[Scan Output]", text)
        logger.debug(f"Scan output: {text}")

        if "Found devices:" in text:
            try:
                # Extract everything after the colon
                list_part = text.split("Found devices:")[1].strip()

                # Safely parse the list using ast.literal_eval
                devices = ast.literal_eval(list_part)
                devices.append("SI:MU:LA:TE:DD:OT")


                if isinstance(devices, list):
                    print("Parsed device list:", devices)
                    logger.info(f"Parsed device list: {devices}")
                    self.lblStatus.setText(f"Found {len(devices)} devices")
                    self.setDeviceList(devices)
                else:
                    print("Unexpected format for devices:", list_part)
                    logger.warning(f"Unexpected format for devices: {list_part}")
                    self.lblStatus.setText("Scan complete (no valid devices found)")
            except Exception as e:
                print("Error parsing device list:", e)
                logger.exception(f"Error parsing device list: {e}")
                self.lblStatus.setText("Error parsing scan output")

        else:
            # Generic live output update
            self.lblStatus.setText(f"Scan running... {text}")

    def on_process_error(self, text: str):
        print("[Scan Error]", text)
        logger.error(f"Scan error: {text}")
        self.lblStatus.setText(f"Error: {text}")
        self._hide_loading()

    def on_process_finished(self, code: int, status: int):
        print(f"Scan finished (code={code}, status={status})")
        logger.info(f"Scan finished: code={code}, status={status}")
        self.lblStatus.setText("Scan complete")
        self._hide_loading()
        # You could reload the device list here if the scan outputs it to a file or stdout

    def connect_to_smartdot(self, text):
        # Reset retry counter if switching to different target
        if self.last_connect_target != text:
            self.retry_attempts = 0

        # Track target for retry path
        self.last_connect_target = text
        self._connection_attempt_active = True

        logger.info(f"connect_to_smartdot start: {text}")

        # Update status to show connection attempt
        self.lblStatus.setText(f"Connecting to {text}...")
        self._show_loading(f"Connecting to {text}...")
        
        # Check if this is a simulated device
        is_simulated = (text == "SI:MU:LA:TE:DD:OT" or not utils.is_raspberry_pi())

        #Check if we are already connected to this SmartDot
        for i in bsc.get_smartdotConnectionManager().get_connections():
            if i == text:
                self.lblStatus.setText(f"Already connected to {text}")
                self._connection_attempt_active = False
                self._hide_loading()
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
        device_address = smartdot._MAC_ADDRESS if hasattr(smartdot, '_MAC_ADDRESS') else "device"
        logger.info(f"Connection success: {device_address}")
        self.smartdot = smartdot
        self.lblStatus.setText(f"Connected to {device_address}")
        self._connection_attempt_active = False
        self._hide_loading()
        self.signalSmartDotConnected.emit(self.smartdot)

        #Add the connection to the manager upon successful connection
        bsc.get_smartdotConnectionManager().add_connection(self.smartdot._MAC_ADDRESS, self.smartdot)
        print(f"Connections: {bsc.get_smartdotConnectionManager().get_connections()}")
        logger.debug(f"Connection list after success: {bsc.get_smartdotConnectionManager().get_connections()}")
        
        # Update disconnect list to show the new connection
        self.updateDisconnectList()
    
    def on_status_update(self, status_message):
        """Called when status update is emitted"""
        self.lblStatus.setText(status_message)
        if self._connection_attempt_active:
            self._show_loading(status_message)
    
    def on_device_disconnected(self, mac_address):
        """Called when device disconnects"""
        self.lblStatus.setText(f'Disconnected "{mac_address}"')
        if not self._connection_attempt_active:
            self._hide_loading()

        #Remove the connection from the manager upon disconnection
        smartdot = bsc.get_smartdotConnectionManager().get_smartdot(mac_address)
        bsc.get_smartdotConnectionManager().remove_connection(mac_address, smartdot)
        print(f"Connections: {bsc.get_smartdotConnectionManager().get_connections()}")
        logger.debug(f"Connection list after disconnect: {bsc.get_smartdotConnectionManager().get_connections()}")

        # Update disconnect list to reflect the disconnection
        self.updateDisconnectList()
    
    def on_connection_failed(self, error_message):
        """Called when connection fails"""
        logger.warning(f"Connection failed: {error_message}")
        self.lblStatus.setText(error_message)

        # Remove the failed device from the available connect list
        if self.last_connect_target:
            self.removeDeviceFromList(self.last_connect_target)

        # Notify user with a modal warning/critical dialog for visibility
        try:
            utils.notify_user(
                "SmartDot connection failed. See details for the full exception.",
                title="SmartDot Connection Error",
                type="critical",
                details=error_message,
            )
        except Exception as e:
            print(f"Failed to show error dialog: {e}")
            logger.exception(f"Failed to show error dialog: {e}")

        # Handle stale BLE condition and retry for common errors
        recovery_keywords = [
            "socket connection failed",
            "Failed to discover GATT services",
            "Connection failed",
            "Error initializing the API",
            "Connection error",
        ]
        if any(keyword in error_message for keyword in recovery_keywords):
            self._run_ble_recovery_scripts()
            if self.last_connect_target:
                existing = bsc.get_smartdotConnectionManager().get_smartdot(self.last_connect_target)
                if existing is not None:
                    try:
                        existing.disconnect()
                    except Exception as e:
                        print(f"Error disconnecting stale SmartDot: {e}")
                        logger.exception(f"Error disconnecting stale SmartDot: {e}")
                    bsc.get_smartdotConnectionManager().remove_connection(self.last_connect_target, existing)
                    self.updateDisconnectList()

            self.retry_attempts += 1
            if self.retry_attempts <= self.max_retry_attempts and self.last_connect_target:
                delay_ms = 1000 * self.retry_attempts
                self.lblStatus.setText(f"Retrying connection ({self.retry_attempts}/{self.max_retry_attempts})...")
                self._show_loading(
                    f"Recovering Bluetooth and retrying ({self.retry_attempts}/{self.max_retry_attempts})..."
                )
                QtCore.QTimer.singleShot(delay_ms, lambda: self.connect_to_smartdot(self.last_connect_target))
            else:
                self.lblStatus.setText("Maximum retries reached. Please restart Bluetooth or device and try again.")
                self._connection_attempt_active = False
                self._hide_loading()
        else:
            self._connection_attempt_active = False
            self._hide_loading()

    def _get_loading_overlay(self):
        host = self.window() or self
        overlay = getattr(host, "_global_loading_overlay", None)
        if overlay is None:
            overlay = LoadingOverlay(host)
            setattr(host, "_global_loading_overlay", overlay)
            overlay.cancel_requested.connect(self._on_loading_cancel)
        return overlay

    def _on_loading_cancel(self):
        """Dismiss overlay; reset connection UI state (BLE connect may still finish in background)."""
        self._connection_attempt_active = False
        self._hide_loading()
        if self.lblStatus is not None:
            self.lblStatus.setText("Cancelled.")

    def _show_loading(self, message: str):
        self._get_loading_overlay().show_message(message)

    def _hide_loading(self):
        self._get_loading_overlay().hide_overlay()

    def _run_ble_recovery_scripts(self):
        """Run local BLE recovery scripts after SmartDot connection failures."""
        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            restart_script = os.path.join(repo_root, "restartbluetooth.sh")
            scan_script = os.path.join(repo_root, "bluetoothctlscantrick.sh")

            if os.path.exists(restart_script):
                logger.info(f"Running BLE recovery script: {restart_script}")
                QtCore.QProcess.startDetached("bash", [restart_script])

            if os.path.exists(scan_script):
                logger.info(f"Running BLE scan recovery script: {scan_script}")
                QtCore.QProcess.startDetached("expect", [scan_script])
        except Exception as e:
            logger.exception(f"Failed to run BLE recovery scripts: {e}")


    def removeDeviceFromList(self, device):
        """Remove a device from the available SmartDot list and refresh the UI."""
        if device in self.Devices:
            self.Devices = [d for d in self.Devices if d != device]
            self.setDeviceList(self.Devices)


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
            btn = QtWidgets.QPushButton(f"Connect to \n{device}")
            layout.addWidget(btn)
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
            logger.info(f"Disconnected from {mac_address}")
            print(f"Connections: {bsc.get_smartdotConnectionManager().get_connections()}")
            logger.debug(f"Connections after disconnect: {bsc.get_smartdotConnectionManager().get_connections()}")
        else:
            self.lblStatus.setText(f"Device {mac_address} not found")

    def refresh(self):
        """Refresh the device list and emit signals for connected devices from the connection manager"""
        # Get all current connections from the manager
        connections = bsc.get_smartdotConnectionManager().get_connections()
        # Emit signal for each connected device
        for mac_address in connections:
            smartdot = bsc.get_smartdotConnectionManager().get_smartdot(mac_address)
            if smartdot is not None:
                self.signalSmartDotConnected.emit(smartdot)
        # Update the disconnect list to show all current connections
        self.updateDisconnectList()



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = SmartDotConnectWidget()
    widget.show()
    widget.setDeviceList(["SmartDot A", "SmartDot B", "SmartDot C"])

    widget.setDeviceList(["SmartDot D", "SmartDot E", "SmartDot F"])
    sys.exit(app.exec())