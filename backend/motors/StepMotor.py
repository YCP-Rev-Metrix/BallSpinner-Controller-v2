try:
    import lgpio
except ImportError:
    lgpio = None
import time
import threading
from typing import Optional
#from .iMotor import iMotor

# ================================
# GPIO PIN DEFINITIONS (BCM MODE)
# ================================
# STEP_PIN drives the PUL- input on the stepper driver (e.g. DM542).
# Each rising edge (or full high+low pulse, depending on driver) is one microstep.
#STEP_PIN = 23  # BCM 23 -> PUL-

# DIR_PIN drives the DIR- input on the stepper driver.
# Changing this pin HIGH/LOW changes the motor rotation direction (CW/CCW),
# as long as the driver's DIR+ is tied to a stable logic voltage (e.g. 3.3 V or 5 V)
# and there is a common ground between the Pi and the driver.
#DIR_PIN  = 24  # BCM 24 -> DIR-

# ================================
# MOTION / MECHANICAL PARAMETERS
# ================================
# This is the total number of microsteps per full revolution of the motor shaft.
# It depends on:
#   - The motor's native full-step count (commonly 200 full steps/rev)
#   - The microstepping setting on the driver (e.g. 8x, 16x, etc.)
#
# Example:
#   200 full steps/rev * 8x microstepping = 1600 steps/rev
STEPS_PER_REV = 25000  # adjust if you change microstepping on the driver

class StepMotor():

    DEFAULT_KP = 0.1
    DEFAULT_DUTY_CYCLE_SCALE = 0.000043333333

    motorID = 0
    currSpeed = 0.0
    targetSpeed = 0.0
    targetPower = 0.0
    GPIO_Pin = 0
    motor = None
    STEP_PIN = 0 
    DIR_PIN  = STEP_PIN + 1

    motor_degrees = [0.0]
    motor_times = [0.0]
    count = 0
    #h = lgpio.gpiochip_open(0) moved to BSC.py
    h = 0 #default to 0, will be set to the handle in BSC.py
    connected = True
    #t = threading.Thread()#target=run_movement_chain, daemon=True)
    prev_angle = 0.0
    current_angle = 0.0

    def stop(self):
        #self.t.join()  # Wait for the thread to finish before continuing
        if self.connected and self.h:
            try:
                lgpio.gpio_write(self.h, self.STEP_PIN, 0)
                lgpio.gpio_write(self.h, self.DIR_PIN, 0)
                if hasattr(self, "ENABLE_PIN") and self.ENABLE_PIN is not None:
                    self.disable()
                    lgpio.gpio_free(self.h, self.ENABLE_PIN)
                # Free the GPIO pins so they can be claimed again
                lgpio.gpio_free(self.h, self.STEP_PIN)
                lgpio.gpio_free(self.h, self.DIR_PIN)
            except Exception as e:
                print(f"Error freeing GPIO pins for motor {self.GPIO_Pin}: {e}")
        self.connected = False
        # Don't set h to None here - BSC manages the handle
        print(f"GPIO released for motor on pin {self.GPIO_Pin}")

    @property
    def Kp(self) -> float:
        return self._Kp

    @Kp.setter
    def Kp(self, value: float):
        self._Kp = value

    @property
    def duty_cycle_scale(self) -> float:
        return self._duty_cycle_scale

    @duty_cycle_scale.setter
    def duty_cycle_scale(self, value: float):
        self._duty_cycle_scale = value

    def disconnect(self):
        # Close the gpiochip handle to release resources.
        if(self.connected):
            self.stop()
    
    def __init__(
        self,
        GPIO_Pin,
        DIR_Pin,
        h,
        enable_pin=None,
        enable_active_low=True,
        current_sensor=None,
        current_sensor_channel=None,
    ):
        self.GPIO_Pin = GPIO_Pin
        self.STEP_PIN = GPIO_Pin
        self.DIR_PIN = DIR_Pin
        self.h = h
        self.ENABLE_PIN = enable_pin
        self._enable_active_low = enable_active_low
        self._current_sensor = current_sensor
        self._current_sensor_channel = current_sensor_channel

        # Motor settings (needed for UI controls / interface compatibility)
        self._Kp = self.DEFAULT_KP
        self._duty_cycle_scale = self.DEFAULT_DUTY_CYCLE_SCALE

        if not (self.connected):
            self.h = lgpio.gpiochip_open(0)
            self.connected = True

        # Setup pins
        lgpio.gpio_claim_output(self.h, self.STEP_PIN, 0)
        lgpio.gpio_claim_output(self.h, self.DIR_PIN, 0)
        if self.ENABLE_PIN is not None:
            lgpio.gpio_claim_output(self.h, self.ENABLE_PIN, 1 if self._enable_active_low else 0)
            # Ensure motor is enabled by default
            self.disable()  # Start with motor disabled; caller can enable when ready

        self.movement_in_progress = False  # Track if a movement is currently running
        self.movement_lock = threading.Lock()  # Lock for thread safety
        self.current_angle = 0.0

    def _write_enable(self, enabled: bool):
        """Write to the enable pin (if configured) taking active-low into account."""
        if self.ENABLE_PIN is None:
            return
        if self._enable_active_low:
            lgpio.gpio_write(self.h, self.ENABLE_PIN, 0 if enabled else 1)
        else:
            lgpio.gpio_write(self.h, self.ENABLE_PIN, 1 if enabled else 0)

    def enable(self):
        """Enable the stepper driver (assert enable pin)."""
        self._write_enable(True)

    def disable(self):
        """Disable the stepper driver (deassert enable pin)."""
        self._write_enable(False)

    def start(self, rpm=1):
        # Check if handle is valid, reopen if needed
        if self.h:
            try:
                # Test if handle is valid
                lgpio.gpio_read(self.h, self.STEP_PIN)
            except Exception:
                # Handle is invalid (closed), reopen it
                self.h = lgpio.gpiochip_open(0)
        else:
            # No handle, open it
            self.h = lgpio.gpiochip_open(0)
        
        # If pins might already be claimed, try to free them first
        try:
            # Try to free pins if they're already claimed (won't error if not claimed)
            lgpio.gpio_free(self.h, self.STEP_PIN)
            lgpio.gpio_free(self.h, self.DIR_PIN)
        except Exception:
            pass  # Pins weren't claimed, that's fine
        
        if not (self.connected):
            self.connected = True
            lgpio.gpio_claim_output(self.h, self.STEP_PIN, 0)
            lgpio.gpio_claim_output(self.h, self.DIR_PIN, 0)
            self.movement_in_progress = False  # Track if a movement is currently running
            self.movement_lock = threading.Lock()  # Lock for thread safety

        # Ensure enable line is asserted before moving
        if self.ENABLE_PIN is not None:
            self.enable()

        self.count = 0  # Reset counter for new sequence
        self.movement_in_progress = False
        self.current_angle = 0.0  # Track current position
        # Don't move here - wait for first changeSpeed call

    def changeSpeed(self, dutyCycle: float, isShotMode: bool):
        angle = dutyCycle # so i dont have to fix imotor lol
        #This not being fixed lead me down a rabbit 
        if not (isShotMode):
            isClockwise = True
            new_angle = angle - self.prev_angle
            if(new_angle<0):
                new_angle = new_angle * -1
                isClockwise = False
                
            self.prev_angle = angle

            move_angle_timeds(
                self.h,
                step_pin=self.STEP_PIN,
                dir_pin=self.DIR_PIN,
                angle_deg=new_angle,
                total_time_s=0.1,
                clockwise=isClockwise,
            )
            self.current_angle = angle
        else:
            # Reactive approach: move towards target angle each time step
            target_angle = angle
            angle_diff = target_angle - self.current_angle
            
            if abs(angle_diff) > 0.01:  # Only move if significant difference
                # Get dt from ShotViewPage - we need to pass it or calculate it
                # For now, use a small default that will be overridden
                # You'll need to pass dt as a parameter or store it
                dt = 0.1  # This should come from the caller or be stored
                
                # Determine direction
                isClockwise = angle_diff > 0
                
                # Move the difference over the time interval
                move_angle_timeds(
                    self.h,
                    step_pin=self.STEP_PIN,
                    dir_pin=self.DIR_PIN,
                    angle_deg=abs(angle_diff),
                    total_time_s=dt,
                    clockwise=isClockwise,
                )
                
                self.current_angle = target_angle  # Update current position
            else:
                self.current_angle = target_angle

        print(f"step motor on pin{self.GPIO_Pin} running and moving to {angle} degrees")

    def returnToZero(self):
        if not self.connected or not self.h:
            return
        angle_to_move = self.current_angle
        if abs(angle_to_move) < 0.01:
            self.current_angle = 0.0
            self.prev_angle = 0.0
            return
        isClockwise = angle_to_move < 0
        move_angle_timeds(
            self.h,
            step_pin=self.STEP_PIN,
            dir_pin=self.DIR_PIN,
            angle_deg=abs(angle_to_move),
            total_time_s=0.1,
            clockwise=isClockwise,
        )
        self.current_angle = 0.0
        self.prev_angle = 0.0

    def setCurrentPositionZero(self):
        self.current_angle = 0.0
        self.prev_angle = 0.0

    
    def _start_movement_sequence(self):
        """Start the sequence of movements through all waypoints"""
        if self.count >= len(self.motor_degrees):
            return  # Already completed all waypoints
        
        import threading
        
        def run_movement_chain():
            """Chain movements together - each movement triggers the next"""
            with self.movement_lock:
                if self.movement_in_progress:
                    return  # Already running
                self.movement_in_progress = True
            
            try:
                # Move through all waypoints sequentially
                while self.count < len(self.motor_degrees):
                    if self.count == 0:
                        # First movement: from 0 to first waypoint
                        if len(self.motor_degrees) == 0:
                            break
                        
                        target_angle = self.motor_degrees[0]
                        time_to_use = self.motor_times[1] if len(self.motor_times) > 1 else (self.motor_times[0] if len(self.motor_times) > 0 else 1.0)
                        
                        if abs(target_angle) > 0.01:  # Only move if significant
                            print(f"Moving to waypoint {self.count}: {target_angle}° in {time_to_use}s")
                            move_angle_timeds(
                                self.h,
                                step_pin=self.STEP_PIN,
                                dir_pin=self.DIR_PIN,
                                angle_deg=abs(target_angle),
                                total_time_s=time_to_use,
                                clockwise=(target_angle > 0),
                            )
                        self.count += 1
                    else:
                        # Subsequent movements: from previous waypoint to current waypoint
                        if self.count >= len(self.motor_degrees):
                            break
                        
                        angle_diff = self.motor_degrees[self.count] - self.motor_degrees[self.count-1]
                        time_to_use = self.motor_times[self.count] if self.count < len(self.motor_times) else 1.0
                        
                        if abs(angle_diff) > 0.01:  # Only move if significant difference
                            print(f"Moving to waypoint {self.count}: {self.motor_degrees[self.count]}° (Δ{angle_diff}°) in {time_to_use}s")
                            move_angle_timeds(
                                self.h,
                                step_pin=self.STEP_PIN,
                                dir_pin=self.DIR_PIN,
                                angle_deg=abs(angle_diff),
                                total_time_s=time_to_use,
                                clockwise=(angle_diff > 0),
                            )
                        self.count += 1
                
                # After completing all waypoints, move back to 0
                if len(self.motor_degrees) > 0:
                    final_angle = self.motor_degrees[-1]
                    if abs(final_angle) > 0.01:  # Only move if not already at 0
                        # Use the last time interval, or default to 1 second
                        time_to_zero = self.motor_times[-1] if len(self.motor_times) > 0 else 1.0
                        print(f"Returning to 0° from {final_angle}° in {time_to_zero}s")
                        move_angle_timeds(
                            self.h,
                            step_pin=self.STEP_PIN,
                            dir_pin=self.DIR_PIN,
                            angle_deg=abs(final_angle),
                            total_time_s=time_to_zero,
                            clockwise=(final_angle < 0),  # Opposite direction to return to 0
                        )
                
                print(f"Movement sequence complete. Returned to 0°")
            finally:
                with self.movement_lock:
                    self.movement_in_progress = False

        self.t = threading.Thread(target=run_movement_chain, daemon=True)
        self.t.start()  # Start the thread instead of calling directly

    def getCurrentSpeed(self):
        return self.currSpeed

    def getVals(self):
        """Return diagnostic sensor data for this stepper motor.

        This method is used by the UI diagnostic code path. It returns a dictionary
        with the keys expected by the existing motor sensor handling:
            - input_current: current in amps or None when unavailable
            - temp_motor: temperature, always None for stepper/INA240 today
        """
        current = None
        if self._current_sensor is not None and self._current_sensor_channel is not None:
            try:
                current = self._current_sensor.read_current(self._current_sensor_channel)
            except Exception as e:
                print(f"Error reading current sensor for motor on pin {self.GPIO_Pin}: {e}")

        return {"input_current": current, "temp_motor": None}

    def rampUp(self):
        pass

    def rampDown(self):
        pass

    def setDutyCycle(self, dutyCycle: int):
        pass

    def interpolate(self, arr):
        """
        Given an array of float values, finds all local maxima and minima (points where the sequence changes direction)
        and updates self.motor_degrees to those values, and self.motor_times to their indexes.

        Arguments:
            arr (list of float): array of float values representing the function to analyze
        """
        if len(arr) < 2:
            # Not enough data to determine switch points
            self.motor_degrees = arr[:]
            self.motor_times = list(range(len(arr)))
            return

        switch_indexes = []
        switch_values = []

        direction = 0  # 1 = increasing, -1 = decreasing, 0 = not yet determined

        for i in range(1, len(arr)):
            delta = arr[i] - arr[i-1]
            new_direction = 1 if delta > 0 else (-1 if delta < 0 else 0)

            # Detect a change in direction (excluding first transition)
            if direction != 0 and new_direction != 0 and new_direction != direction:
                # Local min or max at the previous point (i-1)
                switch_indexes.append(i-1)
                switch_values.append(arr[i-1])
            # Update direction if changed and not zero
            if new_direction != 0:
                direction = new_direction

        # Always add the last point as a switch if not already present
        if not switch_indexes or switch_indexes[-1] != len(arr)-1:
            switch_indexes.append(len(arr)-1)
            switch_values.append(arr[-1])

        self.motor_degrees = switch_values
        self.motor_times = switch_indexes

    def set_motor_times_from_indices(self, arr):
        """
        Given an array, set self.motor_times to the values at the indexes currently specified in self.motor_times.
        This replaces the indexes (self.motor_times) with the values from arr at those positions.

        Arguments:
            arr (list or array-like): Source array of values.
        """
        if not hasattr(self, 'motor_times'):
            return
        # Ensure all indices are within range
        self.motor_times = [arr[i] for i in self.motor_times if 0 <= i < len(arr)]
        self.motor_times = self.difference_array(self.motor_times)

    def difference_array(self, arr):
        """
        Given an array of values, return a new array where each element is the difference between the value and the previous value.
        The first element will be value[0] - 0.
        
        Arguments:
            arr (list or array-like): Source array of values.
        Returns:
            list of float: Array of differences.
        """
        if not arr:
            return []
        diffs = [arr[0] - 0]
        for i in range(1, len(arr)):
            diffs.append(arr[i] - arr[i-1])
        return diffs




def pulse(h, step_pin, half_delay):
    """
    Generate a single STEP pulse on 'step_pin' using software bit-banging.

    The pulse shape is:
        HIGH for 'half_delay' seconds,
        then LOW for 'half_delay' seconds.

    So one full step period = 2 * half_delay.
    That period determines the effective step frequency (speed).
    """
    # Drive STEP high (this is one edge of the step pulse)
    lgpio.gpio_write(h, step_pin, 1)
    time.sleep(half_delay)

    # Drive STEP low to complete the pulse
    lgpio.gpio_write(h, step_pin, 0)
    time.sleep(half_delay)


def move_angle_timeds(h, step_pin, dir_pin, angle_deg, total_time_s, clockwise=True):
    """
    Move the stepper motor by a given mechanical angle in a specified time.

    Parameters
    ----------
    h : int
        Handle to the opened gpiochip (from lgpio.gpiochip_open).
    step_pin : int
        BCM pin number connected to the PUL- (STEP-) input of the driver.
    dir_pin : int
        BCM pin number connected to the DIR- input of the driver.
    angle_deg : float
        Target mechanical angle in degrees. Positive values are assumed.
        This function uses abs(angle_deg) so it works if the caller passes
        a negative angle by accident.
    total_time_s : float
        Desired total time (in seconds) for this move to complete.
        The function computes the necessary time per step to hit this target.
    clockwise : bool
        Direction flag:
            True  -> GPIO level mapped to "clockwise" (as wired)
            False -> opposite direction

        NOTE: Whether "clockwise" actually matches physical CW on your rig
        depends on motor wiring and driver configuration. If it's reversed,
        simply swap the 0/1 mapping below or swap one motor coil on the driver.
    """
    # --------------------------
    # 1) Set the DIRECTION pin
    # --------------------------
    # Here we map:
    #   clockwise=True  -> DIR = 0
    #   clockwise=False -> DIR = 1
    #
    # If the physical direction is reversed, flip these two values:
    #   lgpio.gpio_write(h, dir_pin, 1 if clockwise else 0)
    lgpio.gpio_write(h, dir_pin, 0 if clockwise else 1)

    # Allow a short settling time for the direction signal
    # before we start issuing step pulses. Some drivers require
    # a minimum DIR setup time relative to the STEP edge.
    time.sleep(0.01)

    # --------------------------
    # 2) Compute number of steps
    # --------------------------
    # Convert desired angle in degrees to number of microsteps.
    # Fraction of full rotation = angle_deg / 360.0
    # Steps for that fraction  = STEPS_PER_REV * (angle_deg / 360.0)
    steps = int(round(STEPS_PER_REV * (abs(angle_deg) / 360.0)))
    if steps <= 0:
        # Nothing to do if the angle is too small or zero.
        return

    # --------------------------
    # 3) Compute timing per step
    # --------------------------
    # We want the entire move (all 'steps') to take 'total_time_s'.
    # Each step consists of a HIGH and LOW interval:
    #   time_per_step = total_time_s / steps
    #   half_delay    = time_per_step / 2
    #
    # Final behavior:
    #   steps * (2 * half_delay) = total_time_s
    time_per_step = total_time_s / steps
    half_delay = time_per_step / 2.0

    # Print debug info to console so you can confirm the math at runtime.
    print(
        f"Moving {angle_deg}° in {total_time_s:.3f}s -> "
        f"{steps} steps, {time_per_step*1000:.3f} ms/step"
    )

    # --------------------------
    # 4) Issue step pulses
    # --------------------------
    for _ in range(steps):
        pulse(h, step_pin, half_delay)


'''
def main():
    """
    Main entry point:
    - Opens the gpiochip
    - Claims the STEP and DIR pins as outputs
    - Executes a single 90° move in 4 seconds (clockwise)
    - Cleans up GPIO on exit
    """
    # Open gpiochip 0 (typically the default GPIO controller on the Pi).
    # h is a handle that we pass to all subsequent lgpio calls.
    h = lgpio.gpiochip_open(0)

    # Configure STEP and DIR pins as outputs and initialize them LOW.
    # NOTE: These levels only affect the - (negative) terminals on the driver
    # when using low-level control (e.g., PUL- and DIR- to GPIO, PUL+ and DIR+ to 3.3V/5V).
    lgpio.gpio_claim_output(h, STEP_PIN, 0)
    lgpio.gpio_claim_output(h, DIR_PIN, 0)

    try:
        # ------------------------------------------
        # Example motion:
        #   - Move 90 degrees clockwise in 4 seconds
        # ------------------------------------------
        print("90° CW in 4 seconds...")
        move_angle_timeds(
            h,
            step_pin=STEP_PIN,
            dir_pin=DIR_PIN,
            angle_deg=360.0,
            total_time_s=4.0,
            clockwise=True,
        )
        time.sleep(0.5)

        # If you want to test the opposite direction as well, you can
        # uncomment the block below. This will move the motor back 90°
        # in 4 seconds using the opposite DIR level.
        """
        print("90° CCW in 4 seconds...")
        move_angle_timeds(
            h,
            step_pin=STEP_PIN,
            dir_pin=DIR_PIN,
            angle_deg=90.0,
            total_time_s=4.0,
            clockwise=False,
        )
        """

        print("Done.")

    finally:
        # --------------------------
        # GPIO CLEANUP
        # --------------------------
        # Ensure outputs are set LOW before releasing them.
        # This prevents leaving stray pulses or direction signals active.
        lgpio.gpio_write(h, STEP_PIN, 0)
        lgpio.gpio_write(h, DIR_PIN, 0)

        # Close the gpiochip handle to release resources.
        lgpio.gpiochip_close(h)
        print("GPIO released.")

'''
if __name__ == "__main__":
    main()
