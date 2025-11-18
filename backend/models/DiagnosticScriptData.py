from .SessionData import SessionData

class DiagnosticScriptDataInstance:
    def __init__(self, sessionData: SessionData, time: float, motor_id: int, instruction: float):
        self.time = time
        self.sessionData = sessionData
        self.motor_id = motor_id
        self.instruction = instruction

    def __str__(self):
        return f"DiagnosticScriptDataInstance(time={self.time}, sessionData={self.sessionData.get_id()}, motor_id={self.motor_id}, instruction={self.instruction})"

class DiagnosticScriptData:
    def __init__(self):
        self.diagnostic_script_data_entries = []  

    def add_diagnostic_script_data(self, diagnosticScriptData: DiagnosticScriptDataInstance):
        self.diagnostic_script_data_entries.append(diagnosticScriptData)

    def __str__(self):
        return f"DiagnosticScriptData(diagnostic_script_data_entries={self.diagnostic_script_data_entries})"