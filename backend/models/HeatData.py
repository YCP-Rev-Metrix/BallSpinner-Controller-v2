class HeatDataInstance:
    def __init__(self, time: float, motor_id: int, value: float, replay_iteration: int):
        self.time = time
        self.motor_id = motor_id
        self.value = value
        self.replay_iteration = replay_iteration

    def get_time(self):
        return self.time
    def get_motor_id(self):
        return self.motor_id
    def get_value(self):
        return self.value

    def __str__(self):
        return f"HeatDataInstance(time={self.time}, motor_id={self.motor_id}, value={self.value}, replay_iteration={self.replay_iteration})"

class HeatData:
    def __init__(self):
        self.heat_data_entries = []

    def add_heat_data(self, heat_data: HeatDataInstance):
        self.heat_data_entries.append(heat_data)

    def get_heat_data_entries(self):
        return self.heat_data_entries   

    def __str__(self):
        s = ""
        for i in self.heat_data_entries:
            s += f"{i.__str__()},"
        return f"HeatData: {s}"