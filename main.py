from PyQt6 import QtWidgets
from PyQt6 import QtCore
from PyQt6.QtGui import QGuiApplication, QCursor, QIcon
import io
import os
import sys

from logs.logger_config import setup_logging
from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin
from frontend.BSCMainWindow import BSCMainWindow
from ErrorHandling.ErrorHandling import ErrorWindow

# Version Numbering: Major.Milestone.Patch
# Major: Significant changes, possibly breaking compatibility (e.g., 2.0.0)
# Milestone: After a milestone presentation, increment this (e.g., 1.1.0)
# Patch: any build after a milestone, increment this for bug fixes and minor improvements (e.g., 1.1.1, 1.1.2, etc.)
# Make sure v is lower case




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

def get_icon_path():
    """
    Find the application icon in both bundled and development environments.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Use only the official app icon.
    icon_candidates = [
        os.path.join(base_path, 'Icons', 'BSC_Icon.ico'),
        os.path.join(base_path, 'Icons', 'BSC_Icon.png'),
    ]
    
    for icon_path in icon_candidates:
        if os.path.exists(icon_path):
            return icon_path
    
    return None


if __name__ == '__main__':
    # Set up global exception handling to show errors in a PyQt window
    sys.excepthook = ErrorWindow
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
    
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)

    app = QtWidgets.QApplication([])
    
    # Load and set application icon
    icon_path = get_icon_path()
    if icon_path:
        try:
            app_icon = QIcon(icon_path)
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
        except Exception as e:
            pass
    
    
    # Re-get screen info after app creation
    screen = QGuiApplication.screenAt(QCursor.pos()) or app.primaryScreen()
    size = screen.size()
    
    app.setStyle("Fusion")  # Ensure QSS applies consistently across platforms
    app.setApplicationName("Ball Spinner Controller") 


    window = BSCMainWindow()
    
    # Set window icon (important for Windows taskbar)
    if icon_path:
        try:
            window.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
    
    # ensure all combo boxes use a list view with spacing for their popup
    # and double their minimum width so they appear wider
    def _patch_comboboxes(parent):
        for cb in parent.findChildren(QtWidgets.QComboBox):
            view = QtWidgets.QListView(cb)
            view.setSpacing(16)
            cb.setView(view)
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
        window.resize(window_width, window_height)
        window.showMaximized()

    QtWidgets.QApplication.exec()
