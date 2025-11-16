import platform
from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QAction

from FrontPage import FrontPage
from SmartDotTestPage import SmartDotTestPage



 


class HomePage(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file.
        uic.loadUi('HomePage.ui', self)

        self.EStop = self.findChild(QtWidgets.QPushButton, 'btnEStop')
        self.EStop.setStyleSheet("background-color: red; font-weight: bold; font-size: 16px;")
        
        self.tab = self.findChild(QtWidgets.QStackedWidget, "stackedWidget")

        self.frontPage = self.findChild(QtWidgets.QWidget, 'FrontPage')
        self.diagnosticPage = self.findChild(QtWidgets.QWidget, 'DiagnosticModePage')
        self.shotModePage = self.findChild(QtWidgets.QWidget, 'ShotModePage')
        self.smartDotTestPage = self.findChild(QtWidgets.QWidget, 'SmartDotTestPage')

        # connect page change signals 
        self.frontPage.changePage.connect(self.switch_to_page) #100% Nescessary
        self.diagnosticPage.changePage.connect(self.switch_to_page) #curr
        self.shotModePage.changePage.connect(self.switch_to_page)


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
       

    def closeEvent(self, event):
        """Signal background threads to stop when the window is closing."""
        try:
            self._stop_event.set()
        except Exception:
            pass
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
        