from PyQt6 import QtWidgets, uic
import os
from PyQt6.QtCore import pyqtSignal
import datetime as dt
from backend.models.EncoderData import EncoderDataInstance
from backend.models.HeatData import HeatDataInstance
from backend.models.SessionData import SessionData
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
        self.pushButton_10.clicked.connect(self.post_encoder_data)
        self.pushButton_11.clicked.connect(self.get_encoder_data)
        self.pushButton_12.clicked.connect(self.post_heat_data)
        self.pushButton_13.clicked.connect(self.get_heat_data)
        self.pushButton_14.clicked.connect(self.submit_all_data)
        self.pushButton_15.clicked.connect(self.load_session_data_from_cloud)
        self.cloud_api = bsc.get_cloud_api()

    def ask_cloud_for_6(self):
        """Handle the 'Ask Cloud for 6' button click"""
        #Ask the cloud for the test data
        # status_code, data = self.cloud_api.api_get_test_data()
        data = SessionData(id=-1,timeStamp=dt.datetime.now().isoformat(), name="Test Session", isShotMode=True)
        

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
        result = self.cloud_api.get_sessions_in_time_range(20251119,20251119)
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

    def post_encoder_data(self):
        print("Post Encoder Data clicked")

        artificial_encoder_data = [
                                    EncoderDataInstance(time=0.0, pulses=100, motor_id=1),
                                    EncoderDataInstance(time=0.1, pulses=200, motor_id=2),
                                    EncoderDataInstance(time=0.2, pulses=300, motor_id=3)
                                  ]
        # result = self.cloud_api.post_encoder_data(bsc.get_data_controller().get_encoder_data(), 1)
        result = self.cloud_api.post_encoder_data(artificial_encoder_data, 1)
        print(result)
    def get_encoder_data(self):
        print("Get Encoder Data clicked")
        result = self.cloud_api.get_encoder_data(1)
        print(result)
    def post_heat_data(self):
        print("Post Heat Data clicked")
        artificial_heat_data = [
                                HeatDataInstance(time=0.0, value=100, motor_id=1),
                                HeatDataInstance(time=0.1, value=200, motor_id=2),
                                HeatDataInstance(time=0.2, value=300, motor_id=3)
                              ]
    
        # result = self.cloud_api.post_heat_data(bsc.get_data_controller().get_heat_data(), 1)
        result = self.cloud_api.post_heat_data(artificial_heat_data, 1)
        print(result)
    def get_heat_data(self):
        print("Get Heat Data clicked")
        result = self.cloud_api.get_heat_data(1)
        print(result)

    def submit_all_data(self):
        print("Submit All Data clicked")
        bsc.get_data_controller().submit_session_data()
        print("All data submitted")

    def load_session_data_from_cloud(self):
        print("Load Session Data from Cloud clicked")
        session_id = self.spinBox_sessionId.value()
        bsc.get_data_controller().load_session_data_from_cloud(SessionData(id=session_id, timeStamp=dt.datetime.now().isoformat(), name="Diagnostic Session", isShotMode=False))
        print("Session data loaded from cloud")

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