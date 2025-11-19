from .SmartDotData import SmartDotData, SmartDotDataInstance
from .DiagnosticScriptData import DiagnosticScriptData, DiagnosticScriptDataInstance
from .SessionData import SessionData
from .ShotScriptData import ShotScriptData, ShotScriptDataInstance
from .EncoderData import EncoderData, EncoderDataInstance
from .HeatData import HeatData, HeatDataInstance

from BSC import bsc
import logging
logger = logging.getLogger(__name__)

class DataController:
    def __init__(self, session_data: SessionData):
        self.session_data = session_data
        self.smartdot_data = SmartDotData()
        self.diagnostic_script_data = DiagnosticScriptData()
        self.shot_script_data = ShotScriptData()
        self.encoder_data = EncoderData()
        self.heat_data = HeatData()
        self.cloud_api = bsc.get_cloud_api()

    def get_diagnostic_script_data(self,) -> DiagnosticScriptData:
        return self.diagnostic_script_data.get_diagnostic_script_data()
    
    def get_shot_script_data(self) -> ShotScriptData:
        return self.shot_script_data.get_shot_script_data_entries()

    def get_smartdot_data(self) -> SmartDotData:
        return self.smartdot_data.get_data_entries()

    def add_smartdot_data(self, smartDotData: SmartDotDataInstance):
        self.smartdot_data.add_new_data(smartDotData)
        logger.info(f"Added smartdot data: {smartDotData}")

    def add_diagnostic_script_data(self, diagnosticScriptData: DiagnosticScriptDataInstance):
        self.diagnostic_script_data.add_diagnostic_script_data(diagnosticScriptData)
        logger.info(f"Added diagnostic script data: {diagnosticScriptData}")

    def add_shot_script_data(self, shotScriptData: ShotScriptDataInstance):
        self.shot_script_data.add_shot_script_data(shotScriptData)
        logger.info(f"Added shot script data: {shotScriptData}")
        
    def add_encoder_data(self, encoderData: EncoderDataInstance):   
        self.encoder_data.add_encoder_data(encoderData)
        logger.info(f"Added encoder data: {encoderData}")

    def add_heat_data(self, heatData: HeatDataInstance):
        self.heat_data.add_heat_data(heatData)
        logger.info(f"Added heat data: {heatData}")

    def get_heat_data(self) -> HeatData:
        return self.heat_data.get_heat_data_entries()

    def get_encoder_data(self) -> EncoderData:
        return self.encoder_data.get_encoder_data_entries()

    def submit_session_data(self):
        #First we need to submit the session data to the cloud API
        session = self.cloud_api.post_session_data(self.session_data)
        #Grab the session id from the response
        session_id = session['data'][0]

        if self.session_data.isShotMode:
            #Submit the shot script data to the cloud API
            self.cloud_api.post_shot_script_data(self.shot_script_data.get_shot_script_data_entries(), session_id)
        else:
            #Submit the diagnostic script data to the cloud API
            self.cloud_api.post_diagnostic_script_data(self.diagnostic_script_data.get_diagnostic_script_data(), session_id)
        
        #Submit the smartdot data to the cloud API
        self.cloud_api.post_smartdot_data(self.smartdot_data.get_data_entries(), session_id)


        #Submit the encoder data to the cloud API
        self.cloud_api.post_encoder_data(self.encoder_data.get_encoder_data_entries(), session_id)
        
        #Submit the heat data to the cloud API
        self.cloud_api.post_heat_data(self.heat_data.get_heat_data_entries(), session_id)


    def load_session_data_from_cloud(self, session_data: SessionData):
        #Load the correct script data from the cloud API
        if session_data.isShotMode:
            #Load the shot script data from the cloud API
            ss_data = self.cloud_api.get_shot_script_data_by_session(session_data.id)
            for i in ss_data:
                self.shot_script_data.add_shot_script_data(ShotScriptDataInstance(time=i['time'], rpm=i['rpm'], angleDeg=i['angleDegrees'], tiltDeg=i['tiltDegrees']))
        else:
            #Load the diagnostic script data from the cloud API
            ds_data = self.cloud_api.get_diagnostic_script_data_by_session(session_data.id)
            for i in ds_data:
                self.diagnostic_script_data.add_diagnostic_script_data(DiagnosticScriptDataInstance(time=i['time'], motor_id=i['motorID'], instruction=i['instruction']))

        #load the smartdot data from the cloud API
        sd_data = self.cloud_api.get_smartdot_data(session_data.id)
        for i in sd_data:
            self.smartdot_data.add_smartdot_data(SmartDotDataInstance(time=i['time'], data_selector=i['dataSelector'], accelerometer_x=i['xL_X'], accelerometer_y=i['xL_Y'], accelerometer_z=i['xL_Z'], gyroscope_x=i['gY_X'], gyroscope_y=i['gY_Y'], gyroscope_z=i['gY_Z'], magnetometer_x=i['mG_X'], magnetometer_y=i['mG_Y'], magnetometer_z=i['mG_Z'], light=i['lt']))

        #load the encoder data from the cloud API
        enc_data = self.cloud_api.get_encoder_data(session_data.id)
        for i in enc_data:
            self.encoder_data.add_encoder_data(EncoderDataInstance(time=i['time'], pulses=i['pulses'], motor_id=i['motorId']))

        #load the heat data from the cloud API
        hd_data = self.cloud_api.get_heat_data(session_data.id)
        for i in hd_data:
            self.heat_data.add_heat_data(HeatDataInstance(time=i['time'], value=i['value'], motor_id=i['motorId']))

        print(f"Data Controller loaded from cloud: {self}")
        
    def __str__(self):
        return f"DataController(session_data={self.session_data}\n, smartdot_data={self.smartdot_data}\n, diagnostic_script_data={self.diagnostic_script_data}\n, shot_script_data={self.shot_script_data}\n, encoder_data={self.encoder_data}\n, heat_data={self.heat_data}\n)"