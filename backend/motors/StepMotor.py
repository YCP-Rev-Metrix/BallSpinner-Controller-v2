try:
    import lgpio
except ImportError:
    lgpio = None
import time
import threading
from typing import Optional, Tuple
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

DEFAULT_HOMING_CFG = {
    "phase_timeout_s": 120.0,
    "max_search_steps": STEPS_PER_REV * 5,
    "backoff_clear_steps": 80,
    "first_sweep_clockwise": False,
    "limit_sample_angle_deg": 1.0,
    "limit_backoff_angle_deg": 1.0,
    "homing_search_half_delay_s": 0.001,
    # Max time for a single “back off until switch opens” phase (per release call).
    "limit_release_timeout_s": 2.5,
}


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
        limit_switch_pin=None,
        limit_switch_active_low=False,
        homing_config=None,
    ):
        self.GPIO_Pin = GPIO_Pin
        self.STEP_PIN = GPIO_Pin
        self.DIR_PIN = DIR_Pin
        self.h = h
        self.ENABLE_PIN = enable_pin
        self._enable_active_low = enable_active_low
        self._current_sensor = current_sensor
        self._current_sensor_channel = current_sensor_channel
        self._limit_switch_pin = limit_switch_pin
        self._limit_switch_active_low = limit_switch_active_low
        self.current_step_position = 0
        self._last_limit_fault = None
        self._homing_cfg = dict(DEFAULT_HOMING_CFG)
        if isinstance(homing_config, dict):
            self._homing_cfg.update(homing_config)

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

    def _set_limit_fault(self, reason: str):
        self._last_limit_fault = str(reason)
        print(f"StepMotor limit fault (GPIO {self.GPIO_Pin}): {self._last_limit_fault}")
        self._signal_primary_motor_fault(self._last_limit_fault)

    def _clear_limit_fault(self):
        self._last_limit_fault = None

    def get_last_limit_fault(self):
        return self._last_limit_fault

    def _signal_primary_motor_fault(self, reason: Optional[str] = None):
        """If the primary motor is actively running, use its built-in fault light."""
        try:
            from BSC import bsc
            primary = getattr(bsc, "motor1", None)
            if primary is None or not hasattr(primary, "trigger_fault"):
                return
            active_now = False
            for attr in ("targetSpeed", "currSpeed"):
                val = getattr(primary, attr, 0.0)
                if isinstance(val, (int, float)) and abs(val) > 1.0:
                    active_now = True
                    break
            if active_now:
                reason_txt = (reason or "").lower()
                fault_code = 8 if "stuck" in reason_txt else 5
                primary.trigger_fault(fault_code)
        except Exception:
            pass

    def set_homing_config(self, cfg: dict) -> None:
        if isinstance(cfg, dict):
            self._homing_cfg.update(cfg)

    def _steps_for_angle(self, angle_deg: float) -> int:
        return int(round(STEPS_PER_REV * (abs(angle_deg) / 360.0)))

    def _is_limit_active(self) -> bool:
        if lgpio is None or not self.h:
            return False
        limit_pin = self._limit_switch_pin
        if limit_pin is None:
            return False
        try:
            raw = bool(lgpio.gpio_read(self.h, limit_pin))
            return (not raw) if self._limit_switch_active_low else raw
        except Exception:
            return False

    def _set_direction(self, clockwise: bool):
        lgpio.gpio_write(self.h, self.DIR_PIN, 0 if clockwise else 1)
        time.sleep(0.001)

    def _single_step(self, clockwise: bool, half_delay: float = 0.0005):
        self._set_direction(clockwise)
        pulse(self.h, self.STEP_PIN, half_delay)
        self.current_step_position += 1 if clockwise else -1

    def _move_steps_timed_plain(self, steps: int, total_time_s: float, clockwise: bool) -> int:
        """Pulse steps with timing; no limit checks (used when no limit GPIO)."""
        if steps <= 0:
            return 0
        time_per_step = total_time_s / max(steps, 1)
        half_delay = max(0.00001, time_per_step / 2.0)
        self._set_direction(clockwise)
        for _ in range(steps):
            pulse(self.h, self.STEP_PIN, half_delay)
            self.current_step_position += 1 if clockwise else -1
        return steps

    def _move_steps_timed(self, steps: int, total_time_s: float, clockwise: bool) -> Tuple[int, bool]:
        """Returns (steps moved in commanded direction, limit_hit).

        With a limit GPIO: advance in ~1° chunks, read limit once per chunk; on hit back off
        ``limit_backoff_angle_deg`` in the opposite direction (no limit checks during backoff).
        """
        if steps <= 0:
            return (0, False)
        if self._limit_switch_pin is None:
            return (self._move_steps_timed_plain(steps, total_time_s, clockwise), False)

        hc = self._homing_cfg
        sample_deg = float(hc.get("limit_sample_angle_deg", 1.0))
        backoff_deg = float(hc.get("limit_backoff_angle_deg", 1.0))
        chunk_steps = max(1, self._steps_for_angle(sample_deg))
        backoff_steps = max(1, self._steps_for_angle(backoff_deg))

        time_per_step = total_time_s / max(steps, 1)
        half_delay = max(0.00001, time_per_step / 2.0)
        moved = 0
        while moved < steps:
            batch = min(chunk_steps, steps - moved)
            self._set_direction(clockwise)
            for _ in range(batch):
                pulse(self.h, self.STEP_PIN, half_delay)
                self.current_step_position += 1 if clockwise else -1
                moved += 1
            if self._is_limit_active():
                self._set_direction(not clockwise)
                for _ in range(backoff_steps):
                    pulse(self.h, self.STEP_PIN, half_delay)
                    self.current_step_position += 1 if (not clockwise) else -1
                return (moved, True)
        return (moved, False)

    def _move_angle_timed(self, angle_deg: float, total_time_s: float, clockwise: bool) -> Tuple[int, bool]:
        """Returns (steps_moved_in_command_direction, limit_hit). Updates ``current_angle`` if limit hit."""
        steps = self._steps_for_angle(angle_deg)
        ca0 = self.current_angle
        moved, hit = self._move_steps_timed(steps, total_time_s, clockwise)
        if hit:
            bd = float(self._homing_cfg.get("limit_backoff_angle_deg", 1.0))
            moved_deg = 360.0 * moved / STEPS_PER_REV
            net_deg = moved_deg - bd
            self.current_angle = ca0 + (1 if clockwise else -1) * net_deg
        return (moved, hit)

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
        self.current_angle = 0.0
        self.prev_angle = 0.0
        self.current_step_position = 0

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

        # Re-claim STEP/DIR every time. The class default ``connected = True`` means the
        # old ``if not self.connected`` branch was often skipped after gpio_free, leaving
        # STEP/DIR unclaimed so pulses did not drive the driver (motor appeared "disabled").
        try:
            lgpio.gpio_free(self.h, self.STEP_PIN)
            lgpio.gpio_free(self.h, self.DIR_PIN)
        except Exception:
            pass
        lgpio.gpio_claim_output(self.h, self.STEP_PIN, 0)
        lgpio.gpio_claim_output(self.h, self.DIR_PIN, 0)

        self.connected = True
        if not hasattr(self, "movement_lock") or self.movement_lock is None:
            self.movement_lock = threading.Lock()

        # After stop(), ENABLE was freed; reclaim then assert enabled level.
        if self.ENABLE_PIN is not None:
            try:
                lgpio.gpio_free(self.h, self.ENABLE_PIN)
            except Exception:
                pass
            lgpio.gpio_claim_output(self.h, self.ENABLE_PIN, 1 if self._enable_active_low else 0)
            self.enable()

        self.count = 0  # Reset counter for new sequence
        self.movement_in_progress = False
        self.current_angle = 0.0  # Track current position
        self._clear_limit_fault()
        # Don't move here - wait for first changeSpeed call

    def changeSpeed(self, dutyCycle: float, isShotMode: bool, dt_s: Optional[float] = None):
        angle = dutyCycle # so i dont have to fix imotor lol
        #This not being fixed lead me down a rabbit 
        with self.movement_lock:
            if not (isShotMode):
                isClockwise = True
                new_angle = angle - self.prev_angle
                if(new_angle<0):
                    new_angle = new_angle * -1
                    isClockwise = False
                    
                self.prev_angle = angle

                moved_steps, hit_limit = self._move_angle_timed(
                    angle_deg=new_angle,
                    total_time_s=0.1,
                    clockwise=isClockwise,
                )
                expected_steps = self._steps_for_angle(new_angle)
                if hit_limit:
                    self._set_limit_fault("Limit hit while tracking manual angle command.")
                elif moved_steps == expected_steps:
                    self.current_angle = angle
                    self._clear_limit_fault()
                else:
                    self.current_angle += (360.0 * moved_steps / STEPS_PER_REV) * (1 if isClockwise else -1)
            else:
                # Reactive approach: move towards target angle each time step
                target_angle = angle
                angle_diff = target_angle - self.current_angle
                
                if abs(angle_diff) > 0.01:  # Only move if significant difference
                    dt = float(dt_s) if dt_s and dt_s > 0.0 else 0.1
                    
                    # Determine direction
                    isClockwise = angle_diff > 0
                    
                    # Move the difference over the time interval
                    moved_steps, hit_limit = self._move_angle_timed(
                        angle_deg=abs(angle_diff),
                        total_time_s=dt,
                        clockwise=isClockwise,
                    )
                    expected_steps = self._steps_for_angle(abs(angle_diff))
                    if hit_limit:
                        self._set_limit_fault("Limit hit during shot-mode angle tracking.")
                    elif moved_steps == expected_steps:
                        self.current_angle = target_angle
                        self._clear_limit_fault()
                    else:
                        direction = 1 if isClockwise else -1
                        self.current_angle += (360.0 * moved_steps / STEPS_PER_REV) * direction
                else:
                    self.current_angle = target_angle
                    self._clear_limit_fault()

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
        _, hit_limit = self._move_angle_timed(
            angle_deg=abs(angle_to_move),
            total_time_s=0.1,
            clockwise=isClockwise,
        )
        if not hit_limit:
            self.current_angle = 0.0
            self.prev_angle = 0.0
            self.current_step_position = 0
        else:
            self.prev_angle = self.current_angle

    def setCurrentPositionZero(self):
        self.current_angle = 0.0
        self.prev_angle = 0.0
        self.current_step_position = 0

    def _release_limit_switch(
        self,
        half_delay: float,
        backoff_clear: int,
        phase_deadline: float,
        approach_clockwise: Optional[bool] = None,
    ) -> bool:
        """Clear the limit: step until the switch opens or the release timeout expires.

        When ``approach_clockwise`` is known, the switch was closed while moving in that
        direction; we **only** step in the opposite direction (away from that motion) until
        open or timeout. A shared limit can trip from either side — stepping again in the
        approach direction would drive back into the trip, so we never do that here.

        When ``approach_clockwise`` is unknown (e.g. homing starts on the switch), fall back
        to long single-direction bursts in each direction.

        Wall time is capped by ``limit_release_timeout_s`` and ``phase_deadline``.
        """
        max_burst = max(backoff_clear * 12, 800)
        release_budget = float(self._homing_cfg.get("limit_release_timeout_s", 2.5))
        release_deadline = min(phase_deadline, time.monotonic() + release_budget)

        def burst_clear(clockwise: bool, max_steps: int, until: float) -> bool:
            """Return True if switch opens before max_steps or ``until`` deadline."""
            for _ in range(max_steps):
                if not self._is_limit_active():
                    return True
                if time.monotonic() > until:
                    return False
                self._single_step(clockwise, half_delay)
            return not self._is_limit_active()

        if not self._is_limit_active():
            return True

        if approach_clockwise is not None:
            away = not approach_clockwise
            while self._is_limit_active():
                if time.monotonic() > release_deadline:
                    self._set_limit_fault("Limit switch stuck: timeout while backing off switch.")
                    return False
                self._single_step(away, half_delay)
            return True

        while self._is_limit_active():
            if time.monotonic() > release_deadline:
                self._set_limit_fault("Limit switch stuck: timeout while clearing switch.")
                return False
            if burst_clear(False, max_burst, release_deadline):
                return True
            if burst_clear(True, max_burst, release_deadline):
                return True
            self._set_limit_fault("Limit switch stuck: failed to clear after bidirectional backoff.")
            return False

    def _search_until_limit(self, clockwise: bool, half_delay: float, max_steps: int, deadline: float) -> bool:
        """Move in one direction until limit activates or step/timeout cap. Returns True if limit hit."""
        if self._is_limit_active():
            return False
        n = 0
        while True:
            if time.monotonic() > deadline:
                self._set_limit_fault("Timed out searching for limit switch edge.")
                return False
            if n >= max_steps:
                self._set_limit_fault("Max steps reached while searching for limit switch edge.")
                return False
            self._single_step(clockwise, half_delay)
            n += 1
            if self._is_limit_active():
                self._clear_limit_fault()
                return True

    def zero(self) -> bool:
        """Two-sweep limit homing: find both edges, move to midpoint, zero reference.

        Returns True on success. Uses ``homing`` config for timeouts and sweep direction.
        """
        if not self.connected or not self.h:
            return False
        if self._limit_switch_pin is None:
            self.setCurrentPositionZero()
            return True

        hc = self._homing_cfg
        half_delay = float(hc.get("homing_search_half_delay_s", 0.001))
        max_search = int(hc.get("max_search_steps", STEPS_PER_REV * 5))
        phase_timeout = float(hc.get("phase_timeout_s", 120.0))
        backoff_clear = int(hc.get("backoff_clear_steps", 80))
        first_cw = bool(hc.get("first_sweep_clockwise", False))

        with self.movement_lock:
            self.setCurrentPositionZero()

            deadline = time.monotonic() + phase_timeout
            if self._is_limit_active():
                if not self._release_limit_switch(half_delay, backoff_clear, deadline):
                    if self._last_limit_fault is None:
                        self._set_limit_fault("Limit switch stuck active at homing start.")
                    return False

            deadline = time.monotonic() + phase_timeout
            if not self._search_until_limit(first_cw, half_delay, max_search, deadline):
                return False
            edge1 = self.current_step_position

            # Back off opposite to sweep 1 approach direction (same axis as ``first_cw`` search).
            deadline = time.monotonic() + phase_timeout
            if not self._release_limit_switch(
                half_delay, backoff_clear, deadline, approach_clockwise=first_cw
            ):
                return False

            deadline = time.monotonic() + phase_timeout
            if not self._search_until_limit(not first_cw, half_delay, max_search, deadline):
                return False
            edge2 = self.current_step_position

            mid = (edge1 + edge2) // 2

            deadline = time.monotonic() + phase_timeout
            if not self._release_limit_switch(
                half_delay, backoff_clear, deadline, approach_clockwise=(not first_cw)
            ):
                return False

            delta = mid - self.current_step_position
            if delta != 0:
                cw_to_center = delta > 0
                steps = abs(int(delta))
                total_time = max(0.05, (half_delay * 2.0) * steps)
                _, _ = self._move_steps_timed(steps, total_time, cw_to_center)

            self.setCurrentPositionZero()
            self._clear_limit_fault()
            return True

    def home(self):
        self.zero()

    
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
                            _, hit = self._move_angle_timed(
                                angle_deg=abs(target_angle),
                                total_time_s=time_to_use,
                                clockwise=(target_angle > 0),
                            )
                            if hit:
                                break
                        self.count += 1
                    else:
                        # Subsequent movements: from previous waypoint to current waypoint
                        if self.count >= len(self.motor_degrees):
                            break
                        
                        angle_diff = self.motor_degrees[self.count] - self.motor_degrees[self.count-1]
                        time_to_use = self.motor_times[self.count] if self.count < len(self.motor_times) else 1.0
                        
                        if abs(angle_diff) > 0.01:  # Only move if significant difference
                            print(f"Moving to waypoint {self.count}: {self.motor_degrees[self.count]}° (Δ{angle_diff}°) in {time_to_use}s")
                            _, hit = self._move_angle_timed(
                                angle_deg=abs(angle_diff),
                                total_time_s=time_to_use,
                                clockwise=(angle_diff > 0),
                            )
                            if hit:
                                break
                        self.count += 1
                
                # After completing all waypoints, move back to 0
                if len(self.motor_degrees) > 0:
                    final_angle = self.motor_degrees[-1]
                    if abs(final_angle) > 0.01:  # Only move if not already at 0
                        # Use the last time interval, or default to 1 second
                        time_to_zero = self.motor_times[-1] if len(self.motor_times) > 0 else 1.0
                        print(f"Returning to 0° from {final_angle}° in {time_to_zero}s")
                        _, hit = self._move_angle_timed(
                            angle_deg=abs(final_angle),
                            total_time_s=time_to_zero,
                            clockwise=(final_angle < 0),  # Opposite direction to return to 0
                        )
                        if hit:
                            pass  # stopped on limit; skip complete message semantics
                
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
