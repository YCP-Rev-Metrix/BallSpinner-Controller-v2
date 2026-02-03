import platform
from unittest import case
from PyQt6 import QtWidgets, QtCore, uic
import os
from PyQt6.QtGui import QAction

from frontend.DataViewPage import DataViewPage
from frontend.FrontPage import FrontPage
from frontend.SmartDotViewer import SmartDotViewer
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

        self.EStop = self.findChild(QtWidgets.QPushButton, 'btnEStop')
        self.EStop.setStyleSheet("background-color: red; font-weight: bold; font-size: 16px;")
        
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

        # Set default to Real Motor
        self.actionSimulatedMotor.setChecked(True)

        self.actionSimulatedMotor.toggled.connect(lambda checked: self.motorSimulationControl(checked, True))
        self.actionRealMotor.toggled.connect(lambda checked: self.motorSimulationControl(checked, False))

    def estop(self):
        """E-stop function: stops motor and forces navigation enabled."""
        self.diagnosticPage.EStop()
        self.LockCount = 0
        self.menuBar.setEnabled(True)
        self.statusBar.showMessage("Navigation is enabled by force.",5000)
        self.NavigationSatus.setTitle("")

    def toggle_navigation(self, enable: bool, message :str):
        """Enable or disable the navigation menu."""
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
                self.diagnosticPage.smartdotViewer.smartdotConnectWidget.refresh()
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

        bsc.disconnect_all_motors()
        super().closeEvent(event)

    def resizeEvent(self, event):
            """Lock window to 16:9 aspect ratio on resize."""
            width = event.size().width()
            height = int(width * 9 / 16)
            # Prevent recursion by only resizing if height is not already correct
            if event.size().height() != height:
                self.resize(width, height)
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
            
        # Uncheck the other option
        if is_simulated:
            self.actionRealMotor.setChecked(False)
        else:
            self.actionSimulatedMotor.setChecked(False)
        



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
        
