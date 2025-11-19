from PyQt6 import QtWidgets, uic
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
        self.btnAnalysis = self.findChild(QtWidgets.QPushButton, 'btnAnalysis')

        self.btnDiagnostics.clicked.connect(lambda: self.changePage.emit(1, "Diagnostics"))
        self.btnShotMode.clicked.connect(lambda: self.changePage.emit(2, "Shot Mode"))
        self.btnAnalysis.clicked.connect(lambda: self.changePage.emit(3, "Analysis"))  # Updated to match page name




        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = FrontPage()
    window.show()
    sys.exit(app.exec())