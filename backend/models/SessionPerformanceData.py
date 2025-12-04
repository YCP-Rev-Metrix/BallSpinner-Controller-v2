from .ShotScriptData import ShotScriptData


class MotorCommandPerformanceInstance:
    """
    Represents a single motor command performance record.
    Tracks timing data for motor commands: when instruction started, when command was sent, and when it returned.
    """
    def __init__(self, motor_id: int, instruction_start_time: float, command_sent_time: float, command_return_time: float):
        self.motor_id = motor_id
        self.instruction_start_time = instruction_start_time
        self.command_sent_time = command_sent_time
        self.command_return_time = command_return_time

    def get_motor_id(self):
        return self.motor_id

    def get_instruction_start_time(self):
        return self.instruction_start_time

    def get_command_sent_time(self):
        return self.command_sent_time

    def get_command_return_time(self):
        return self.command_return_time

    def get_command_latency(self):
        """Calculate the time between command sent and command return."""
        return self.command_return_time - self.command_sent_time

    def get_total_instruction_time(self):
        """Calculate the total time from instruction start to command return."""
        return self.command_return_time - self.instruction_start_time

    def __str__(self):
        return f"MotorCommandPerformanceInstance(motor_id={self.motor_id}, instruction_start_time={self.instruction_start_time}, command_sent_time={self.command_sent_time}, command_return_time={self.command_return_time})"


class SessionPerformanceData:
    """
    Collects data about motor performance vs what we actually tell them.
    Tracks the total instruction set from the Data Model, total elapsed time of the session,
    and a list of motor command performance data pairs.
    """
    def __init__(self, shot_script_data: ShotScriptData = None):
        # Collect the total instruction set from the Data Model
        self.shot_script_data = shot_script_data
        
        # Collect the total elapsed time of the session
        self.total_elapsed_time: float = 0.0
        
        # Collect a list of these data pairs (Motor id, motor instruction start time, time command to motor sent, time command returns)
        self.motor_command_performance_entries: list[MotorCommandPerformanceInstance] = []

    def set_shot_script_data(self, shot_script_data: ShotScriptData):
        """Set the total instruction set from the Data Model."""
        self.shot_script_data = shot_script_data

    def get_shot_script_data(self) -> ShotScriptData:
        """Get the total instruction set from the Data Model."""
        return self.shot_script_data

    def set_total_elapsed_time(self, elapsed_time: float):
        """Set the total elapsed time of the session."""
        self.total_elapsed_time = elapsed_time

    def get_total_elapsed_time(self) -> float:
        """Get the total elapsed time of the session."""
        return self.total_elapsed_time

    def add_motor_command_performance(self, motor_command_performance: MotorCommandPerformanceInstance):
        """Add a motor command performance record."""
        self.motor_command_performance_entries.append(motor_command_performance)

    def get_motor_command_performance_entries(self) -> list[MotorCommandPerformanceInstance]:
        """Get all motor command performance entries."""
        return self.motor_command_performance_entries

    def __str__(self):
        return f"SessionPerformanceData(shot_script_data={self.shot_script_data}, total_elapsed_time={self.total_elapsed_time}, motor_command_performance_entries={len(self.motor_command_performance_entries)} entries)"
