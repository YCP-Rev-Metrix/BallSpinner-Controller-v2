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


    def set_session_name(self, session_name: str):
        self.session_data.name = session_name
        logger.info(f"Set session name: {session_name}")

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
            shot_script_data = self.get_shot_script_data()
            if shot_script_data:
                self.cloud_api.post_shot_script_data(shot_script_data, session_id)
            else:
                logger.warning(f"No Shot Script Data found for this Shot Session {self.session_data}")
        else:
            #Submit the diagnostic script data to the cloud API
            diagnostic_script_data = self.get_diagnostic_script_data()
            if diagnostic_script_data:
                self.cloud_api.post_diagnostic_script_data(diagnostic_script_data, session_id)
            else:
                logger.warning(f"No Diagnostic Script Data found for this Shot Session {self.session_data}")
        
        #Submit the smartdot data to the cloud API
        smartdot_data = self.get_smartdot_data()
        for i in smartdot_data:
            print(f"JABGIAWBGOAWHG: {i.__str__()}")
        if smartdot_data:
            result = self.cloud_api.post_smartdot_data(smartdot_data, session_id)
            print(f"JABGIAWBGOAWHGJABGIAWBGOAWHG: {result}")
        else:
            logger.warning(f"No SmartDot Data found for this Shot Session {self.session_data}")


        #Submit the encoder data to the cloud API
        encoder_data = self.get_encoder_data()
        if encoder_data:
            self.cloud_api.post_encoder_data(encoder_data, session_id)
        else:
            logger.warning(f"No Encoder Data found for this Shot Session {self.session_data}")
        
        #Submit the heat data to the cloud API
        heat_data = self.get_heat_data()
        if heat_data:
            self.cloud_api.post_heat_data(heat_data, session_id)
        else:
            logger.warning(f"No Heat Data found for this Shot Session {self.session_data}")

    #ALL DATA WITH SESSION, Not JUST SESSION METADATA
    def load_session_data_from_cloud(self, session_data: SessionData):
        #Load the correct script data from the cloud API
        if session_data.isShotMode:
            #Load the shot script data from the cloud API
            ss_data = self.cloud_api.get_shot_script_data_by_session(session_data.id)
            print(f"Shot Script Data: {ss_data}")
            if ss_data:
                for i in ss_data['data']:
                    self.shot_script_data.add_shot_script_data(ShotScriptDataInstance(time=i['time'], rpm=i['rpm'], angleDeg=i['angleDegrees'], tiltDeg=i['tiltDegrees']))
            else:
                logger.warning(f"No Shot Mode Data found for this Shot Session {session_data}")
        else:
            #Load the diagnostic script data from the cloud API
            ds_data = self.cloud_api.get_diagnostic_script_data_by_session(session_data.id)
            # print(f"Diagnostic Script Data: {ds_data}")
            if ds_data:
                for i in ds_data['data']:
                    # print(f"Loading Diagnostic Script Data: {i}")
                    self.diagnostic_script_data.add_diagnostic_script_data(DiagnosticScriptDataInstance(time=i['time'], motor_id=i['motorId'], instruction=i['instruction']))
            else:
                logger.warning(f"No Diagnostic Mode Data found for this Shot Session {session_data}")

        #load the smartdot data from the cloud API
        sd_data = self.cloud_api.get_smartdot_data(session_data.id)
        if sd_data:
            for i in sd_data['data']:
                self.smartdot_data.add_new_data(SmartDotDataInstance(time=i['time'], data_selector=i['dataSelector'], accelerometer_x=i['xL_X'], accelerometer_y=i['xL_Y'], accelerometer_z=i['xL_Z'], gyroscope_x=i['gY_X'], gyroscope_y=i['gY_Y'], gyroscope_z=i['gY_Z'], magnetometer_x=i['mG_X'], magnetometer_y=i['mG_Y'], magnetometer_z=i['mG_Z'], light=i['lt']))
            else:
                logger.warning(f"No SmartDot Data found for this Shot Session {session_data}")

        #load the encoder data from the cloud API
        enc_data = self.cloud_api.get_encoder_data(session_data.id)
        if enc_data:
            for i in enc_data['data']:
                self.encoder_data.add_encoder_data(EncoderDataInstance(time=i['time'], pulses=i['pulses'], motor_id=i['motorId']))
        else:
            logger.warning(f"No Encoder Data found for this Shot Session {session_data}")

        #load the heat data from the cloud API
        hd_data = self.cloud_api.get_heat_data(session_data.id)
        if hd_data:
            for i in hd_data['data']:
                self.heat_data.add_heat_data(HeatDataInstance(time=i['time'], motor_id=i['motorId'], value=i['value']))
        else:
            logger.warning(f"No Heat Data found for this Shot Session {session_data}")

        print(f"Data Controller loaded from cloud: {self}")
        
    def __str__(self):
        return f"DataController(session_data={self.session_data}\n, smartdot_data={self.smartdot_data}\n, diagnostic_script_data={self.diagnostic_script_data}\n, shot_script_data={self.shot_script_data}\n, encoder_data={self.encoder_data}\n, heat_data={self.heat_data}\n)"