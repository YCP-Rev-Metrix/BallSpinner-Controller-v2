# Requires: sudo pip3 install metawear
# usage: sudo python3 scan_connect.py
# from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from mbientlab.warble import * 
from time import sleep
print("libwarble", libwarble);
import platform
import six

import ctypes
import struct
import time

def warble_log(level, message):
    print(f"[WARBLE] {message.decode('utf-8')}", flush=True)

# Set log callback
#libwarble.warble_set_logger(ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)(warble_log))

# Set max verbosity (0 = none, 4 = debug)
#libwarble.warble_set_log_level(4)


selection = -1
devices = None

while selection == -1:
    print("scanning for devices...")
    devices = {}
    def handler(result):
        devices[result.mac] = result.name

    BleScanner.set_handler(handler)
    BleScanner.start()

    sleep(10.0)
    BleScanner.stop()

    i = 0
    for address, name in six.iteritems(devices):
        print("[%d] %s (%s)" % (i, address, name))
        i+= 1

    msg = "Select your device (-1 to rescan): "
    selection = int(raw_input(msg) if platform.python_version_tuple()[0] == '2' else input(msg))

address = list(devices)[selection]
print("Connecting to %s..." % (address))
device = MetaWear(address)
device.connect()

def turnOnBlueLED():
    pattern = LedPattern(delay_time_ms= 5000, repeat_count= Const.LED_REPEAT_INDEFINITELY)
    libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.SOLID)
    libmetawear.mbl_mw_led_write_pattern(device.board, byref(pattern), LedColor.BLUE)
    libmetawear.mbl_mw_led_play(device.board)


def turnOffLED():
    libmetawear.mbl_mw_led_stop_and_clear(device.board)

#Lets port the functionality to collect accelerometer data and see if we can output it to the terminal.
XL_samplerate = 25
XL_range = 2
def setupCollection():
    #set connection parameters 7.5ms connection interval, 0 Slave interval, 6s timeout
    libmetawear.mbl_mw_settings_set_connection_parameters(device.board, 7.5, 7.5, 0, 6000)
     #setup event loops
    accelCallback = FnVoid_VoidP_DataP(accelDataHandler)


def accelDataHandler(ctx, data, state=None):
    """Standalone accelerometer data handler (no self).

    Args:
        ctx: callback context (passed from C callback, unused here).
        data: pointer to data (as provided by metawear callbacks).
        state: optional dict-like object to store persistent fields used by the
            handler. If omitted, a minimal ephemeral state is created. Expected
            keys (if provided): 'AccelSampleCount', 'prevAccelEpoch',
            'is_local_mode', 'accelDataSig' (callable), 'xl_start_time', 'data_arr'.

    Returns:
        The state dict (useful if caller passed None and wants to keep it).
    """
    parsedData = parse_value(data)

    if state is None:
        state = {}

    # initialize persistent fields if missing
    if 'AccelSampleCount' not in state:
        state['AccelSampleCount'] = 0
    if 'prevAccelEpoch' not in state:
        # set using first received sample's epoch
        try:
            state['prevAccelEpoch'] = data.contents.epoch
        except Exception:
            state['prevAccelEpoch'] = 0

    prev_epoch = state.get('prevAccelEpoch', 0)
    try:
        timeStamp = (data.contents.epoch - prev_epoch) / 1000.0
    except Exception:
        # fallback if epoch not available
        timeStamp = 0.0

    if not state.get('is_local_mode', False):
        # Pack Sample Count into 3 Byte Big Endian Int
        state['AccelSampleCount'] += 1
        sampleCountInBytes = struct.pack('>I', state['AccelSampleCount'])[1:4]
        print(f"x:  {parsedData.x}  y:  {parsedData.y}  z:  {parsedData.z}")
        # Pack Timestamp, and x,y,z into 4 Byte Little Endian Floats
        # timeStampInBytes = struct.pack("<f", timeStamp)
        # xValInBytes = struct.pack('<f', parsedData.x)
        # yValInBytes = struct.pack('<f', parsedData.y)
        # zValInBytes = struct.pack('<f', parsedData.z)

        # mess = sampleCountInBytes + timeStampInBytes + xValInBytes + yValInBytes + zValInBytes

        # try:
        #     sig = state.get('accelDataSig')
        #     if callable(sig):
        #         sig(mess)
        #     else:
        #         # no TCP / signal provided — print a human-friendly fallback
        #         print("Encoded message (hex):", mess.hex())
        # except Exception as e:
        #     print(parsedData)
        #     print(e)
    # else:
    #     xl_start = state.get('xl_start_time', time.time())
    #     # persist start time if not present
    #     if 'xl_start_time' not in state:
    #         state['xl_start_time'] = xl_start
    #     time_val = time.time() - state['xl_start_time']
    #     arr = state.setdefault('data_arr', [None])
    #     arr[0] = {
    #         'timestamp': time_val,
    #         'x': parsedData.x,
    #         'y': parsedData.y,
    #         'z': parsedData.z
    #     }
    #     print(arr[0])

    return state


def startAccel(device, state=None):
    """Start accelerometer sampling using a state dict instead of self.

    Args:
        device: MetaWear device instance (required).
        state: optional dict to persist handler state across calls.

    Returns:
        The state dict (populated/updated).
    """
    if state is None:
        state = {}

    XL_rate = state.get('XL_SampleRate', globals().get('XL_samplerate', 25))
    XL_range_val = state.get('XL_Range', globals().get('XL_range', 2))

    print("Configuring Accelerometer")
    libmetawear.mbl_mw_acc_set_odr(device.board, XL_rate)
    print("ODR SET")
    libmetawear.mbl_mw_acc_set_range(device.board, XL_range_val)
    print("RANGE SET")
    libmetawear.mbl_mw_acc_write_acceleration_config(device.board)

    print("Subscribing to acceleration data")
    accelSignal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(device.board)
    state['xl_start_time'] = time.time()

    # create a C-callable callback that closes over the state dict
    def _cb(ctx, data):
        accelDataHandler(ctx, data, state)

    state['accelCallback'] = FnVoid_VoidP_DataP(_cb)
    libmetawear.mbl_mw_datasignal_subscribe(accelSignal, None, state['accelCallback'])

    print("Enabling acceleration sampling")
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(device.board)

    if accelSignal is not None:
        libmetawear.mbl_mw_acc_start(device.board)
    else:
        print("Unable to Start Polling Data: Acceleration Not Enabled")

    state['AccelSampleCount'] = 0
    state['accelSignal'] = accelSignal
    return state


def stopAccel(device, state=None):
    """Stop accelerometer sampling using a state dict instead of self.

    Args:
        device: MetaWear device instance (required).
        state: optional dict previously returned by startAccel.

    Returns:
        The state dict (may be modified).
    """
    if state is None:
        state = {}

    accelSignal = state.get('accelSignal')
    print("Stopping acceleration sampling")
    try:
        libmetawear.mbl_mw_acc_stop(device.board)
    except Exception:
        pass
    try:
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(device.board)
    except Exception:
        pass

    try:
        if accelSignal is not None:
            libmetawear.mbl_mw_datasignal_unsubscribe(accelSignal)
        else:
            # try to unsubscribe directly if accelSignal missing from state
            tmp = libmetawear.mbl_mw_acc_get_acceleration_data_signal(device.board)
            libmetawear.mbl_mw_datasignal_unsubscribe(tmp)
    except Exception:
        pass

    return state

turnOffLED()

print("ENABLING LED")
turnOnBlueLED()
print("Connected to " + device.address + " over " + ("USB" if device.usb.is_connected else "BLE"))
# print("Device information: " + str(device.info))
print("setting up XL collection")
setupCollection()
print("Starting XL collection")
startAccel(device)

sleep(5.0)


print("DISABLING LED")
turnOffLED()
device.disconnect()
sleep(1.0)
print("Disconnected") 


