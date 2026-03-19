#!/usr/bin/env python3
"""
Deep dive: Print every PID calculation step.
"""
import sys
sys.path.insert(0, ".")

import time
import serial
from pyvesc import encode
from pyvesc.VESC.messages import SetRPM
from backend.motors.USBBDCMotor import (
    USBBDCMotor, PID_KP, PID_KI, PID_KD, PID_MAX_INTEGRAL, 
    LOW_SPEED_BOOST_MAGNITUDE, LOW_SPEED_BOOST_THRESHOLD, ERPM_SCALE, SPEED_LOOP_RATE
)

# Monkey-patch changeSpeed to print internals
original_changeSpeed = USBBDCMotor.changeSpeed

def logged_changeSpeed(self, dutyCycle, isShotMode):
    """Intercept and log PID calculations."""
    clamped_rpm = self.clamp(dutyCycle, 0, 600)
    target_mech_rpm = clamped_rpm * self._rpm_scale
    actual_mech_rpm = self.getCurrentSpeed()
    
    if actual_mech_rpm is None:
        actual_mech_rpm = 0.0
    
    speed_error = target_mech_rpm - actual_mech_rpm
    
    p_term = PID_KP * speed_error
    self._pid_integral += speed_error * SPEED_LOOP_RATE
    old_integral = self._pid_integral
    self._pid_integral = self.clamp(self._pid_integral, -PID_MAX_INTEGRAL, PID_MAX_INTEGRAL)
    i_term = PID_KI * self._pid_integral
    
    d_term = PID_KD * (speed_error - self._pid_prev_error) / SPEED_LOOP_RATE
    self._pid_prev_error = speed_error
    
    pid_correction = p_term + i_term + d_term
    
    # New smooth boost logic (matches USBBDCMotor.py)
    boost_strength = max(0.0, 1.0 - (target_mech_rpm / 500.0))
    feedforward_boost = LOW_SPEED_BOOST_MAGNITUDE * boost_strength
    
    adjusted_mech_rpm = target_mech_rpm + pid_correction + feedforward_boost / ERPM_SCALE
    adjusted_mech_rpm = self.clamp(adjusted_mech_rpm, 0, 2400)
    target_erpm = int(adjusted_mech_rpm * ERPM_SCALE)
    
    # PRINT INTERNALS
    if clamped_rpm > 0:  # Skip zero
        print(f"Cmd{clamped_rpm:3.0f}: target={target_mech_rpm:6.0f} actual={actual_mech_rpm:6.1f} error={speed_error:7.1f}")
        print(f"      P={p_term:7.2f} I_accum={old_integral:8.1f}→{self._pid_integral:8.1f} I_term={i_term:7.2f} D={d_term:7.2f}")
        print(f"      boost={feedforward_boost:6.0f} adjusted={adjusted_mech_rpm:6.1f} ERPM={target_erpm:6.0f}")
    
    # Send it
    self.ser.write(encode(SetRPM(target_erpm)))
    self.currSpeed = actual_mech_rpm

USBBDCMotor.changeSpeed = logged_changeSpeed

print("=" * 80)
print("Deep Dive: PID Internals")
print("=" * 80 + "\n")

motor = USBBDCMotor(rpm_scale=2.0)
motor.connect()
time.sleep(0.5)
print("✓ Motor initialized\n")

# Test just the low-speed range
print("Test: 50 → 600 in 150 unit steps\n")
for cmd in [0, 50, 100, 150, 200, 250, 300]:
    motor.changeSpeed(cmd, False)
    time.sleep(0.3)

motor.stop()
print("\n✓ Done")
