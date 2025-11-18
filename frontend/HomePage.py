import platform
from unittest import case
from PyQt6 import QtWidgets, uic
import os
from PyQt6.QtGui import QAction

from frontend.FrontPage import FrontPage
from frontend.SmartDotTestPage import SmartDotTestPage
from frontend.AnalysisModePage import AnalysisModePage
from frontend.DiagnosticModePage import DiagnosticModePage
from frontend.ShotModePage import ShotModePage
from frontend.CloudTest import CloudTest
from BSC import bsc

class HomePage(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file (module-relative path).
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'HomePage.ui'), self, package='frontend')

        self.EStop = self.findChild(QtWidgets.QPushButton, 'btnEStop')
        self.EStop.setStyleSheet("background-color: red; font-weight: bold; font-size: 16px;")
        
        # This is the container for all pages
        self.tab = self.findChild(QtWidgets.QStackedWidget, "stackedWidget") 

        # Find each page by its class type
        self.frontPage = self.findChild(FrontPage, 'FrontPage')
        self.diagnosticPage = self.findChild(DiagnosticModePage, 'DiagnosticModePage')
        self.shotModePage = self.findChild(ShotModePage, 'ShotModePage')
        self.analysisModePage = self.findChild(AnalysisModePage, 'AnalysisModePage')
        self.cloudTestPage = self.findChild(CloudTest, 'CloudTestPage')
        self.smartDotTestPage = self.findChild(SmartDotTestPage, 'SmartDotTestPage')

        # connect page change signals 
        self.frontPage.changePage.connect(self.switch_to_page) #100% Nescessary
        self.diagnosticPage.changePage.connect(self.switch_to_page)
        self.shotModePage.changePage.connect(self.switch_to_page)
        self.analysisModePage.changePage.connect(self.switch_to_page)
        self.cloudTestPage.changePage.connect(self.switch_to_page)
        self.smartDotTestPage.changePage.connect(self.switch_to_page)


        # connect E-Stop button to diagnostic page E-Stop function
        self.EStop.clicked.connect(lambda: self.diagnosticPage.EStop())

        # lock resolution to 1920x1080 except on macOS
        if(platform.system() != 'Darwin'):
            self.setFixedSize(1920, 1080)  # Set fixed window size to 1920x1080
        else:
            self.setBaseSize(1920, 1080)  # Set base window size to 1920x1080 on macOS
        
        self.switch_to_page(0, "Home")  # Start on FrontPage

        #connect to navigation from menu bar if exists
        self.actionHome = self.findChild(QAction, 'actionHome')
        self.actionCloudTest = self.findChild(QAction, 'actionCloud_Test')

        self.actionHome.triggered.connect(lambda: self.switch_to_page(0, "Home"))
        self.actionCloudTest.triggered.connect(lambda: self.switch_to_page(4, "Cloud Test"))

       
    def switch_to_page(self, index, data):
        """Switch to the specified tab index and update the window title."""
        self.tab.setCurrentIndex(index)
        # data is if page needs components hidden or shown; not used yet
        match index:
            case 0: #Front Page
                #No Data Expected
                pass
            case 1: #Diagnostic Page
                #No Data Expected
                pass
            case 2: #Shot Mode Page
                #No Data Expected
                pass
            case 3: #Analysis Mode Page
                #No Data Expected
                pass
            case 4: #Cloud Test Page
                #No Data Expected
                pass
            case 5: #SmartDot Test Page
                #No Data Expected
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
        super().closeEvent(event)

"""
Order of pages in stackedWidget:
0 - FrontPage
1 - DiagnosticModePage
2 - ShotModePage
3 - AnalysisModePage
4 - Cloud Test 
5 - SmartDotTestPage (Currently not used, can be replaced)
"""
        