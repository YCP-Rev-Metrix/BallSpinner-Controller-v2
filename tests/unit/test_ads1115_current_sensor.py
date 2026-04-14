import pytest

from backend.sensors.ADS1115CurrentSensor import ADS1115CurrentSensor


class DummyBus:
    def __init__(self, bus_id):
        self.bus_id = bus_id
        self.writes = []

    def write_i2c_block_data(self, addr, reg, data):
        self.writes.append((addr, reg, data))

    def read_i2c_block_data(self, addr, reg, length):
        assert addr == 0x48
        assert reg == ADS1115CurrentSensor.POINTER_CONVERSION
        assert length == 2
        # Return a raw ADC reading corresponding to 2.048V for a 4.096V range.
        return [0x40, 0x00]

    def close(self):
        pass


class DummySMBusModule:
    SMBus = DummyBus


def test_ads1115_current_sensor_conversion(monkeypatch):
    monkeypatch.setattr(
        'backend.sensors.ADS1115CurrentSensor.smbus2',
        DummySMBusModule,
    )
    sensor = ADS1115CurrentSensor(volts_per_amp=0.05, zero_voltage=2.048)
    current = sensor.read_current(0)
    assert current == pytest.approx(0.0, abs=1e-3)
    voltage = sensor.read_voltage(0)
    assert voltage == pytest.approx(2.048, abs=1e-3)
    sensor.close()


def test_ads1115_current_sensor_missing_smbus(monkeypatch):
    monkeypatch.setattr('backend.sensors.ADS1115CurrentSensor.smbus2', None)
    with pytest.raises(RuntimeError, match='smbus2 is required'):
        ADS1115CurrentSensor()


def test_stepmotor_getVals_with_current_sensor(monkeypatch):
    from backend.motors.StepMotor import StepMotor

    class DummySensor:
        def read_current(self, channel):
            return 1.23

    class DummyLGPIO:
        def gpio_claim_output(self, h, pin, level):
            pass
        def gpio_write(self, h, pin, value):
            pass
        def gpio_free(self, h, pin):
            pass
        def gpiochip_open(self, idx):
            return 0

    monkeypatch.setattr('backend.motors.StepMotor.lgpio', DummyLGPIO())
    motor = StepMotor(
        GPIO_Pin=27,
        DIR_Pin=17,
        h=0,
        enable_pin=None,
        enable_active_low=True,
        current_sensor=DummySensor(),
        current_sensor_channel=0,
    )
    vals = motor.getVals()
    assert vals['input_current'] == pytest.approx(1.23)
    assert vals['temp_motor'] is None
