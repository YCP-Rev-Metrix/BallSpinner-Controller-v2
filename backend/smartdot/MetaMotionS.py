from .iSmartDot import iSmartDot
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
class MetaMotion(iSmartDot):

    XL_availSampleRate = [12.5, 25, 50, 100, 200, 400, 800]
    XL_availRange = [2,4,8,16]

    GY_availSampleRate = [25, 50, 100, 200, 400, 800, 1600]
    GY_availRange = [125,250,500,1000,2000]

    
    MG_availSampleRate = [2, 4, 6, 8, 10, 15, 20, 25, 30]
    MG_availRange      = [2500]

    LT_availSampleRate = [.5, 1, 2, 5, 10, 20]
    LT_availRange = [600, 1300, 8000, 16000, 32000, 64000]
    
    def __init__(self, MAC_Address="", autoConnect=False, is_local=False):
        self._MAC_ADDRESS = MAC_Address
        if autoConnect:
            self.connect(MAC_Address)

        #temp rig to create a different data capture method for local mode HMI
        self.data_arr= [None,None,None,None]

        def connect(self, MAC_Address) -> bool:
        #print("Attempting to connect to device")
        #print(MAC_Address)
        #try:
            self.device = MetaWear(MAC_Address)
            self.device.connect()
            #set connection parameters 7.5ms connection interval, 0 Slave interval, 6s timeout
            libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
            
            #setup event loops
            self.accelCallback = FnVoid_VoidP_DataP(self.accelDataHandler)
            self.magCallback = FnVoid_VoidP_DataP(self.magDataHandler)
            self.gyroCallback = FnVoid_VoidP_DataP(self.gyroDataHandler)
            self.lightCallback = FnVoid_VoidP_DataP(self.lightDataHandler)

            #I2C Reading setup
            self.XL_ODR_Callback = FnVoid_VoidP_DataP(self.i2c_data_handler)
            #0x68 is bmi270 i2c addr. 0x40 is odr register addr.
            self.XL_ODR_parameters= I2cReadParameters(device_addr= 0x68, register_addr= 0x40)


            #set configurabe settings for each sensor's Rate and Range
            self.XL_availSampleRate = MetaMotion.XL_availSampleRate
            self.XL_availRange = MetaMotion.XL_availRange
            self.GY_availSampleRate = MetaMotion.GY_availSampleRate
            self.GY_availRange = MetaMotion.GY_availRange
            self.MG_availSampleRate = MetaMotion.MG_availSampleRate
            self.MG_availRange = MetaMotion.MG_availRange
            self.LT_availRange = MetaMotion.LT_availRange
            self.LT_availSampleRate = MetaMotion.LT_availSampleRate

           
            #self.setSampleRanges(XL=100, GY=100, MG=10)

            self.XL_Range = 2
            self.GY_Range = 2
            
            self.MG_SampleRate = 10

            self.turnOnBlueLED()
            print("Connected to device")
            return True