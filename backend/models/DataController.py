from .SmartDotData import SmartDotData, SmartDotDataInstance
from .DiagnosticScriptData import DiagnosticScriptData, DiagnosticScriptDataInstance
from .SessionData import SessionData
from .ShotScriptData import ShotScriptData, ShotScriptDataInstance
from .EncoderData import EncoderData, EncoderDataInstance
from BSC import bsc
class DataController:
    def __init__(self, session_data: SessionData):
        self.session_data = session_data
        self.smartdot_data = SmartDotData()
        self.diagnostic_script_data = DiagnosticScriptData()
        self.shot_script_data = ShotScriptData()
        self.encoder_data = EncoderData()
        self.cloud_api = bsc.get_cloud_api()

    def add_smartdot_data(self, smartDotData: SmartDotDataInstance):
        self.smartdot_data.add_new_data(smartDotData)

    def add_diagnostic_script_data(self, diagnosticScriptData: DiagnosticScriptDataInstance):
        self.diagnostic_script_data.add_new_data(diagnosticScriptData)

    def add_shot_script_data(self, shotScriptData: ShotScriptDataInstance):
        self.shot_script_data.add_shot_script_data(shotScriptData)
    
    def add_encoder_data(self, encoderData: EncoderDataInstance):   
        self.encoder_data.add_encoder_data(encoderData)

    def submit_session_data(self):
        if self.session_data.isShotMode:
            self.cloud_api.submit_shot_mode_data(self.session_data, self.smartdot_data, self.shot_script_data, self.encoder_data)
        else:
            self.cloud_api.submit_diagnostic_mode_data(self.session_data, self.smartdot_data, self.diagnostic_script_data, self.encoder_data)


    def __str__(self):
        return f"DataController(session_data={self.session_data}\n, smartdot_data={self.smartdot_data}\n, diagnostic_script_data={self.diagnostic_script_data}\n, shot_script_data={self.shot_script_data}\n, encoder_data={self.encoder_data}\n)"