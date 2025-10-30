from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from mbientlab.warble import * 
import platform
import six
import time

class ScanSmartDot():
    # self.devices = None
    def __init__(self):
        self.devices = None
        
    def scan10Seconds(self):
        devices = {}
        def handler(result):
            devices[result.mac] = result.name

        BleScanner.set_handler(handler)
        BleScanner.start()

        time.sleep(10.0)
        BleScanner.stop()

        #Parse the dictionary by values == Metawear then build an array that results in. 
        metawear_devices = [key for key, value in devices.items() if value == 'MetaWear']

        self.devices = metawear_devices
    
if __name__ == "__main__":
    scan = ScanSmartDot()
    scan.scan10Seconds()
    print(scan.devices)

