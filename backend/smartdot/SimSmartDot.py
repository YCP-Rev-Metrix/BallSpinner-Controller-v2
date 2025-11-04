from .iSmartDot import iSmartDot
from PyQt6.QtCore import QThread
import time
import math
import logging
import random

logger = logging.getLogger(__name__)

class TimerThread(QThread):
    #Goal is to create a thread that will call the accelDataHandler, gyroDataHandler, magDataHandler, and lightDataHandler functions at the specified sample rates
    def __init__(self, sample_rate, callback, parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate
        self.callback = callback
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if self.callback:
                self.callback(None, None)  # Call with None for ctx and data as requested
            time.sleep(1.0 / self.sample_rate)
    
    def stop(self):
        self.running = False
        self.wait()  # Wait for thread to finish
class SimSmartDot(iSmartDot):
    # Sample frequency constants (Hz)
    XL_SAMPLE_FREQUENCY = 25.0  # Accelerometer
    GY_SAMPLE_FREQUENCY = 25.0  # Gyroscope
    MG_SAMPLE_FREQUENCY = 10.0  # Magnetometer
    LT_SAMPLE_FREQUENCY = 2.0   # Light sensor
    
    def __init__(self, MAC_Address=""):
        super().__init__()
        self.connected = False
        # Track start times for each sensor
        self.xl_start_time = None
        self.gy_start_time = None
        self.mg_start_time = None
        self.lt_start_time = None
        
        # Timer threads for data collection
        self.xl_timer_thread = None
        self.gy_timer_thread = None
        self.mg_timer_thread = None
        self.lt_timer_thread = None

        self.connect(MAC_Address)

    def connect(self, MAC_Address):
        self.connected = True
        logger.info(f"Connected to SIMULATED SMART DOT {MAC_Address}")
        return True

    def disconnect(self):
        # Stop collecting if still running
        if (self.xl_timer_thread or self.gy_timer_thread or 
            self.mg_timer_thread or self.lt_timer_thread):
            self.stopCollecting()
        self.connected = False
        return True

    def startAccel(self):
        self.xl_start_time = time.time()

    def stopAccel(self):
        self.xl_start_time = None

    def startGyro(self):
        self.gy_start_time = time.time()

    def stopGyro(self):
        self.gy_start_time = None

    def startMag(self):
        self.mg_start_time = time.time()

    def stopMag(self):
        self.mg_start_time = None

    def startLight(self):
        self.lt_start_time = time.time()

    def stopLight(self):
        self.lt_start_time = None

    def accelDataHandler(self, ctx, data):
        if self.xl_start_time is None:
            self.xl_start_time = time.time()
        
        time_val = time.time() - self.xl_start_time
        
        # Generate simulated accelerometer data (sinusoidal patterns)
        # Using different frequencies for x, y, z to create realistic variation
        self.xl_time.append(time_val)
        self.xl_x.append(9.81 * math.sin(2 * math.pi * 0.5 * time_val) + 0.1 * math.sin(2 * math.pi * 5 * time_val))
        self.xl_y.append(9.81 * math.cos(2 * math.pi * 0.3 * time_val) + 0.1 * math.cos(2 * math.pi * 4 * time_val))
        self.xl_z.append(9.81 + 0.5 * math.sin(2 * math.pi * 0.2 * time_val))

        # print(f"XL: {self.xl_time}, {self.xl_x}, {self.xl_y}, {self.xl_z}")

    def gyroDataHandler(self, ctx, data):
        if self.gy_start_time is None:
            self.gy_start_time = time.time()
        
        time_val = time.time() - self.gy_start_time
        
        # Generate simulated gyroscope data (degrees per second)
        self.gy_time.append(time_val)
        self.gy_x.append(10.0 * math.sin(2 * math.pi * 0.4 * time_val))
        self.gy_y.append(15.0 * math.cos(2 * math.pi * 0.35 * time_val))
        self.gy_z.append(5.0 * math.sin(2 * math.pi * 0.6 * time_val))

    def magDataHandler(self, ctx, data):
        if self.mg_start_time is None:
            self.mg_start_time = time.time()
        
        time_val = time.time() - self.mg_start_time
        
        # Generate simulated magnetometer data (microteslas)
        # Earth's magnetic field is typically around 50-60 microteslas
        self.mg_time.append(time_val)
        self.mg_x.append(0.0 + 5.0 * math.sin(2 * math.pi * 0.1 * time_val))
        self.mg_y.append(5.0 + 5.0 * math.cos(2 * math.pi * 0.12 * time_val))
        self.mg_z.append(5.0 + 3.0 * math.sin(2 * math.pi * 0.15 * time_val))

    def lightDataHandler(self, ctx, data):
        if self.lt_start_time is None:
            self.lt_start_time = time.time()
        
        time_val = time.time() - self.lt_start_time
        
        # Generate simulated light sensor data (lux)
        # Varies between day and night levels
        self.lt_time.append(time_val)
        self.lt_value.append(random.uniform(0, 10))

    def startCollecting(self):
        # Start the sensors
        self.startAccel()
        self.startMag()
        self.startGyro()
        self.startLight()
        
        # Create and start timer threads for each data handler
        self.xl_timer_thread = TimerThread(
            self.XL_SAMPLE_FREQUENCY, 
            self.accelDataHandler
        )
        self.gy_timer_thread = TimerThread(
            self.GY_SAMPLE_FREQUENCY, 
            self.gyroDataHandler
        )
        self.mg_timer_thread = TimerThread(
            self.MG_SAMPLE_FREQUENCY, 
            self.magDataHandler
        )
        self.lt_timer_thread = TimerThread(
            self.LT_SAMPLE_FREQUENCY, 
            self.lightDataHandler
        )
        
        # Start all threads
        self.xl_timer_thread.start()
        self.gy_timer_thread.start()
        self.mg_timer_thread.start()
        self.lt_timer_thread.start()
        
        logger.info("Started collecting data with timer threads")
        print("Started collecting data")

    def stopCollecting(self):
        # Stop and kill timer threads
        if self.xl_timer_thread:
            self.xl_timer_thread.stop()
            self.xl_timer_thread = None
        if self.gy_timer_thread:
            self.gy_timer_thread.stop()
            self.gy_timer_thread = None
        if self.mg_timer_thread:
            self.mg_timer_thread.stop()
            self.mg_timer_thread = None
        if self.lt_timer_thread:
            self.lt_timer_thread.stop()
            self.lt_timer_thread = None
        
        # Stop the sensors
        self.stopAccel()
        self.stopMag()
        self.stopGyro()
        self.stopLight()
        
        logger.info("Stopped collecting data and killed timer threads")
        
    def UUID(self):
        return "SimSmartDot"