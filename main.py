from PyQt6 import QtWidgets
from PyQt6.QtGui import QPalette, QColor
import io

try:
    import qdarktheme
except ImportError as exc:
    raise ImportError(
        "qdarktheme is required for the dark theme. Install with: ``pip install qdarktheme``"
    ) from exc

from logs.logger_config import setup_logging
from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin
from gpiozero.pins.native import NativeFactory
from frontend.HomePage import HomePage


def is_raspberry_pi():
    """Checks if the code is running on a Raspberry Pi."""
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                return True
    except FileNotFoundError:
        pass
    return False


if is_raspberry_pi():
    pass
        # Device.pin_factory = NativeFactory()
else:
    # Use a mock pin factory off-device (e.g., macOS, dev machine)
    Device.pin_factory = MockFactory(pin_class=MockPWMPin)

# Initialize logging at application startup
setup_logging()
#Device.pin_factory = MockFactory(pin_class=MockPWMPin)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")

    # Apply qdarktheme stylesheet and palette. These must run before any
    # widgets are instantiated or UI files are loaded.
    app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
    app.setPalette(qdarktheme.load_palette("dark"))

    window = HomePage()
    window.show()

    QtWidgets.QApplication.exec()
