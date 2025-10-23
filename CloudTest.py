from PyQt6 import QtWidgets, uic

class CloudTest(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('cloudTest.ui', self)
        
        # Connect button signals to their respective functions
        self.pushButton.clicked.connect(self.ask_cloud_for_6)
        self.pushButton_2.clicked.connect(self.clear_label)
    
    def ask_cloud_for_6(self):
        """Handle the 'Ask Cloud for 6' button click"""
        # Update the label with some response
        self.label.setText("Cloud says: 6")
        print("Asked cloud for 6")
    
    def clear_label(self):
        """Handle the 'Clear Label' button click"""
        # Clear the label text
        self.label.setText("Response")
        print("Label cleared")


if __name__ == '__main__':
    # Standard boilerplate for a PyQt application
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show the main window
    window = CloudTest()
    window.setGeometry(100, 100, 800, 600) # x, y, width, height
    window.setWindowTitle("Cloud Test")
    window.show()
    sys.exit(app.exec())