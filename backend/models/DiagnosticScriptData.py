from .SessionData import SessionData

class DiagnosticScriptDataInstance:
    def __init__(self, sessionData: SessionData, time: float, motor_id: int, instruction: float):
        self.time = time
        self.sessionData = sessionData
        self.motor_id = motor_id
        self.instruction = instruction

class DiagnosticScriptData:
    def __init__(self):
        self.diagnostic_script_data_entries = []  

    def add_diagnostic_script_data(self, diagnosticScriptData: DiagnosticScriptDataInstance):
        self.diagnostic_script_data_entries.append(diagnosticScriptData)