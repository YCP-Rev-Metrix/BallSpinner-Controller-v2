#!/usr/bin/env python3
"""
Debug test to see raw ERPM commands being sent to VESC.
Instruments changeSpeed() to print what's happening internally.
"""
import sys
sys.path.insert(0, ".")

import time
import serial
from pyvesc import encode
from pyvesc.VESC.messages import SetRPM

# Import motor with patched logging
from backend.motors.USBBDCMotor import USBBDCMotor

# Monkey-patch to capture and print ERPM commands
original_write = serial.Serial.write
commands_sent = []

def logged_write(self, data):
    global commands_sent
    # Detect SetRPM packets (contains "SetRPM" in pyvesc encoding)
    if len(data) >= 7:
        # VESC packet: [0x02, len, payload..., crc_hi, crc_lo, 0x03]
        # SetRPM payload: [0x08, val1, val2, val3, val4]
        if data[2] == 0x08 and len(data) >= 7:  # SetRPM command ID = 8
            erpm = (data[3] << 24) | (data[4] << 16) | (data[5] << 8) | data[6]
            # VESC uses signed int32
            if erpm > 0x7FFFFFFF:
                erpm -= 0x100000000
            commands_sent.append(erpm)
    return original_write(self, data)

serial.Serial.write = logged_write

print("================================================================================")
print("ERPM Debug Test (printing raw SetRPM ERPM values)")
print("================================================================================\n")

motor = USBBDCMotor(rpm_scale=2.0)
motor.connect()
time.sleep(0.5)

print("✓ Motor initialized\n")

print("Test: Ramp 0 → 600 in steps (Ki=0.6, boost=800)")
print("Cmd    Target_RPM     Actual_RPM     Error      ERPM_Cmd   Mech_Expected")
print("-" * 80)

for cmd in range(0, 601, 50):
    motor.changeSpeed(cmd, False)
    time.sleep(0.3)  # Settle PID loop
    
    actual = motor.currSpeed
    target = cmd * motor.rpm_scale
    error = target - actual if actual is not None else target
    
    # Last ERPM sent
    last_erpm = commands_sent[-1] if commands_sent else 0
    expected_mech = last_erpm / 2  # POLE_PAIRS = 2
    
    status = "OK" if abs(error) < 50 else ("OVERSHOOT" if error < 0 else "UNDERSHOOT")
    
    print(f"{cmd:3.0f}    {target:6.0f}          {actual:6.1f}        {error:7.1f}     {last_erpm:7.0f}     {expected_mech:6.0f}")

motor.stop()
time.sleep(0.2)

print("\n✓ Test complete")
print("\nNote: ERPM_Cmd ÷ 2 = mechanical RPM that VESC *should* actually be running")
print("      If actual < mechanical RPM expected, then VESC is undershooting on its own")
