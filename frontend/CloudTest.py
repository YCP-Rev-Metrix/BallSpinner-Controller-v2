from PyQt6 import QtWidgets, uic
import os
from backend.cloud_api.CloudAPI import api_get_test_data

class CloudTest(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'cloudTest.ui'), self, package='frontend')
        
        # Connect button signals to their respective functions
        self.pushButton.clicked.connect(self.ask_cloud_for_6)
        self.pushButton_2.clicked.connect(self.clear_label)
    
    def ask_cloud_for_6(self):
        """Handle the 'Ask Cloud for 6' button click"""
        #Ask the cloud for the test data
        status_code, data = api_get_test_data()
        if status_code == 200:
            self.label.setText(str(data))
        else:
            self.label.setText("Error: " + data)
    
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