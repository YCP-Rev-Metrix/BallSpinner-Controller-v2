class DiagnosticScriptDataInstance:
    def __init__(self, time: float, motor_id: int, instruction: float):
        self.time = time
        self.motor_id = motor_id
        self.instruction = instruction

    def __str__(self):
        return f"DiagnosticScriptDataInstance(time={self.time}, motor_id={self.motor_id}, instruction={self.instruction})"

class DiagnosticScriptData:
    def __init__(self):
        self.diagnostic_script_data_entries : DiagnosticScriptDataInstance = []  

    def add_diagnostic_script_data(self, diagnosticScriptData: DiagnosticScriptDataInstance):
        self.diagnostic_script_data_entries.append(diagnosticScriptData)

    def get_diagnostic_script_data(self):
        return self.diagnostic_script_data_entries
                
    def __str__(self):
        s = "" #Build data string
        for i in self.diagnostic_script_data_entries:
            s += f"{i.__str__()},"
        return f"DiagnosticScriptData: {s}"