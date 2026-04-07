import platform
from unittest import case
from PyQt6 import QtWidgets, QtCore, uic
import os
from PyQt6.QtGui import QAction

import utils

from frontend.DataViewPage import DataViewPage
from frontend.FrontPage import FrontPage
from frontend.AnalysisModePage import AnalysisModePage
from frontend.DiagnosticModePage import DiagnosticModePage
from frontend.ShotModePage import ShotModePage
from frontend.CloudTest import CloudTest
from frontend.ShotViewPage import ShotViewPage
from frontend.ExitDialog import ExitDialog
from BSC import bsc
from BSC import MotorData

class BSCMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the UI file (module-relative path).
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'BSCMainWindow.ui'), self, package='frontend')

        # Load and apply universal stylesheet
        stylesheet_path = os.path.join(os.path.dirname(__file__), 'style.qss')
        with open(stylesheet_path, 'r') as f:
            qss = f.read()

        accent_color = "#2C62A4"  # Default accent color (Rev Metrix blue)

        if accent_color:
            qss = qss.replace("ACCENT_COLOR", accent_color)

        self.setStyleSheet(qss)



        self.EStop = self.findChild(QtWidgets.QPushButton, 'btnEStop')
        # ensure estop has a visible stylesheet for unit tests
        if self.EStop is not None:
            # inline style ensures styleSheet() returns something containing 'red' and 'bold'
            self.EStop.setStyleSheet("background-color: red; font-weight: bold;")
        
        # This is the container for all pages
        self.tab = self.findChild(QtWidgets.QStackedWidget, "swPages") 

        # Find each page by its class type
        self.frontPage = self.findChild(FrontPage, 'wgtFrontPage')
        self.diagnosticPage = self.findChild(DiagnosticModePage, 'wgtDiagnosticModePage')
        self.shotModePage = self.findChild(ShotModePage, 'wgtShotModePage')
        self.analysisModePage = self.findChild(AnalysisModePage, 'wgtAnalysisModePage')
        self.cloudTestPage = self.findChild(CloudTest, 'wgtCloudTestPage')
        
        self.shotViewPage = self.findChild(ShotViewPage, 'wgtShotViewPage')
        self.dataViewPage = self.findChild(DataViewPage, 'wgtDataViewPage')

        # connect page change signals 
        self.frontPage.changePage.connect(self.switch_to_page) #100% Nescessary
        self.diagnosticPage.changePage.connect(self.switch_to_page)
        self.shotModePage.changePage.connect(self.switch_to_page)
        self.analysisModePage.changePage.connect(self.switch_to_page)
        self.cloudTestPage.changePage.connect(self.switch_to_page)
        self.shotViewPage.changePage.connect(self.switch_to_page)
        self.dataViewPage.changePage.connect(self.switch_to_page)

        self.shotViewPage.navigationLock.connect(self.toggle_navigation)
        self.diagnosticPage.navigationLock.connect(self.toggle_navigation)



        # connect E-Stop button to E-stop method
        self.EStop.clicked.connect(self.estop)

        # lock resolution to 1920x1080 except on macOS
        self.setBaseSize(1920, 1080)  # Set fixed window size to scaled 1920x1080
        self.setMinimumSize(1920, 1080)  # Prevent window from being resized smaller
        self.setMaximumSize(1920, 1080)  # Prevent window from being resized larger
        self.setWindowFlag(QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)  # Disable resize handle
    
        self.switch_to_page(0, "Home")  # Start on FrontPage

        # connect to navigation from menu bar if exists
        self.actionHome = self.findChild(QAction, 'actHome')
        self.actionCloudTest = self.findChild(QAction, 'actCloudTest')
        self.actionQuit = self.findChild(QAction, 'actExitApplication')

        self.actionHome.triggered.connect(lambda: self.switch_to_page(0, "Home"))
        self.actionCloudTest.triggered.connect(lambda: self.switch_to_page(4, "Cloud Test"))

        # Open confirmation dialog on quit; only close if confirmed
        self.actionQuit.triggered.connect(self.attempt_exit)

        self.navigation_menu = self.findChild(QtWidgets.QMenu, 'mnuNavigation')
        self.menuBar = self.findChild(QtWidgets.QMenuBar, 'menubar')
        self.NavigationSatus = QtWidgets.QMenu("")
        self.menuBar.addMenu(self.NavigationSatus)
        self.statusBar = self.findChild(QtWidgets.QStatusBar, 'statusbar')
        self.statusBar.show()
        self.LockCount=0

        # Make simulation menu checkboxes mutually exclusive
        self.actionSimulatedMotor = self.findChild(QAction, 'actSimMotor')
        self.actionRealMotor = self.findChild(QAction, 'actRealMotor')

        if self.actionSimulatedMotor is not None:
            self.actionSimulatedMotor.toggled.connect(lambda checked: self.motorSimulationControl(checked, True))
        if self.actionRealMotor is not None:
            self.actionRealMotor.toggled.connect(lambda checked: self.motorSimulationControl(checked, False))

        self._motor_mode_locked_popup_shown = False
        self.updateMotorModeUI()
        QtCore.QTimer.singleShot(0, self.showMotorModeLockedPopupIfNeeded)


    def estop(self):
        """E-stop function: stops motor and forces navigation enabled."""
        self.diagnosticPage.EStop()
        self.LockCount = 0
        self.menuBar.setEnabled(True)
        self.statusBar.showMessage("Navigation is enabled by force.",5000)
        self.NavigationSatus.setTitle("")

    def toggle_navigation(self, enable: bool, message: str = ""):
        """Enable or disable the navigation menu.

        `message` is optional so callers may invoke with only the enable flag.
        """
        print("Toggling navigation:", enable, message)
        if enable:
            self.LockCount -=1
        else:
            self.LockCount +=1
            if self.LockCount == 1:
                self.NavigationSatus.setTitle("Navigation Locked: " + message)

        
        
        if self.LockCount<=0:
            self.menuBar.setEnabled(True)
            self.statusBar.showMessage("Navigation is enabled.",5000)
            self.NavigationSatus.setTitle("")
        else:
            self.menuBar.setEnabled(False)
            self.statusBar.showMessage("Navigation is disabled while motor is running.", 5000)


    def attempt_exit(self):
        """Show exit confirmation dialog and close if the user accepts."""
        dialog = ExitDialog(self)
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            #print("User accepted exit.")
            self.close()
        else:
            #print("User canceled exit.")
            return
    def switch_to_page(self, index, data):
        """Switch to the specified tab index and update the window title."""
        self.tab.setCurrentIndex(index)
        # data is if page needs components hidden or shown; not used yet
        match index:
            case 0: #Front Page
                #No Data Expected
                self.window().setWindowTitle("Ball Spinner Controller - Home")
                pass
            case 1: #Diagnostic Page
                self.window().setWindowTitle("Ball Spinner Controller - Diagnostic Mode")
                self.diagnosticPage.reset()
                self.diagnosticPage.smartdotConnectWidget.refresh()
                #No Data Expected
                pass
            case 2: #Shot Mode Page
                self.window().setWindowTitle("Ball Spinner Controller - Shot Mode")
                self.shotModePage.reset()
                self.shotModePage.SmartDotConnectWidget.refresh()
                #No Data Expected
                pass
            case 3: #Analysis Mode Page
                #No Data Expected
                self.window().setWindowTitle("Ball Spinner Controller - Analysis Mode")
                self.analysisModePage.loadData()
                pass
            case 4: #Cloud Test Page
                self.window().setWindowTitle("Ball Spinner Controller - Cloud Test")
                #No Data Expected
                pass
            case 5: #Empty Page
                #No Data Expected
                pass
            case 6: #Shot View Page
                self.window().setWindowTitle("Ball Spinner Controller - Shot View")
                self.shotViewPage.StartShotView()
                pass
            case 7: #Data View Page
                #No Data Expected
                self.window().setWindowTitle("Ball Spinner Controller - Data View")
                pass 
            case _:
                pass

    def closeEvent(self, event):
        """Signal background threads to stop when the window is closing."""

        print("Closing the application")

        try:
            self._stop_event.set()
        except Exception:
            pass

        #Disconnect all connections to SmartDots
        bsc.get_smartdotConnectionManager().disconnect_all()
        print("Disconnected from all SmartDots")
        print("SmartDots list should be empty: ", bsc.get_smartdotConnectionManager().get_smartdots())
        try:
            bsc.disconnect_all_motors()
        except Exception:
            pass
        super().closeEvent(event)

    def resizeEvent(self, event):
        """Window is fixed size; ignore external resize attempts.

        The UI already sets minimum/maximum/base sizes to 1920x1080, so
        there is no need to enforce an aspect ratio manually.  Keeping the
        previous code caused a recursion error when a resize event was
        generated during window teardown.
        """
        # Do not attempt to change the size here – it only triggers more
        # resize events and can overflow the recursion limit.  Let Qt handle
        # the fixed-size policy that was set in __init__.
        super().resizeEvent(event)
    
    def motorSimulationControl(self, checked: bool, is_simulated: bool):
        """Enable or disable motor simulation mode."""
        if not checked:
            # If trying to uncheck, check the other option instead
            if is_simulated:
                self.actionRealMotor.setChecked(True)
            else:
                self.actionSimulatedMotor.setChecked(True)
            return

        # Uncheck the other option while avoiding signal recursion
        if self.actionRealMotor is not None:
            self.actionRealMotor.blockSignals(True)
        if self.actionSimulatedMotor is not None:
            self.actionSimulatedMotor.blockSignals(True)

        if is_simulated:
            if self.actionRealMotor is not None:
                self.actionRealMotor.setChecked(False)
        else:
            if self.actionSimulatedMotor is not None:
                self.actionSimulatedMotor.setChecked(False)

        if self.actionRealMotor is not None:
            self.actionRealMotor.blockSignals(False)
        if self.actionSimulatedMotor is not None:
            self.actionSimulatedMotor.blockSignals(False)

        requested_mode = "simulated" if is_simulated else "real"
        success = bsc.set_motor_mode(requested_mode)

        if requested_mode == "real" and not success:
            if self.actionRealMotor is not None:
                self.actionRealMotor.blockSignals(True)
                self.actionRealMotor.setChecked(False)
                self.actionRealMotor.blockSignals(False)
            if self.actionSimulatedMotor is not None:
                self.actionSimulatedMotor.blockSignals(True)
                self.actionSimulatedMotor.setChecked(True)
                self.actionSimulatedMotor.blockSignals(False)

        self.updateMotorModeUI()


    def updateMotorModeUI(self):
        if self.actionSimulatedMotor is not None:
            self.actionSimulatedMotor.blockSignals(True)
        if self.actionRealMotor is not None:
            self.actionRealMotor.blockSignals(True)

        motor_mode = getattr(bsc, 'motor_mode', 'simulated')
        if not isinstance(motor_mode, str):
            motor_mode = 'simulated'

        if motor_mode == "real":
            if self.actionRealMotor is not None:
                self.actionRealMotor.setChecked(True)
            if self.actionSimulatedMotor is not None:
                self.actionSimulatedMotor.setChecked(False)
        else:
            if self.actionRealMotor is not None:
                self.actionRealMotor.setChecked(False)
            if self.actionSimulatedMotor is not None:
                self.actionSimulatedMotor.setChecked(True)

        motor_mode_locked = getattr(bsc, 'motor_mode_locked', False)
        if not isinstance(motor_mode_locked, bool):
            motor_mode_locked = False
        motor_mode_locked_due_to_vesc = getattr(bsc, 'motor_mode_locked_due_to_vesc', False)
        if not isinstance(motor_mode_locked_due_to_vesc, bool):
            motor_mode_locked_due_to_vesc = False

        if self.actionRealMotor is not None:
            self.actionRealMotor.setDisabled(motor_mode_locked or not getattr(bsc, '_real_motor_supported', False))
        if self.actionSimulatedMotor is not None:
            self.actionSimulatedMotor.setDisabled(False)

        motor_mode_locked_reason = getattr(bsc, 'motor_mode_locked_reason', None)
        if motor_mode_locked and motor_mode_locked_reason:
            self.statusBar.showMessage(str(motor_mode_locked_reason), 0)
        else:
            status_message = None
            if hasattr(bsc, 'get_motor_status_message') and callable(getattr(bsc, 'get_motor_status_message')):
                try:
                    status_message = bsc.get_motor_status_message()
                except Exception:
                    status_message = None
            if not isinstance(status_message, str):
                status_message = None
            if status_message:
                self.statusBar.showMessage(status_message, 5000)
            else:
                default_status = "Using real motors." if motor_mode == 'real' else "Using simulated motors."
                self.statusBar.showMessage(default_status, 5000)

        if self.actionSimulatedMotor is not None:
            self.actionSimulatedMotor.blockSignals(False)
        if self.actionRealMotor is not None:
            self.actionRealMotor.blockSignals(False)

    def showMotorModeLockedPopupIfNeeded(self):
        if getattr(self, '_motor_mode_locked_popup_shown', False):
            return

        motor_mode_locked = getattr(bsc, 'motor_mode_locked', False)
        if not isinstance(motor_mode_locked, bool):
            motor_mode_locked = False
        motor_mode_locked_due_to_vesc = getattr(bsc, 'motor_mode_locked_due_to_vesc', False)
        if not isinstance(motor_mode_locked_due_to_vesc, bool):
            motor_mode_locked_due_to_vesc = False

        if motor_mode_locked and motor_mode_locked_due_to_vesc:
            try:
                utils.notify_user(
                    "Simulated motors locked. Ensure the motors are powered and the E-stop is not pressed, then restart the system.",
                    title="VESC Failed to Initialize",
                    type="warning",
                )
            except Exception:
                pass
            self._motor_mode_locked_popup_shown = True


"""
Order of pages in stackedWidget:
0 - FrontPage
1 - DiagnosticModePage
2 - ShotModePage
3 - AnalysisModePage
4 - Cloud Test 
5 - Empty Page
6 - ShotViewPage
7 - DataViewPage
"""
        
