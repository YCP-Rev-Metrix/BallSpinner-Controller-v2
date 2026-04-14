import time
import struct
from typing import Optional

try:
    import smbus2
except ImportError:
    smbus2 = None


class ADS1115CurrentSensor:
    """ADS1115-backed current sensor helper for INA240 analog outputs.

    This helper is intended for use with an INA240 current-sense amplifier whose
    analog output is connected to one of the ADS1115 channels. The ADS1115 is
    read in single-shot mode and the raw ADC count is converted into volts using
    the configured PGA range.

    The default constants assume:
      - ADS1115 address 0x48 on I2C bus 1
      - PGA range ±4.096V
      - INA240 0 A output centered at 2.048 V
      - INA240 scale of 0.05 V/A (20 A/V)

    Adjust `zero_voltage` and `volts_per_amp` to match your particular INA240
    gain and wiring.
    """

    POINTER_CONVERSION = 0x00
    POINTER_CONFIG = 0x01
    OS_SINGLE = 0x8000
    MODE_SINGLE_SHOT = 0x0100
    DR_128 = 0x0080
    COMP_QUE_DISABLE = 0x0003

    PGA_4_096 = 0x0200
    MUX_SINGLE_0 = 0x4000
    MUX_SINGLE_1 = 0x5000
    MUX_SINGLE_2 = 0x6000
    MUX_SINGLE_3 = 0x7000

    CHANNEL_CONFIGS = {
        0: MUX_SINGLE_0,
        1: MUX_SINGLE_1,
        2: MUX_SINGLE_2,
        3: MUX_SINGLE_3,
    }

    def __init__(
        self,
        i2c_bus: int = 1,
        address: int = 0x48,
        volts_per_amp: float = 0.05,
        zero_voltage: float = 2.048,
        pga_config: int = PGA_4_096,
        conversion_delay_s: float = 0.01,
    ):
        self.address = address
        self.volts_per_amp = volts_per_amp
        self.zero_voltage = zero_voltage
        self.pga_config = pga_config
        self.conversion_delay_s = conversion_delay_s

        if smbus2 is None:
            raise RuntimeError(
                "smbus2 is required to use ADS1115CurrentSensor but is not installed"
            )

        self._bus = smbus2.SMBus(i2c_bus)

    @property
    def available(self) -> bool:
        """Return True if the I2C backend is available for use."""
        return smbus2 is not None

    def close(self):
        """Close the underlying SMBus handle and release I2C resources."""
        if getattr(self, '_bus', None) is not None:
            try:
                self._bus.close()
            except Exception:
                pass
            self._bus = None

    def _build_config(self, channel: int) -> int:
        """Build the ADS1115 configuration word for the requested input channel."""
        if channel not in self.CHANNEL_CONFIGS:
            raise ValueError(f"ADS1115 channel must be 0-3, got {channel}")

        config = (
            self.OS_SINGLE
            | self.CHANNEL_CONFIGS[channel]
            | self.pga_config
            | self.MODE_SINGLE_SHOT
            | self.DR_128
            | self.COMP_QUE_DISABLE
        )

        return config

    def _read_raw(self, channel: int) -> int:
        """Read the raw 16-bit ADC result from the specified ADS1115 channel."""
        config = self._build_config(channel)
        self._bus.write_i2c_block_data(
            self.address,
            self.POINTER_CONFIG,
            [(config >> 8) & 0xFF, config & 0xFF],
        )
        time.sleep(self.conversion_delay_s)

        raw_bytes = self._bus.read_i2c_block_data(
            self.address,
            self.POINTER_CONVERSION,
            2,
        )
        raw_value = struct.unpack('>h', bytes(raw_bytes))[0]
        return raw_value

    def read_voltage(self, channel: int) -> Optional[float]:
        """Read the ADS1115 channel and return the measured voltage.

        The ADS1115 raw value is converted using the ±4.096 V PGA range and the
        16-bit signed ADC resolution.
        """
        if not self.available:
            return None

        raw_value = self._read_raw(channel)
        voltage = raw_value * (4.096 / 32768.0)
        return voltage

    def read_current(self, channel: int) -> Optional[float]:
        """Convert the measured ADC voltage into current using INA240 calibration.

        `zero_voltage` should be the expected output at 0 A. The current is then
        calculated with:
            current = (voltage - zero_voltage) / volts_per_amp

        For a typical INA240 output with 50 mV/A gain, a 2.048 V zero point
        corresponds to 0 A.
        """
        voltage = self.read_voltage(channel)
        if voltage is None:
            return None

        return (voltage - self.zero_voltage) / self.volts_per_amp
