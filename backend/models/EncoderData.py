class EncoderDataInstance:
    def __init__(self, time: float, pulses: float, motor_id: int, replay_iteration: int):
        self.time = time
        self.pulses = pulses
        self.motor_id = motor_id
        self.replay_iteration = replay_iteration

    def get_time(self):
        return self.time

    def get_pulses(self):
        return self.pulses

    def get_motor_id(self):
        return self.motor_id

    def __str__(self):
        return f"EncoderDataInstance(time={self.time}, pulses={self.pulses}, motor_id={self.motor_id}, replay_iteration={self.replay_iteration})"

class EncoderData:
    def __init__(self):
        self.encoder_data_entries = []

    def add_encoder_data(self, encoder_data: EncoderDataInstance):
        self.encoder_data_entries.append(encoder_data)

    def get_encoder_data_entries(self):
        return self.encoder_data_entries

    def __str__(self):
        return f"EncoderData(encoder_data_entries={self.encoder_data_entries})"