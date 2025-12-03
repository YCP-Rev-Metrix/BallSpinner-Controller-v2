from PyQt6 import QtWidgets
from PyQt6 import QtCore
from PyQt6.QtGui import QPalette, QColor, QGuiApplication, QCursor
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

    # Create a temporary application to get screen info for scaling
    temp_app = QtWidgets.QApplication([])
    screen = QGuiApplication.screenAt(QCursor.pos()) or temp_app.primaryScreen()
    scale = 1.0
    size = screen.size()
    try:
        #Get height and width relative to 1920x1080
        width = float(size.width())/1920.0
        height = float(size.height())/1080.0
        scale = min(width, height)
        #scale = 0.5 #test value for debugging
        print(f"Screen scale factor: {scale:.2f}")
        os.environ["QT_SCALE_FACTOR"] = f"{scale:.2f}"
        os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    except Exception as e:
        print(f"Error determining screen size: {e}")
        scale = 1.0
    finally:
        #always attempt to clean up temp app
        try:
            temp_app.quit()
            del temp_app
        except Exception:
            #If something else goes wrong, just pass
            pass

    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")


    # Apply qdarktheme stylesheet and palette. These must run before any
    # widgets are instantiated or UI files are loaded.
    #app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
    app.setPalette(qdarktheme.load_palette("dark"))

    window = BSCMainWindow()
    window.show()

    #Make window full screen
    #window.showFullScreen()

    QtWidgets.QApplication.exec()
