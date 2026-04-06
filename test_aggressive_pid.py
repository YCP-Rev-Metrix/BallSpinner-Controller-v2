#!/usr/bin/env python3
import sys
import time
sys.path.insert(0, '/home/ballz/BallSpinner-Controller-v2')

from backend.motors.USBBDCMotor import USBBDCMotor

print("=" * 80)
print("Testing Aggressive PID + Feedforward Boost")
print("=" * 80)

try:
    motor = USBBDCMotor()
    print("\n✓ Motor initialized")
    
    print("\nTest: Ramp 0 → 600 in steps (aggressive dead zone compensation)")
    print(f"{'Cmd':<6} {'Target_RPM':<14} {'Actual_RPM':<14} {'Error':<10} {'Status':<20}")
    print("-" * 80)
    
    for cmd in range(0, 605, 50):
        motor.changeSpeed(cmd, False)
        time.sleep(0.3)
        
        target_rpm = cmd * 2
        actual_rpm = motor.currSpeed if motor.currSpeed else 0
        error = actual_rpm - target_rpm
        
        status = "OK" if abs(error) < 100 else ("UNDERSHOOT" if error < -100 else "OVERSHOOT")
        print(f"{cmd:<6} {target_rpm:<14.0f} {actual_rpm:<14.1f} {error:+9.1f} {status:<20}")
    
    print("\nStopping motor...")
    motor.stop()
    time.sleep(0.2)
    
    print("\n✓ Test complete")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
