from logs.logger_config import get_logger
#from motors.BDCMotor import BDCMotor
from backend.motors.SimMotor import SimMotor
logger = get_logger(__name__)

class ShotScript:
    def __init__(self, motor1, motor2, motor3):
        self.motors = [motor1, motor2, motor3]

    def start_motors(self, values):
        if len(values) != 3:
            logger.error("start_motors: must provide 3 values for 3 motors.")
            return

        for i, motor in enumerate(self.motors):
            try:
                motor.start(float(values[i]))
                logger.info(f"Started motor {i + 1} with value {values[i]}")
            except Exception as e:
                logger.error(f"Error starting motor {i + 1}: {e}")

    def stop_motors(self, values=None):
        if values is not None:
            if len(values) != 3:
                logger.warning("stop_motors: values parameter provided but ignored (stop() does not accept parameters).")
        for i, motor in enumerate(self.motors):
            try:
                motor.stop()
                logger.info(f"Stopped motor {i + 1}")
            except Exception as e:
                logger.error(f"Error stopping motor {i + 1}: {e}")
    #change Speed instruction for all three motors at once
    def change_speed(self, values):
        if len(values) != 3:
            logger.error("change_speed: must provide 3 values for 3 motors.")
            return
        for i, motor in enumerate(self.motors):
            try:
                motor.changeSpeed(float(values[i]), True)
                logger.info(f"Changed speed of motor {i + 1} to {values[i]}")
            except Exception as e:
                logger.error(f"Error changing speed of motor {i + 1}: {e}")
    
    #Change instruction for a single motor
    def change_speed_single(self, motor_index, value):
        if motor_index < 0 or motor_index >= len(self.motors):
            logger.error("change_speed_single: invalid motor index.")
            return
        try:
            self.motors[motor_index].changeSpeed(float(value), True)
            logger.info(f"Changed speed of motor {motor_index + 1} to {value}")
        except Exception as e:
            logger.error(f"Error changing speed of motor {motor_index + 1}: {e}")

