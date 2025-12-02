'''import time #THIS PORTION IS NOT WORKING
import serial
import pyvesc
from pyvesc import VESCMessage, encode, decode
from pyvesc.VESC.messages import SetDutyCycle 

PORT = "/dev/ttyACM0"
BAUD = 115200

def send_duty(frac, seconds):
    frac = max(-1.0, min(1.0, frac))
    duty_int = int(frac * 1e5)
    msg = SetDutyCycle(duty_int)
    pkt = pyvesc.encode(msg)
    t_end = time.time() + seconds
    while time.time() < t_end:
        ser.write(pkt)
        time.sleep(0.02)  # 50 Hz

with serial.Serial(PORT, BAUD, timeout=0.05) as ser:
    time.sleep(1.0)

    #print("5% duty...")
    send_duty(0.05, 2.0)

    #print("20% duty...")
    send_duty(0.20, 2.0)

    #print("Stop...")
    send_duty(0.0, 1.0)

#print("Done.")
'''




#THE BELOW PORTION IS WORKING, COMMENTED OUT FOR FURTHER TESTING
'''
#!/usr/bin/env python3
import time
import serial
from pyvesc import encode
from pyvesc.VESC.messages import SetDutyCycle

PORT = "/dev/ttyACM0"   # or /dev/ttyUSB0
BAUD = 115200

DUTY_RAW = 5000     # 5% duty = 0.05 * 100000
DUTY_SMALL = 0.05
RUN_TIME = 4      # seconds


#print(f"Opening {PORT}...")
with serial.Serial(PORT, BAUD, timeout=0.05) as ser:
    #print("Connected.")

    # Stop motor first
    ser.write(encode(SetDutyCycle(0)))
    time.sleep(0.2)

    #print("Running at 5% duty for 4 seconds...")

    ser.write(encode(SetDutyCycle(0.01)))
    time.sleep(4)
    ser.write(encode(SetDutyCycle(0.02)))
    time.sleep(0.25)
    ser.write(encode(SetDutyCycle(0.03)))
    time.sleep(0.25)
    ser.write(encode(SetDutyCycle(0.04)))
    time.sleep(0.25)
    ser.write(encode(SetDutyCycle(0.05)))
    time.sleep(0.25)


    start = time.time()
    while time.time() - start < RUN_TIME:
        ser.write(encode(SetDutyCycle(DUTY_SMALL)))
        time.sleep(0.05)  # keep alive

    #print("Moving to 10% duty for 4 seconds...")

    start = time.time()
    while time.time() - start < RUN_TIME:
        ser.write(encode(SetDutyCycle(DUTY_SMALL*2)))
        time.sleep(0.05)  # keep alive


    #print("Moving to 30% duty for 4 seconds...")

    
    start = time.time()
    while time.time() - start < 4:
        ser.write(encode(SetDutyCycle(DUTY_SMALL*6)))
        time.sleep(0.05)  # keep alive

    #print("Stopping motor...")
    for i in range(10):
        ser.write(encode(SetDutyCycle(0)))
        time.sleep(0.05)

#print("Done.")
'''
import time
import serial
import struct

from pyvesc import encode
from pyvesc.VESC.messages import SetDutyCycle

PORT = "/dev/ttyACM0"   # or "/dev/ttyUSB0"
BAUD = 115200

DUTY = 0.05        # 5% duty
RUN_TIME = 10      # seconds

COMM_GET_VALUES = 4  # VESC command id for "get values"


# ---------- VESC packet helpers (no pyvesc for GetValues) ----------

def crc16(data: bytes) -> int:
    """
    CRC16-CCITT (polynomial 0x1021, init 0) used by VESC.
    """
    crc = 0
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def make_packet(payload: bytes) -> bytes:
    """
    Build a full VESC UART packet from a payload.
    We only handle "short" packets (len <= 255) which is fine here.
    """
    length = len(payload)
    assert length <= 255
    packet = bytearray()
    packet.append(2)        # start byte for short packet
    packet.append(length)   # length
    packet.extend(payload)  # payload
    c = crc16(payload)
    packet.append((c >> 8) & 0xFF)  # CRC high
    packet.append(c & 0xFF)        # CRC low
    packet.append(3)        # stop byte
    return bytes(packet)


def send_get_values(ser: serial.Serial):
    """
    Send a COMM_GET_VALUES request to the VESC.
    """
    payload = bytes([COMM_GET_VALUES])
    pkt = make_packet(payload)
    ser.write(pkt)


def read_mc_values(ser: serial.Serial, timeout: float = 0.2):
    """
    Read one VESC packet and, if it's a COMM_GET_VALUES reply,
    decode key fields and return them as a dict.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        head = ser.read(1)
        if not head:
            continue

        h = head[0]
        if h not in (2, 3):
            continue

        # length
        if h == 2:
            lb = ser.read(1)
            if len(lb) != 1:
                continue
            length = lb[0]
        else:  # long packet (not expected for GetValues, but handle anyway)
            lb = ser.read(2)
            if len(lb) != 2:
                continue
            length = (lb[0] << 8) | lb[1]

        payload = ser.read(length)
        if len(payload) != length:
            continue

        # crc + end
        crc_bytes = ser.read(2)
        end = ser.read(1)
        if len(crc_bytes) != 2 or end != b'\x03':
            continue

        # (optional) check CRC
        # if crc16(payload) != ((crc_bytes[0] << 8) | crc_bytes[1]):
        #     continue

        # First byte of payload is command
        if not payload or payload[0] != COMM_GET_VALUES:
            continue

        # ----- Decode fields according to COMM_GET_VALUES layout -----
        ind = 1  # skip command byte

        def read_f16(scale):
            nonlocal ind
            raw = struct.unpack(">h", payload[ind:ind+2])[0]
            ind += 2
            return raw / scale

        def read_f32(scale):
            nonlocal ind
            raw = struct.unpack(">i", payload[ind:ind+4])[0]
            ind += 4
            return raw / scale

        def read_i32():
            nonlocal ind
            raw = struct.unpack(">i", payload[ind:ind+4])[0]
            ind += 4
            return raw

        temp_fet      = read_f16(10.0)
        temp_motor    = read_f16(10.0)
        motor_current = read_f32(100.0)
        input_current = read_f32(100.0)
        _id           = read_f32(100.0)
        _iq           = read_f32(100.0)
        duty_now      = read_f16(1000.0)
        rpm           = read_f32(1.0)
        v_in          = read_f16(10.0)
        amp_hours     = read_f32(10000.0)
        amp_hours_ch  = read_f32(10000.0)
        wh            = read_f32(10000.0)
        wh_ch         = read_f32(10000.0)
        tachometer    = read_i32()
        tach_abs      = read_i32()
        fault         = payload[ind]

        return {
            "temp_fet": temp_fet,
            "temp_motor": temp_motor,
            "motor_current": motor_current,
            "input_current": input_current,
            "duty_now": duty_now,
            "rpm": rpm,
            "v_in": v_in,
            "tachometer": tachometer,
            "tachometer_abs": tach_abs,
            "fault": fault,
        }

    return None


# ---------- Main program ----------

#print(f"Opening {PORT}...")
with serial.Serial(PORT, BAUD, timeout=0.05) as ser:
    #print("Connected.")

    # Stop motor initially
    ser.write(encode(SetDutyCycle(0.0)))
    time.sleep(0.2)

    #print("Running at 5% duty and #printing encoder/RPM data...")

    start = time.time()
    while time.time() - start < RUN_TIME:
        # 1) keep motor commanded
        ser.write(encode(SetDutyCycle(0.026)))#(time.time()-start)*DUTY*0.1)))

        # 2) ask for values
        send_get_values(ser)

        # 3) read and decode reply
        vals = read_mc_values(ser)
        if vals is not None:
            erpm = vals["rpm"]

            # Your 4-pole RC motor = 2 pole pairs → mech RPM = ERPM / 2
            mech_rpm = erpm / 2.0

            #print(
                f"ERPM: {erpm:9.1f} | "
                f"RPM: {mech_rpm:9.1f} | "
                f"I_motor: {vals['motor_current']:6.2f} A | "
                f"V_in: {vals['v_in']:5.2f} V | "
                f"Duty: {vals['duty_now']*100:5.1f}% | "
                f"Fault: {vals['fault']}"
            )

        time.sleep(0.05)

    #print("Stopping motor...")
    for _ in range(10):
        ser.write(encode(SetDutyCycle(0.0)))
        time.sleep(0.05)

#print("Done.")
