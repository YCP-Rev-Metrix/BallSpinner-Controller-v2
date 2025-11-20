import lgpio
import time

# ================================
# GPIO PIN DEFINITIONS (BCM MODE)
# ================================
# STEP_PIN drives the PUL- input on the stepper driver (e.g. DM542).
# Each rising edge (or full high+low pulse, depending on driver) is one microstep.
STEP_PIN = 23  # BCM 23 -> PUL-

# DIR_PIN drives the DIR- input on the stepper driver.
# Changing this pin HIGH/LOW changes the motor rotation direction (CW/CCW),
# as long as the driver's DIR+ is tied to a stable logic voltage (e.g. 3.3 V or 5 V)
# and there is a common ground between the Pi and the driver.
DIR_PIN  = 24  # BCM 24 -> DIR-

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
STEPS_PER_REV = 1600  # adjust if you change microstepping on the driver


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
            angle_deg=90.0,
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


if __name__ == "__main__":
    main()
