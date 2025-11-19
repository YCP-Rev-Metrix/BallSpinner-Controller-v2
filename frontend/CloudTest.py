from PyQt6 import QtWidgets, uic
import os
from PyQt6.QtCore import pyqtSignal
import datetime as dt

from BSC import bsc

class CloudTest(QtWidgets.QWidget):
    changePage = pyqtSignal(int, str)

    
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'cloudTest.ui'), self, package='frontend')
        
        # Connect button signals to their respective functions
        self.pushButton.clicked.connect(self.ask_cloud_for_6)
        self.pushButton_2.clicked.connect(self.clear_label)
        self.pushButton_3.clicked.connect(self.get_sessions)
        self.pushButton_4.clicked.connect(self.post_smart_dot_data)
        self.pushButton_5.clicked.connect(self.get_smart_dot_data)
        self.pushButton_6.clicked.connect(self.get_diagnostic_data)
        self.pushButton_7.clicked.connect(self.post_diagnostic_data)
        self.pushButton_8.clicked.connect(self.post_shot_script_data)
        self.pushButton_9.clicked.connect(self.get_shot_script_data)
    
        self.cloud_api = bsc.get_cloud_api()

    def ask_cloud_for_6(self):
        """Handle the 'Ask Cloud for 6' button click"""
        #Ask the cloud for the test data
        # status_code, data = self.cloud_api.api_get_test_data()
        data = [
            {"id": -1,
            "timeStamp": dt.datetime.now().isoformat(),
            "name": "Test Session",
            "isShotMode": True,
            }
        ]

        result = self.cloud_api.post_session_data(data)
        print(result)
        # if status_code == 200:
        #     self.label.setText(str(data))
        # else:
        #     self.label.setText("Error: " + data)
    
    def clear_label(self):
        """Handle the 'Clear Label' button click"""
        # Clear the label text
        self.label.setText("Response")
        print("Label cleared")
    
    def get_sessions(self):
        """Handle the 'Get Sessions' button click"""
        #Get all sessions in the time range
        result = self.cloud_api.get_sessions_in_time_range(0,0)
        print("Get Sessions clicked")
        print(result)


    def post_smart_dot_data(self):
        """Handle the 'Post Smart Dot Data' button click"""
        print("Post Smart Dot Data clicked")
        result = self.cloud_api.post_smartdot_data(bsc.get_data_controller().get_smartdot_data(),1)
        print(result)
    
    def get_smart_dot_data(self):
        """Handle the 'Get Smart Dot Data' button click"""
        print("get diagnostic data")
        result = self.cloud_api.get_smartdot_data(1)
        print(result)
    
    def get_diagnostic_data(self):
        """Handle the 'Get Diagnostic Data' button click"""
        print("Get Diagnostic Data clicked")
        result = self.cloud_api.get_all_diagnostic_script_data_by_session(1)
        print(result)
    
    def post_diagnostic_data(self):
        """Handle the 'Post Diagnostic Data' button click"""
        print("Post Diagnostic Data clicked")
        result = self.cloud_api.post_diagnostic_script_data(bsc.get_data_controller().get_diagnostic_script_data(), 1)
        print(result)


    def post_shot_script_data(self):
        """Handle the 'Post Shot Script Data' button click"""
        print("Post Shot Script Data clicked")
        result = self.cloud_api.post_shot_script_data(bsc.get_data_controller().get_shot_script_data(), 1)
        print(result)
    
    def get_shot_script_data(self):
        """Handle the 'Get Shot Script Data' button click"""
        print("Get Shot Script Data clicked")
        result = self.cloud_api.get_shot_script_data_by_session(1)
        print(result)


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