import platform
from PyQt6 import QtWidgets, uic

from FrontPage import FrontPage
from SmartDotTestPage import SmartDotTestPage



 


class HomePage(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file.
        uic.loadUi('HomePage.ui', self)

        self.EStop = self.findChild(QtWidgets.QPushButton, 'btnEStop')
        self.EStop.setStyleSheet("background-color: red; font-weight: bold; font-size: 16px;")
        
        self.tab = self.findChild(QtWidgets.QTabWidget, 'tabWidget')
        self.frontPage = self.findChild(QtWidgets.QWidget, 'FrontPage')
        self.diagnosticPage = self.findChild(QtWidgets.QWidget, 'DiagnosticModePage')
        self.shotModePage = self.findChild(QtWidgets.QWidget, 'ShotModePage')
        self.smartDotTestPage = self.findChild(QtWidgets.QWidget, 'SmartDotTestPage')

        # Create FrontPage instance and connect signal
        self.frontPage.changePage.connect(self.switch_to_page)
        self.diagnosticPage.changePage.connect(self.switch_to_page)
        self.shotModePage.changePage.connect(self.switch_to_page)
        #self.smartDotTestPage.changePage.connect(self.switch_to_page)

        self.EStop.clicked.connect(lambda: self.diagnosticPage.EStop())

        # lock resolution to 1920x1080 except on macOS
        if(platform.system() != 'Darwin'):
            self.setFixedSize(1920, 1080)  # Set fixed window size to 1920x1080
        else:
            self.setBaseSize(1920, 1080)  # Set base window size to 1920x1080 on macOS

       
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
        