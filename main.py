from PyQt6 import QtWidgets
from PyQt6 import QtCore
from PyQt6.QtGui import QPalette, QColor
import io
import os

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
from frontend.BSCMainWindow import BSCMainWindow


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
    # Set a global Qt scale factor at runtime. Change to desired value.
    # Use 0.5 to scale the UI designed for 1920x1080 down to half-size.
    os.environ.setdefault("QT_SCALE_FACTOR", "0.5")
    # Let Qt consider per-screen scaling as well
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    # Note: In PyQt6 some AA_* application attributes may not be available
    # via the same names as older bindings. We set environment variables
    # above (`QT_SCALE_FACTOR`, `QT_AUTO_SCREEN_SCALE_FACTOR`) which
    # Qt respects on startup for scaling. If you need explicit attributes
    # for a different Qt binding, they can be added here guarded by
    # attribute existence checks.

    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")

    # Apply qdarktheme stylesheet and palette. These must run before any
    # widgets are instantiated or UI files are loaded.
    #app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
    app.setPalette(qdarktheme.load_palette("dark"))

    window = BSCMainWindow()
    window.show()

    QtWidgets.QApplication.exec()
