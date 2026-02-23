import numpy as np
import io
import os
import logging
from array import array
import pywt
logger = logging.getLogger(__name__)

def get_series_defs(parent=None):
    # Use parent's color attributes if available
    return {
        "smartdot": {
            "accel_x": {"label": "Accel X", "time": "time_accel", "data": "accel_x", "color": getattr(parent, 'accxColor', None), "deriv": True, "fft": True},
            "accel_y": {"label": "Accel Y", "time": "time_accel", "data": "accel_y", "color": getattr(parent, 'accyColor', None), "deriv": True, "fft": True},
            "accel_z": {"label": "Accel Z", "time": "time_accel", "data": "accel_z", "color": getattr(parent, 'acczColor', None), "deriv": True, "fft": True},
            "gyro_x": {"label": "Gyro X", "time": "time_gyro", "data": "gyro_x", "color": getattr(parent, 'gyroxColor', None), "deriv": True, "fft": True},
            "gyro_y": {"label": "Gyro Y", "time": "time_gyro", "data": "gyro_y", "color": getattr(parent, 'gyroyColor', None), "deriv": True, "fft": True},
            "gyro_z": {"label": "Gyro Z", "time": "time_gyro", "data": "gyro_z", "color": getattr(parent, 'gyrozColor', None), "deriv": True, "fft": True},
            "mag_x": {"label": "Mag X", "time": "time_mag", "data": "mag_x", "color": getattr(parent, 'magxColor', None), "deriv": True, "fft": True},
            "mag_y": {"label": "Mag Y", "time": "time_mag", "data": "mag_y", "color": getattr(parent, 'magyColor', None), "deriv": True, "fft": True},
            "mag_z": {"label": "Mag Z", "time": "time_mag", "data": "mag_z", "color": getattr(parent, 'magzColor', None), "deriv": True, "fft": True},
            "light": {"label": "Light", "time": "time_light", "data": "light", "color": getattr(parent, 'lightColor', None), "deriv": False, "fft": False},
        },
        "motor": {
            "motor_rpm": {"label": "Motor RPM", "time": "time_rpm", "data": "motor_rpm", "color": getattr(parent, 'motorRPMColor', None), "deriv": True, "fft": True},
            "motor_angle": {"label": "Motor Angle", "time": "time_angle", "data": "motor_angleDeg", "color": getattr(parent, 'motorAngleColor', None), "deriv": True, "fft": True},
            "motor_tilt": {"label": "Motor Tilt", "time": "time_tilt", "data": "motor_tiltDeg", "color": getattr(parent, 'motorTiltColor', None), "deriv": True, "fft": True},
            "encoder_rpm": {"label": "Encoder RPM", "time": "time_encoder", "data": "encoder_rpm", "color": getattr(parent, 'encoderRPMColor', None), "deriv": True, "fft": True},
            "encoder_angle": {"label": "Encoder Angle", "time": "time_encoder", "data": "encoder_angle", "color": getattr(parent, 'encoderAngleColor', None), "deriv": True, "fft": True},
            "encoder_tilt": {"label": "Encoder Tilt", "time": "time_encoder", "data": "encoder_tilt", "color": getattr(parent, 'encoderTiltColor', None), "deriv": True, "fft": True},
        },
    }

def series_arrays(package, defs):
    series = {}
    for key, meta in defs.items():
        time_values = np.array(getattr(package, meta["time"], []), dtype=np.float64)
        data_values = np.array(getattr(package, meta["data"], []), dtype=np.float64)
        series[key] = (time_values, data_values)
    return series




def bandpass_wavelet(values, wavelet='db4', level=2):
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return arr.copy()
    try:
        coeffs = pywt.wavedec(arr, wavelet, level=level)
    except Exception:
        # if decomposition fails just return original
        return arr.copy()
    # keep only the detail coefficients at level-1 (middle band) if available
    # coeffs structure: [cA_n, cD_n, cD_{n-1}, ..., cD1]
    # we zero every coefficient except the one at index 2 (cD_{n}) when level=2
    for i in range(len(coeffs)):
        if i != 2:
            coeffs[i] = np.zeros_like(coeffs[i])
    try:
        rec = pywt.waverec(coeffs, wavelet)
    except Exception:
        return arr.copy()
    # trim/pad to original length
    if len(rec) > len(arr):
        rec = rec[: len(arr)]
    elif len(rec) < len(arr):
        rec = np.pad(rec, (0, len(arr) - len(rec)), mode='edge')
    return rec


def is_raspberry_pi():
    """Checks if the code is running on a Raspberry Pi."""
    logger.debug("Checking if running on Raspberry Pi")
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                logger.info("Detected Raspberry Pi")
                return True
    except FileNotFoundError:
        logger.debug("Device tree model file not found, not running on Raspberry Pi")
    logger.debug("Not running on Raspberry Pi")
    return False

def is_raspberry_pi_5():
    """Checks if the code is running on a Raspberry Pi 5."""
    logger.debug("Checking if running on Raspberry Pi 5")
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi 5' in m.read().lower():
                logger.info("Detected Raspberry Pi 5")
                return True
    except FileNotFoundError:
        logger.debug("Device tree model file not found, not running on Raspberry Pi 5")
    logger.debug("Not running on Raspberry Pi 5")
    return False


def PackageSmartDotData(self,bsc):
    logger.info("Starting PackageSmartDotData")
    dc = bsc.get_data_controller()
        # Load SmartDot data from BSC data controller
    smartdot_data = dc.smartdot_data
    logger.debug(f"Retrieved {len(smartdot_data.data_entries)} SmartDot data entries")

    self.time_accel = array('d')
    self.accel_x = array('f')
    self.accel_y = array('f')
    self.accel_z = array('f')
    self.time_gyro = array('d')
    self.gyro_x = array('f')
    self.gyro_y = array('f')
    self.gyro_z = array('f')
    self.time_mag = array('d')
    self.mag_x = array('f')
    self.mag_y = array('f')
    self.mag_z = array('f')
    self.time_light = array('d')
    self.light = array('f')

    accel_count = 0
    gyro_count = 0
    mag_count = 0
    light_count = 0
    for data in smartdot_data.data_entries:
        #print(f"SmartDot Data - Time: {data.time}, Selector: {data.data_selector}, AccelX: {data.accelerometer_x}, AccelY: {data.accelerometer_y}, AccelZ: {data.accelerometer_z}, GyroX: {data.gyroscope_x}, GyroY: {data.gyroscope_y}, GyroZ: {data.gyroscope_z}, MagX: {data.magnetometer_x}, MagY: {data.magnetometer_y}, MagZ: {data.magnetometer_z}, Light: {data.light}")
        if data.data_selector == 0:  # Accelerometer
            self.time_accel.append(data.time)
            self.accel_x.append(data.accelerometer_x)
            self.accel_y.append(data.accelerometer_y)
            self.accel_z.append(data.accelerometer_z)
            accel_count += 1
        elif data.data_selector == 1:  # Gyroscope
            self.time_gyro.append(data.time)
            self.gyro_x.append(data.gyroscope_x)
            self.gyro_y.append(data.gyroscope_y)
            self.gyro_z.append(data.gyroscope_z)
            gyro_count += 1
        elif data.data_selector == 2:  # Magnetometer
            self.time_mag.append(data.time)
            self.mag_x.append(data.magnetometer_x)
            self.mag_y.append(data.magnetometer_y)
            self.mag_z.append(data.magnetometer_z)
            mag_count += 1
        elif data.data_selector == 3:  # Light
            self.time_light.append(data.time)
            self.light.append(data.light)
            light_count += 1
    logger.info(f"Packaged SmartDot data - Accelerometer: {accel_count}, Gyroscope: {gyro_count}, Magnetometer: {mag_count}, Light: {light_count}")
    logger.debug("PackageSmartDotData completed successfully")
    return SmartDotDataPackage(
        self.time_accel, self.accel_x, self.accel_y, self.accel_z,
        self.time_gyro, self.gyro_x, self.gyro_y, self.gyro_z,
        self.time_mag, self.mag_x, self.mag_y, self.mag_z,
        self.time_light, self.light
    )


def LegacyDiagnosticPacking(motor_data, time_rpm, motor_rpm, time_angle, motor_angleDeg, time_tilt, motor_tiltDeg, interval=None):
    """Legacy diagnostic packing logic, factored out for compatibility."""
    if interval is None:
        interval = 0.05  # default 50ms
    # Separate motor data by motor_id
    rpm_data = {}  # time -> instruction
    angle_data = {}  # time -> instruction
    tilt_data = {}  # time -> instruction
    all_times = []

    for data in motor_data:
        all_times.append(data.time)
        if data.motor_id == 0:  # RPM
            rpm_data[data.time] = data.instruction
            logger.debug(f"RPM at {data.time}: {data.instruction}")
        elif data.motor_id == 1:  # Angle
            angle_data[data.time] = data.instruction
            logger.debug(f"Angle at {data.time}: {data.instruction}")
        elif data.motor_id == 2:  # Tilt
            tilt_data[data.time] = data.instruction
            logger.debug(f"Tilt at {data.time}: {data.instruction}")

    # Create regular time grid at fixed interval
    if all_times:
        min_time = min(all_times)
        max_time = max(all_times)
        num_points = int((max_time - min_time) / interval) + 1
        regular_times = [min_time + i * interval for i in range(num_points)]
        logger.debug(f"Regular time grid: {len(regular_times)} points from {regular_times[0]:.3f} to {regular_times[-1]:.3f} at {interval*1000:.0f}ms intervals")

        # Forward-fill values: populate each motor array across the regular time grid
        last_rpm = 0.0
        last_angle = 0.0
        last_tilt = 0.0

        for t in regular_times:
            # Find the most recent command at or before this time for each motor
            for cmd_time in sorted(rpm_data.keys()):
                if cmd_time <= t:
                    last_rpm = rpm_data[cmd_time]
            for cmd_time in sorted(angle_data.keys()):
                if cmd_time <= t:
                    last_angle = angle_data[cmd_time]
            for cmd_time in sorted(tilt_data.keys()):
                if cmd_time <= t:
                    last_tilt = tilt_data[cmd_time]

            # Append to all three arrays with regular time
            time_rpm.append(t)
            motor_rpm.append(last_rpm)
            time_angle.append(t)
            motor_angleDeg.append(last_angle)
            time_tilt.append(t)
            motor_tiltDeg.append(last_tilt)

        logger.info(f"Packaged diagnostic data with {interval*1000:.0f}ms regular intervals: RPM={len(motor_rpm)}, Angle={len(motor_angleDeg)}, Tilt={len(motor_tiltDeg)}")
def PackageMotorData(self,bsc):
            # Load Motor data from BSC data controller
    dc = bsc.get_data_controller()
    logger.info("Starting PackageMotorData")

    time_motor = array('d')
    time_rpm = array('d')
    time_angle = array('d')
    time_tilt = array('d')
    motor_rpm = array('f')
    motor_angleDeg = array('f')
    motor_tiltDeg = array('f')

    if dc.session_data.isShotMode:
        #Shot Mode
        logger.debug("Processing shot mode motor data")
        motor_data = dc.shot_script_data.get_shot_script_data_entries()
        logger.debug(f"Retrieved {len(motor_data)} shot script entries")
        for data in motor_data:
            time_motor.append(data.time)
            motor_rpm.append(data.rpm)
            motor_angleDeg.append(data.angleDeg)
            motor_tiltDeg.append(data.tiltDeg)
            #print(f"Motor Data - Time: {data.time}, RPM: {data.rpm}, AngleDeg: {data.angleDeg}, TiltDeg: {data.tiltDeg}")
        time_rpm = time_motor
        time_angle = time_motor
        time_tilt = time_motor
        logger.info(f"Packaged shot mode data: {len(motor_rpm)} RPM entries")
    else:
        #Diagnostic Mode
        logger.debug("Processing diagnostic mode motor data")
        motor_data = dc.diagnostic_script_data.get_diagnostic_script_data() #why are these different names? Brian?
        logger.debug(f"Retrieved {len(motor_data)} diagnostic entries")
        sample_interval = bsc.diagnostic_sample_interval_ms / 1000.0  # convert ms to seconds
        #See if data is already at the configured sample intervals
        if motor_data and abs(motor_data[-1].time - round(motor_data[-1].time / sample_interval) * sample_interval) < 1e-6:
            logger.debug(f"Data already at {bsc.diagnostic_sample_interval_ms}ms intervals, packaging with forward-fill")
            # Separate by motor_id
            rpm_data = {}
            angle_data = {}
            tilt_data = {}
            
            for data in motor_data:
                if data.motor_id == 0:
                    rpm_data[data.time] = data.instruction
                elif data.motor_id == 1:
                    angle_data[data.time] = data.instruction
                elif data.motor_id == 2:
                    tilt_data[data.time] = data.instruction
            
            # Build time grid from 0 to max time
            max_time = motor_data[-1].time
            num_points = int(round(max_time / sample_interval)) + 1
            
            last_rpm = last_angle = last_tilt = 0.0
            
            for i in range(num_points):
                t = i * sample_interval
                
                # Update last values if new data exists at this time
                if t in rpm_data:
                    last_rpm = rpm_data[t]
                if t in angle_data:
                    last_angle = angle_data[t]
                if t in tilt_data:
                    last_tilt = tilt_data[t]
                
                # Append synchronized values
                time_rpm.append(t)
                motor_rpm.append(last_rpm)
                time_angle.append(t)
                motor_angleDeg.append(last_angle)
                time_tilt.append(t)
                motor_tiltDeg.append(last_tilt)
            
            logger.info(f"Packaged diagnostic data on-grid with forward-fill: {len(motor_rpm)} RPM entries")
        else:
            logger.debug(f"Data not at {bsc.diagnostic_sample_interval_ms}ms intervals, using legacy packing")
            LegacyDiagnosticPacking(motor_data, time_rpm, motor_rpm, time_angle, motor_angleDeg, time_tilt, motor_tiltDeg, interval=sample_interval)
    #Ensure all arrays have something to prevent errors downstream
    






    
    #TODO: Implement encoder data packaging when available
    time_encoder = array('d', [0.0])
    encoder_rpm = array('f', [0.0])
    encoder_angle = array('f', [0.0])
    encoder_tilt = array('f', [0.0])
    logger.debug("Encoder data not yet implemented")

    logger.info("PackageMotorData completed successfully")
    logger.debug(f"Final data: RPM={len(motor_rpm)}, Angle={len(motor_angleDeg)}, Tilt={len(motor_tiltDeg)}")
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
