import threading
import time
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from mbientlab.warble import * 
import platform
import six

class ScanSmartDot():
    def __init__(self):
        self.devices = None

    def scan10Seconds(self):
        devices = {}
        
        def handler(result):
            devices[result.mac] = result.name
        
        def stop_scan_after_delay():
            """Thread function that waits 10 seconds then stops scanning."""
            for i in range(10):
                time.sleep(1)
                #print(f"Scanning... {i+1}/10 seconds")
            BleScanner.stop()
            #print("Scan stopped after 10 seconds.")
        
        BleScanner.set_handler(handler)
        BleScanner.start()
        #print("Started scanning for MetaWear devices...")

        # Create and start the timer thread
        timer_thread = threading.Thread(target=stop_scan_after_delay)
        timer_thread.start()

        # Wait for the thread to complete before parsing results
        timer_thread.join()

        # Filter only MetaWear devices
        metawear_devices = [key for key, value in devices.items() if value == 'MetaWear']
        self.devices = metawear_devices

if __name__ == "__main__":
    scan = ScanSmartDot()
    scan.scan10Seconds()
    #print("Found devices:", scan.devices)

