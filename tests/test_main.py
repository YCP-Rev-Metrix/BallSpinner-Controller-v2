from PyQt6 import QtWidgets


def test_hello_world():
    assert 1 + 1 == 2


def test_app_opens(main_window):
    """Test that the main window opens without errors."""
    assert main_window is not None
    assert isinstance(main_window, QtWidgets.QMainWindow)


def test_app_initialization(qapp, mock_device):
    """Test app can be instantiated."""
    from frontend.BSCMainWindow import BSCMainWindow
    window = BSCMainWindow()
    assert window is not None
    window.close()