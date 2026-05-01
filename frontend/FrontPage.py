from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QPixmap
import os
from PyQt6.QtCore import pyqtSignal

class FrontPage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # load the .ui file (module-relative path)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'FrontPage.ui'), self, package='frontend')

        self.btnDiagnostics = self.findChild(QtWidgets.QPushButton, 'btnDiagnostic')
        self.btnShotMode = self.findChild(QtWidgets.QPushButton, 'btnShot')
        self.btnData = self.findChild(QtWidgets.QPushButton, 'btnAnalysis')

        self.lblLogo = self.findChild(QtWidgets.QLabel, 'lblLogo')
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        if self.lblLogo and os.path.exists(logo_path):
            self.lblLogo.setPixmap(QPixmap(logo_path))

        self.btnDiagnostics.clicked.connect(lambda: self.changePage.emit(1, "Diagnostics"))
        self.btnShotMode.clicked.connect(lambda: self.changePage.emit(2, "Shot Mode"))
        self.btnData.clicked.connect(lambda: self.changePage.emit(7, "Data"))  # Updated to match page name




        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = FrontPage()
    window.show()
    sys.exit(app.exec())