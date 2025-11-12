from PyQt6 import QtWidgets
from logs.logger_config import setup_logging
from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin
from gpiozero.pins.native import NativeFactory
from HomePage import HomePage
from BallSpinnerController import BallSpinnerController


def is_raspberry_pi():
    """Checks if the code is running on a Raspberry Pi."""
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                return True
    except FileNotFoundError:
        pass
    return False


if is_raspberry_pi :
    Device.pin_factory = MockFactory(pin_class=MockPWMPin)
else :
    Device.pin_factory = NativeFactory()

# Initialize logging at application startup
setup_logging()
#Device.pin_factory = MockFactory(pin_class=MockPWMPin)

if __name__ == '__main__':
    bsc = BallSpinnerController() #Create the BallSpinnerController instance
    app = QtWidgets.QApplication([])
    window = HomePage(bsc)
    window.show()
    QtWidgets.QApplication.exec()
