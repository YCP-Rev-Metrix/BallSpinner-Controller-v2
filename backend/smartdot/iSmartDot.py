 
from abc import ABCMeta, abstractmethod
from array import array
import threading


class iSmartDot(metaclass=ABCMeta):

    def __init__(self):
        # Required data storage fields for all sensor types
        # Use compact C-backed arrays for lower memory and faster appends
        # Accelerometer (XL) data
        self.xl_time = array('d')
        self.xl_x = array('f')
        self.xl_y = array('f')
        self.xl_z = array('f')

        # Gyroscope (GY) data
        self.gy_time = array('d')
        self.gy_x = array('f')
        self.gy_y = array('f')
        self.gy_z = array('f')

        # Magnetometer (MG) data
        self.mg_time = array('d')
        self.mg_x = array('f')
        self.mg_y = array('f')
        self.mg_z = array('f')

        # Light sensor (LT) data
        self.lt_time = array('d')
        self.lt_value = array('f')

        # Locks for thread-safe appends/reads
        self._xl_lock = threading.Lock()
        self._gy_lock = threading.Lock()
        self._mg_lock = threading.Lock()
        self._lt_lock = threading.Lock()
    
    #Confirm all class under this interface have called all functions
    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        return (hasattr(subclass, 'connect') and 
                hasattr(subclass, 'disconnect'))    

    def setSampleRates(self, XL=None, GY=None, MG=None, LT=None):
        #TOOD Move to SDE and make this abstract
        #Set any Sampling Rates that were passed in
        if XL != None: self.XL_SampleRate = XL
        if GY != None: self.GY_SampleRate = GY
        if MG != None: self.MG_SampleRate = MG
        if LT != None: self.LT_SampleRate = LT

    def setRanges(self, XL=None, GY=None, MG=None, LT=None):
        #TOOD Move to SDE and make this abstract

        #Set any Sampling Rates that were passed in
        if XL != None: self.XL_Range = XL
        if GY != None: self.GY_Range = GY
        if MG != None: self.MG_Range = MG
        if LT != None: self.LT_Range = LT
        
    @abstractmethod
    def connect(self, MAC_Address) -> bool:
        pass

    @abstractmethod
    def disconnect(MAC_Address):
        pass
    
    def setDataSignals(self, accelDataSig, gyroDataSig, magDataSig, lightDataSig):
        self.accelDataSig =  accelDataSig
        self.gyroDataSig = gyroDataSig
        self.magDataSig = magDataSig
        self.lightDataSig = lightDataSig

    @abstractmethod
    def startMag(self):   
        pass

    @abstractmethod
    def stopMag(self):
        pass

    @abstractmethod
    def startAccel(self):
        pass

    @abstractmethod
    def stopAccel(self):
        pass

    @abstractmethod
    def startGyro(self):
        pass

    @abstractmethod
    def stopGyro(self):
        pass
    
    @abstractmethod
    def startLight(self):
        pass

    @abstractmethod
    def stopLight(self):
        pass 
    @abstractmethod
    def accelDataHandler(self, ctx, data):
        pass

    @abstractmethod
    def gyroDataHandler(self, ctx, data):
        pass

    @abstractmethod
    def magDataHandler(self, ctx, data):
        pass

    @abstractmethod
    def lightDataHandler(self, ctx, data):
        pass

    # @abstractmethod
    # def UUID(self) -> str: 
    #     pass
        # Scan Bluetooth Devices and filters for specific devices

