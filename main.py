from PyQt6 import QtWidgets
from PyQt6 import QtCore
from PyQt6.QtGui import QGuiApplication, QCursor
import io

# monkey-patch QComboBox constructor so every combo starts with a larger width
_orig_qcombobox_init = QtWidgets.QComboBox.__init__

def _patched_qcombobox_init(self, *args, **kwargs):
    _orig_qcombobox_init(self, *args, **kwargs)
    # schedule width adjustment after the widget has its layout hints
    QtCore.QTimer.singleShot(0, lambda cb=self: cb.setMinimumWidth(cb.sizeHint().width() * 2))

QtWidgets.QComboBox.__init__ = _patched_qcombobox_init
import os
import sys

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
    # Get screen info before creating the app to set scaling
    temp_app = QtWidgets.QApplication([])
    screen = QGuiApplication.screenAt(QCursor.pos()) or temp_app.primaryScreen()
    size = screen.size()
    width_scale = size.width() / 1920.0
    height_scale = size.height() / 1080.0
    scale = min(width_scale, height_scale)
    #scale -= 0.05  # Slightly reduce scale to ensure fit
    scale = max(0.1, scale)  # Prevent too-small scalex
    
    print(f"Screen resolution: {size.width()}x{size.height()}")
    print(f"Scale factor: {scale:.2f}")
    
    # Set Qt scale factor before creating the main app
    os.environ["QT_SCALE_FACTOR"] = f"{scale:.2f}"
    temp_app.quit()
    del temp_app
    
    # Qt 6 enables high DPI scaling by default; only set menu bar behavior explicitly
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)

    app = QtWidgets.QApplication([])
    
    # Re-get screen info after app creation
    screen = QGuiApplication.screenAt(QCursor.pos()) or app.primaryScreen()
    size = screen.size()
    
    app.setStyle("Fusion")  # Ensure QSS applies consistently across platforms


    window = BSCMainWindow()
    # ensure all combo boxes use a list view with spacing for their popup
    # and double their minimum width so they appear wider
    def _patch_comboboxes(parent):
        for cb in parent.findChildren(QtWidgets.QComboBox):
            view = QtWidgets.QListView(cb)
            view.setSpacing(16)
            cb.setView(view)
            # adjust width based on current size hint
            hint = cb.sizeHint().width()
            if hint > 0:
                cb.setMinimumWidth(hint * 2)
    _patch_comboboxes(window)
    #Combo boxes refuse to cooperate so this is the best option
    
    # Calculate the largest 16:9 window that fits within the screen
    screen_geometry = screen.geometry()
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()
    
    # Try fitting by width
    fit_by_width_height = int(screen_width * 9 / 16)
    # Try fitting by height
    fit_by_height_width = int(screen_height * 16 / 9)
    
    if fit_by_width_height <= screen_height:
        # Width-constrained: use full width, calculate height
        window_width = screen_width
        window_height = fit_by_width_height
    else:
        # Height-constrained: use full height, calculate width
        window_width = fit_by_height_width
        window_height = screen_height
    
    # Resize to maintain aspect ratio
    window.resize(window_width, window_height)
    
    # Move window to the target screen
    window.move(screen_geometry.x(), screen_geometry.y())
    window.setScreen(screen)
    
    # Make window fullscreen
    if scale == 1:
        window.showFullScreen()
    else:   
        window.showMaximized()

    QtWidgets.QApplication.exec()
