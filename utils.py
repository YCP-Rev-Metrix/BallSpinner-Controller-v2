import io
import os
def is_raspberry_pi():
    """Checks if the code is running on a Raspberry Pi."""
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                return True
    except FileNotFoundError:
        pass
    return False

def is_raspberry_pi_5():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi 5' in m.read().lower():
                return True
    except FileNotFoundError:
        pass
    return False


def PackageSmartDotData(self,bsc):
    dc = bsc.get_data_controller()
        # Load SmartDot data from BSC data controller
    smartdot_data = dc.smartdot_data

    self.time_accel = []
    self.accel_x = []
    self.accel_y = []
    self.accel_z = []
    self.time_gyro = []
    self.gyro_x = []
    self.gyro_y = []
    self.gyro_z = []
    self.time_mag = []
    self.mag_x = []
    self.mag_y = []
    self.mag_z = []
    self.time_light = []
    self.light = []

    for data in smartdot_data.data_entries:
        #print(f"SmartDot Data - Time: {data.time}, Selector: {data.data_selector}, AccelX: {data.accelerometer_x}, AccelY: {data.accelerometer_y}, AccelZ: {data.accelerometer_z}, GyroX: {data.gyroscope_x}, GyroY: {data.gyroscope_y}, GyroZ: {data.gyroscope_z}, MagX: {data.magnetometer_x}, MagY: {data.magnetometer_y}, MagZ: {data.magnetometer_z}, Light: {data.light}")
        if data.data_selector == 0:  # Accelerometer
            self.time_accel.append(data.time)
            self.accel_x.append(data.accelerometer_x)
            self.accel_y.append(data.accelerometer_y)
            self.accel_z.append(data.accelerometer_z)
        elif data.data_selector == 1:  # Gyroscope
            self.time_gyro.append(data.time)
            self.gyro_x.append(data.gyroscope_x)
            self.gyro_y.append(data.gyroscope_y)
            self.gyro_z.append(data.gyroscope_z)
        elif data.data_selector == 2:  # Magnetometer
            self.time_mag.append(data.time)
            self.mag_x.append(data.magnetometer_x)
            self.mag_y.append(data.magnetometer_y)
            self.mag_z.append(data.magnetometer_z)
        elif data.data_selector == 3:  # Light
            self.time_light.append(data.time)
            self.light.append(data.light)
    return SmartDotDataPackage(
        self.time_accel, self.accel_x, self.accel_y, self.accel_z,
        self.time_gyro, self.gyro_x, self.gyro_y, self.gyro_z,
        self.time_mag, self.mag_x, self.mag_y, self.mag_z,
        self.time_light, self.light
    )
def PackageMotorData(self,bsc):
            # Load Motor data from BSC data controller
    dc = bsc.get_data_controller()

    time_motor = []
    time_rpm = []
    time_angle = []
    time_tilt = []
    motor_rpm = []
    motor_angleDeg = []
    motor_tiltDeg = []

    if hasattr(dc, 'shot_script_data'):
        motor_data = dc.shot_script_data.get_shot_script_data_entries()
        for data in motor_data:
            time_motor.append(data.time)
            motor_rpm.append(data.rpm)
            motor_angleDeg.append(data.angleDeg)
            motor_tiltDeg.append(data.tiltDeg)
            #print(f"Motor Data - Time: {data.time}, RPM: {data.rpm}, AngleDeg: {data.angleDeg}, TiltDeg: {data.tiltDeg}")
        time_rpm = time_motor
        time_angle = time_motor
        time_tilt = time_motor
    elif hasattr(dc, 'diagnostic_data'):
        motor_data = dc.diagnostic_data.get_diagnostic_data_entries()
        for data in motor_data:
            match data.motor_id:
                case 0:
                    time_rpm.append(data.time)
                    motor_rpm.append(data.instruction)
                case 1:
                    time_angle.append(data.time)
                    motor_angleDeg.append(data.instruction)
                case 2:
                    time_tilt.append(data.time)
                    motor_tiltDeg.append(data.instruction)
                case _:
                    pass  
    else:
        print("No motor data available in DataController.")  
    # Load Encoder data from BSC data controller
    #TODO: Implement encoder data packaging when available
    time_encoder = [0.0]
    encoder_rpm = [0.0]
    encoder_angle = [0.0]
    encoder_tilt = [0.0]

    return MotorDataPackage(
        time_rpm, motor_rpm, time_angle, motor_angleDeg, time_tilt, motor_tiltDeg,
        time_encoder, encoder_rpm, encoder_angle, encoder_tilt
    )

class SmartDotDataPackage:
    def __init__(self, time_accel, accel_x, accel_y, accel_z,
                 time_gyro, gyro_x, gyro_y, gyro_z,
                 time_mag, mag_x, mag_y, mag_z,
                 time_light, light):
        self.time_accel = time_accel
        self.accel_x = accel_x
        self.accel_y = accel_y
        self.accel_z = accel_z
        self.time_gyro = time_gyro
        self.gyro_x = gyro_x
        self.gyro_y = gyro_y
        self.gyro_z = gyro_z
        self.time_mag = time_mag
        self.mag_x = mag_x
        self.mag_y = mag_y
        self.mag_z = mag_z
        self.time_light = time_light
        self.light = light

class MotorDataPackage:
    def __init__(self, time_rpm, motor_rpm, time_angle, motor_angleDeg, time_tilt, motor_tiltDeg,
                 time_encoder, encoder_rpm, encoder_angle, encoder_tilt):
        self.time_rpm = time_rpm
        self.motor_rpm = motor_rpm
        self.time_angle = time_angle
        self.motor_angleDeg = motor_angleDeg
        self.time_tilt = time_tilt
        self.motor_tiltDeg = motor_tiltDeg
        self.time_encoder = time_encoder
        self.encoder_rpm = encoder_rpm
        self.encoder_angle = encoder_angle
        self.encoder_tilt = encoder_tilt
