import time
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QTimer
import numpy as np
from SmartDotGraph import SmartDotGraph
import math
from PyQt6.QtCore import pyqtSignal


class AnalysisModePage(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the UI file.
        uic.loadUi('AnalysisModePage.ui', self)



if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # Create and show the main window
    window = AnalysisModePage()
    window.setBaseSize(1920, 1080)
    window.setWindowTitle("Analysis Mode Page")
    window.show()

    # Start the event loop
    sys.exit(app.exec())
