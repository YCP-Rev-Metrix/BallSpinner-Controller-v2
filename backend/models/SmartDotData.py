class SmartDotDataInstance:
    def __init__(self, time, data_selector, accelerometer_x, accelerometer_y, accelerometer_z, gyroscope_x, gyroscope_y, gyroscope_z, magnetometer_x, magnetometer_y, magnetometer_z, light):
        self.time = time
        self.data_selector = data_selector
        self.accelerometer_x = accelerometer_x
        self.accelerometer_y = accelerometer_y
        self.accelerometer_z = accelerometer_z
        self.gyroscope_x = gyroscope_x
        self.gyroscope_y = gyroscope_y
        self.gyroscope_z = gyroscope_z
        self.magnetometer_x = magnetometer_x
        self.magnetometer_y = magnetometer_y
        self.magnetometer_z = magnetometer_z
        self.light = light

    # def get_data(self):
    #     if self.data_selector == 0:
    #         return self.accelerometer_x, self.accelerometer_y, self.accelerometer_z
    #     elif self.data_selector == 1:
    #         return self.gyroscope_x, self.gyroscope_y, self.gyroscope_z
    #     elif self.data_selector == 2:
    #         return self.magnetometer_x, self.magnetometer_y, self.magnetometer_z
    #     elif self.data_selector == 3:
    #         return self.light

    def __str__(self):
        return f"SmartDotDataInstance(time={self.time}, data_selector={self.data_selector}, accelerometer_x={self.accelerometer_x}, accelerometer_y={self.accelerometer_y}, accelerometer_z={self.accelerometer_z}, gyroscope_x={self.gyroscope_x}, gyroscope_y={self.gyroscope_y}, gyroscope_z={self.gyroscope_z}, magnetometer_x={self.magnetometer_x}, magnetometer_y={self.magnetometer_y}, magnetometer_z={self.magnetometer_z}, light={self.light})"

class SmartDotData:
    def __init__(self):
        self.data_entries = []

    def get_data_entries(self):
        return self.data_entries
    def add_new_data(self, smartDotData: SmartDotDataInstance):
        self.data_entries.append(smartDotData)

    def __str__(self):
        return f"SmartDotData(data_entries={self.data_entries})"

