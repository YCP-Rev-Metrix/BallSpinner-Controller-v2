import datetime

class SessionData:
    def __init__(
        self,
        id: int,
        timeStamp: datetime.datetime,
        name: str,
        isShotMode: bool,
        Spin_Instruction_Points=None,
        Angle_Instruction_Points=None,
        Tilt_Instruction_Points=None,
    ):

        if id is None:
            self.id = -1
        else:
            self.id = id

        self.timeStamp = timeStamp
        self.name = name
        self.isShotMode = isShotMode

        # Avoid mutable default args
        self.Spin_Instruction_Points = Spin_Instruction_Points or []
        self.Angle_Instruction_Points = Angle_Instruction_Points or []
        self.Tilt_Instruction_Points = Tilt_Instruction_Points or []

    def get_id(self):
        return self.id

    def get_time_stamp(self):
        return self.timeStamp

    def get_name(self):
        return self.name

    def get_is_shot_mode(self):
        return self.isShotMode

    def __str__(self):
        return f"SessionData(id={self.id}, timeStamp={self.timeStamp}, name={self.name}, isShotMode={self.isShotMode})"
    
    def set_spin_instruction_points(self, spin_points):
        self.Spin_Instruction_Points = spin_points

    def set_angle_instruction_points(self, angle_points):
        self.Angle_Instruction_Points = angle_points

    def set_tilt_instruction_points(self, tilt_points):
        self.Tilt_Instruction_Points = tilt_points

    def get_spin_instruction_points(self):
        return self.Spin_Instruction_Points

    def get_angle_instruction_points(self):
        return self.Angle_Instruction_Points

    def get_tilt_instruction_points(self):
        return self.Tilt_Instruction_Points
        