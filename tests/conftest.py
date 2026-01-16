import pytest
from PyQt6 import QtWidgets
from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin
from frontend.BSCMainWindow import BSCMainWindow


@pytest.fixture
def mock_device():
    """Setup mock GPIO for testing."""
    Device.pin_factory = MockFactory(pin_class=MockPWMPin)
    yield
    Device.pin_factory = None


@pytest.fixture
def qapp():
    """Create QApplication for testing."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    yield app
    app.quit()


@pytest.fixture
def main_window(qapp, mock_device):
    """Create BSCMainWindow instance for testing."""
    window = BSCMainWindow()
    yield window
    window.close()


@pytest.fixture
def sample_fixture():
    return "Hello, World!"