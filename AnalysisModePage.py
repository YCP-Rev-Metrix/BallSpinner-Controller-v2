from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt

class AnalysisModePage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load the UI file.
        uic.loadUi('AnalysisModePage.ui', self)
        # Additional initialization code can go here
        

if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = AnalysisModePage()
    window.setGeometry(100, 100, 800, 600) # x, y, width, height
    window.setWindowTitle("Analysis Mode Page")
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

