class ShotScriptDataInstance:
    def __init__(self, time: float, rpm: float, angleDeg: float, tiltDeg: float):
        self.time = time
        self.rpm = rpm
        self.angleDeg = angleDeg
        self.tiltDeg = tiltDeg

    def get_time(self):
        return self.time

    def get_rpm(self):
        return self.rpm

    def get_angle_deg(self):
        return self.angleDeg

    def get_tilt_deg(self):
        return self.tiltDeg

    def __str__(self):
        return f"\nShotScriptDataInstance(time={self.time}, rpm={self.rpm}, angleDeg={self.angleDeg}, tiltDeg={self.tiltDeg})"


class ShotScriptData:
    def __init__(self):
        self.shot_script_data_entries: ShotScriptDataInstance = []

    def add_shot_script_data(self, shotScriptData: ShotScriptDataInstance):
        self.shot_script_data_entries.append(shotScriptData)
        # #print(f"Added ssdataInstance: {self.shot_script_data_entries[len(self.shot_script_data_entries)-1]}")
        
    
    def get_shot_script_data_entries(self):
        return self.shot_script_data_entries

    def __str__(self):
        #Build data string
        s = ""
        for i in self.shot_script_data_entries:
            s += f"{i.__str__()}," 

        return f"ShotScriptDatas: {s}"