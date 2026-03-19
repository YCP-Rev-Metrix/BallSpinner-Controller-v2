#!/usr/bin/env python3
"""
Simple test: Command a fixed ERPM and see what telemetry we get back.
Helps diagnose if VESC is actually responding or if telemetry is garbage.
"""
import sys
sys.path.insert(0, ".")

import time
import serial
from pyvesc import encode
from pyvesc.VESC.messages import SetRPM
from backend.motors.USBBDCMotor import send_get_values, read_mc_values

PORT = "/dev/ttyACM0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=0.5)
time.sleep(0.5)

print("=" * 70)
print("Fixed ERPM Test: Send static commands and read back actual")
print("=" * 70 + "\n")

erpm_tests = [
    (0, "Zero (motor off)"),
    (500, "500 ERPM → ~250 mech RPM"),
    (1000, "1000 ERPM → 500 mech RPM"),
    (2000, "2000 ERPM → 1000 mech RPM"),
    (3000, "3000 ERPM → 1500 mech RPM"),
    (4000, "4000 ERPM → 2000 mech RPM"),
    (2000, "Back to 2000 ERPM"),
    (0, "Stop"),
]

for target_erpm, desc in erpm_tests:
    # Send command
    ser.write(encode(SetRPM(target_erpm)))
    
    # Wait for motor to settle
    time.sleep(0.5)
    
    # Read telemetry 5 times to see consistency
    readings = []
    for _ in range(5):
        send_get_values(ser)
        vals = read_mc_values(ser, timeout=0.2)
        if vals:
            readings.append(vals["rpm"])
        time.sleep(0.1)
    
    if readings:
        avg_erpm = sum(readings) / len(readings)
        mech_rpm = avg_erpm / 2
        print(f"ERPM_Cmd: {target_erpm:5.0f}  |  Telemetry ERPM avg: {avg_erpm:7.0f}  |  Mech: {mech_rpm:6.0f}  |  {desc}")
    else:
        print(f"ERPM_Cmd: {target_erpm:5.0f}  |  NO RESPONSE")

# Cleanup
ser.write(encode(SetRPM(0)))
ser.close()

print("\n✓ Test complete")
print("\nInterpretation:")
print("  - If Telemetry ERPM ≈ ERPM_Cmd: VESC is working, we have an algorithm problem")
print("  - If Telemetry ERPM << ERPM_Cmd: VESC firmware/hardware not responding")
