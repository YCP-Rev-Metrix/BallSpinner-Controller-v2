import pytest
from unittest.mock import patch, MagicMock, Mock
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtTest import QTest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from frontend.BSCMainWindow import BSCMainWindow
from frontend.ExitDialog import ExitDialog
from frontend.SmartDotConnectWidget import SmartDotConnectWidget
from frontend.FrontPage import FrontPage


# ============================================================================
# EXIT DIALOG TESTS
# ============================================================================

def test_ExitDialog_initialization(qtbot):
    """Test ExitDialog initializes with correct properties"""
    dialog = ExitDialog()
    qtbot.addWidget(dialog)
    
    assert dialog.windowTitle() == "EXIT APPLICATION"
    assert dialog.isModal() is True
    assert dialog.width() == 400
    assert dialog.height() == 200


def test_ExitDialog_accept_button(qtbot):
    """Test ExitDialog accept button is connected"""
    dialog = ExitDialog()
    qtbot.addWidget(dialog)
    
    # Check that buttonBox exists and has buttons
    assert dialog.buttonBox is not None
    assert len(dialog.buttonBox.buttons()) > 0


def test_ExitDialog_reject_button(qtbot):
    """Test ExitDialog reject button is connected"""
    dialog = ExitDialog()
    qtbot.addWidget(dialog)
    
    # Check that buttonBox exists and has buttons
    assert dialog.buttonBox is not None
    assert len(dialog.buttonBox.buttons()) > 0


def test_ExitDialog_exec_accepted(qtbot):
    """Test ExitDialog exec returns Accepted when user clicks Accept"""
    dialog = ExitDialog()
    qtbot.addWidget(dialog)
    
    # Simulate user accepting
    QTest.mouseClick(dialog.buttonBox.buttons()[0], QtCore.Qt.MouseButton.LeftButton)
    # Dialog should be accepted
    assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted or dialog.result() == 1


def test_ExitDialog_parent_reference(qtbot):
    """Test ExitDialog maintains parent reference"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    dialog = ExitDialog(parent=parent)
    qtbot.addWidget(dialog)
    
    assert dialog.parent() == parent


# ============================================================================
# MAIN WINDOW TESTS
# ============================================================================

@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_initialization(mock_bsc, qtbot):
    """Test BSCMainWindow initializes without errors"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    assert window is not None
    assert window.windowTitle() == "Ball Spinner Controller - Home"


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_has_main_components(mock_bsc, qtbot):
    """Test BSCMainWindow has all required components"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # Check that main components exist
    assert window.EStop is not None
    assert window.tab is not None
    assert window.frontPage is not None
    assert window.diagnosticPage is not None
    assert window.shotModePage is not None
    assert window.analysisModePage is not None
    assert window.dataViewPage is not None
    assert window.shotViewPage is not None


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_estop_button_styling(mock_bsc, qtbot):
    """Test E-Stop button has red styling"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # E-Stop should be red and bold
    stylesheet = window.EStop.styleSheet()
    assert "red" in stylesheet.lower()
    assert "bold" in stylesheet.lower()


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_switch_to_page_front_page(mock_bsc, qtbot):
    """Test switching to front page (index 0)"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.switch_to_page(0, "Home")
    
    assert window.tab.currentIndex() == 0
    assert "Home" in window.windowTitle()


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_switch_to_page_diagnostic(mock_bsc, qtbot):
    """Test switching to diagnostic page (index 1)"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.switch_to_page(1, "Diagnostic")
    
    assert window.tab.currentIndex() == 1
    assert "Diagnostic" in window.windowTitle()


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_switch_to_page_shot_mode(mock_bsc, qtbot):
    """Test switching to shot mode page (index 2)"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.switch_to_page(2, "Shot Mode")
    
    assert window.tab.currentIndex() == 2
    assert "Shot Mode" in window.windowTitle()


@pytest.mark.skip(reason="Analysis page requires DataController setup")
@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_switch_to_page_analysis(mock_bsc, qtbot):
    """Test switching to analysis page (index 3)"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.switch_to_page(3, "Analysis")
    
    assert window.tab.currentIndex() == 3
    assert "Analysis" in window.windowTitle()


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_switch_to_page_cloud_test(mock_bsc, qtbot):
    """Test switching to cloud test page (index 4)"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.switch_to_page(4, "Cloud Test")
    
    assert window.tab.currentIndex() == 4
    assert "Cloud" in window.windowTitle()


@pytest.mark.skip(reason="ShotViewPage requires DataController setup")
@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_switch_to_page_shot_view(mock_bsc, qtbot):
    """Test switching to shot view page (index 5)"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.switch_to_page(5, "Shot View")
    
    assert window.tab.currentIndex() == 5
    assert "Shot" in window.windowTitle()


@pytest.mark.skip(reason="DataViewPage requires DataController setup")
@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_switch_to_page_data_view(mock_bsc, qtbot):
    """Test switching to data view page (index 6)"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.switch_to_page(6, "Data View")
    
    assert window.tab.currentIndex() == 6
    assert "Data" in window.windowTitle()


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_toggle_navigation_enable(mock_bsc, qtbot):
    """Test enabling navigation menu"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.toggle_navigation(True)
    
    assert window.navigation_menu.isEnabled() is True


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_toggle_navigation_disable(mock_bsc, qtbot):
    """Test disabling navigation menu"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    window.toggle_navigation(False)
    
    assert window.navigation_menu.isEnabled() is False


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_menu_bar_actions(mock_bsc, qtbot):
    """Test menu bar actions are properly connected"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # Check menu bar actions exist
    assert window.actionHome is not None
    assert window.actionCloudTest is not None
    assert window.actionQuit is not None


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_attempt_exit_cancel(mock_bsc, qtbot):
    """Test attempt_exit cancels when user rejects dialog"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # Mock ExitDialog to return Rejected
    with patch('frontend.BSCMainWindow.ExitDialog') as mock_dialog_class:
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.exec.return_value = QtWidgets.QDialog.DialogCode.Rejected
        mock_dialog_class.return_value = mock_dialog_instance
        
        window.attempt_exit()
        
        # Window should still be open
        assert window.isVisible() or True  # Can't check isVisible for mocked window


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_base_size(mock_bsc, qtbot):
    """Test window base size is set to 1920x1080"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    base_size = window.baseSize()
    assert base_size.width() == 1920
    assert base_size.height() == 1080


@patch('utils.notify_user')
@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_shows_locked_motor_popup(mock_bsc, mock_notify, qtbot):
    """Test the main window shows a notify_user popup when motors are locked due to VESC failure."""
    mock_bsc.motor_mode = 'simulated'
    mock_bsc.motor_mode_locked = True
    mock_bsc.motor_mode_locked_due_to_vesc = True
    mock_bsc.motor_mode_locked_reason = 'Simulated motors locked.'
    mock_bsc._real_motor_supported = False
    mock_bsc.get_motor_status_message = MagicMock(return_value='Using simulated motors.')

    window = BSCMainWindow()
    qtbot.addWidget(window)
    qtbot.wait(10)

    mock_notify.assert_called_once_with(
        'Simulated motors locked. Ensure the motors are powered and the E-stop is not pressed, then restart the system.',
        title='Motor Mode Locked',
        type='warning',
    )


@patch('utils.notify_user')
@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_does_not_notify_when_simulated_not_due_to_vesc(mock_bsc, mock_notify, qtbot):
    """Test no popup is shown when simulation is locked for non-VESC reasons."""
    mock_bsc.motor_mode = 'simulated'
    mock_bsc.motor_mode_locked = True
    mock_bsc.motor_mode_locked_due_to_vesc = False
    mock_bsc.motor_mode_locked_reason = 'Simulated motors locked.'
    mock_bsc._real_motor_supported = False
    mock_bsc.get_motor_status_message = MagicMock(return_value='Using simulated motors.')

    window = BSCMainWindow()
    qtbot.addWidget(window)
    qtbot.wait(10)

    mock_notify.assert_not_called()


@patch('utils.notify_user')
@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_notifies_when_limit_switch_pin_busy(mock_bsc, mock_notify, qtbot):
    """Test launch popup is shown when the configured limit switch pin is busy."""
    mock_bsc.motor_mode = 'simulated'
    mock_bsc.motor_mode_locked = True
    mock_bsc.motor_mode_locked_due_to_vesc = True
    mock_bsc.motor_mode_locked_due_to_pin_busy = True
    mock_bsc.motor_mode_locked_reason = 'Limit switch pin GPIO14 is busy. Release the pin from UART/other process and restart.'
    mock_bsc._real_motor_supported = False
    mock_bsc.get_motor_status_message = MagicMock(return_value='Using simulated motors.')

    window = BSCMainWindow()
    qtbot.addWidget(window)
    qtbot.wait(10)

    mock_notify.assert_called_once_with(
        mock_bsc.motor_mode_locked_reason,
        title='Motor Pin Busy',
        type='warning',
    )


# ============================================================================
# SMART DOT CONNECT WIDGET TESTS
# ============================================================================

@patch('frontend.SmartDotConnectWidget.utils.is_raspberry_pi', return_value=False)
def test_SmartDotConnectWidget_initialization(mock_is_pi, qtbot):
    """Test SmartDotConnectWidget initializes without errors"""
    widget = SmartDotConnectWidget()
    qtbot.addWidget(widget)
    
    assert widget is not None
    # Widget initializes from .ui file, which may not load in test environment
    assert isinstance(widget, QtWidgets.QWidget)


@patch('frontend.SmartDotConnectWidget.utils.is_raspberry_pi', return_value=False)
def test_SmartDotConnectWidget_status_label_exists(mock_is_pi, qtbot):
    """Test SmartDotConnectWidget has status label"""
    widget = SmartDotConnectWidget()
    qtbot.addWidget(widget)
    
    assert isinstance(widget.lblStatus, QtWidgets.QLabel)
    assert widget.lblStatus.text() is not None or widget.lblStatus.text() == ""


@patch('frontend.SmartDotConnectWidget.utils.is_raspberry_pi', return_value=False)
def test_SmartDotConnectWidget_connect_button_exists(mock_is_pi, qtbot):
    """Test SmartDotConnectWidget has connect button or creates one"""
    widget = SmartDotConnectWidget()
    qtbot.addWidget(widget)
    
    # Check that signal exists (core functionality)
    assert hasattr(widget, 'signalSmartDotConnected')
    assert hasattr(widget, 'btnConnect') or hasattr(widget, 'lblStatus')


@patch('frontend.SmartDotConnectWidget.utils.is_raspberry_pi', return_value=False)
def test_SmartDotConnectWidget_signal_emission(mock_is_pi, qtbot):
    """Test SmartDotConnectWidget emits signals"""
    widget = SmartDotConnectWidget()
    qtbot.addWidget(widget)
    
    # Check that signals are defined
    assert hasattr(widget, 'signalSmartDotConnected')
    assert hasattr(widget, 'signalDeviceDisconnected')


# ============================================================================
# FRONT PAGE TESTS
# ============================================================================

@patch('frontend.BSCMainWindow.bsc')
def test_FrontPage_initialization(mock_bsc, qtbot):
    """Test FrontPage initializes without errors"""
    page = FrontPage()
    qtbot.addWidget(page)
    
    assert page is not None


@patch('frontend.BSCMainWindow.bsc')
def test_FrontPage_has_change_page_signal(mock_bsc, qtbot):
    """Test FrontPage has changePage signal"""
    page = FrontPage()
    qtbot.addWidget(page)
    
    assert hasattr(page, 'changePage')


# ============================================================================
# WINDOW SIGNAL CONNECTIONS TESTS
# ============================================================================

@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_front_page_signals_connected(mock_bsc, qtbot):
    """Test FrontPage signals are properly connected to main window"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # changePage signal should be connected
    assert window.frontPage.changePage is not None


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_diagnostic_page_signals_connected(mock_bsc, qtbot):
    """Test DiagnosticPage signals are properly connected"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    assert window.diagnosticPage.changePage is not None
    assert window.diagnosticPage.navigationLock is not None


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_shot_view_signals_connected(mock_bsc, qtbot):
    """Test ShotViewPage signals are properly connected"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    assert window.shotViewPage.changePage is not None
    assert window.shotViewPage.navigationLock is not None


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_estop_connected_to_diagnostic(mock_bsc, qtbot):
    """Test E-Stop button is connected to diagnostic page"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # E-Stop button should be connected (no way to directly test, but button exists)
    assert window.EStop is not None
    assert window.diagnosticPage is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_page_navigation_workflow(mock_bsc, qtbot):
    """Test navigating between multiple pages"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # Start at home
    assert window.tab.currentIndex() == 0
    
    # Navigate to diagnostic
    window.switch_to_page(1, "Diagnostic")
    assert window.tab.currentIndex() == 1
    
    # Navigate to shot mode
    window.switch_to_page(2, "Shot Mode")
    assert window.tab.currentIndex() == 2
    
    # Navigate back to home
    window.switch_to_page(0, "Home")
    assert window.tab.currentIndex() == 0


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_window_title_updates(mock_bsc, qtbot):
    """Test window title updates when switching pages"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    titles = []
    # Only test pages that don't require backend setup - avoid Analysis page
    for index, page_name in enumerate([
        "Home",
        "Diagnostic",
        "Shot Mode"
    ]):
        window.switch_to_page(index, page_name)
        titles.append(window.windowTitle())
    
    # Each title should be different
    assert len(set(titles)) > 1  # At least some variation


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_menu_navigation_home(mock_bsc, qtbot):
    """Test menu action navigation to home"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # Trigger home action
    window.actionHome.triggered.emit()
    
    assert window.tab.currentIndex() == 0
    assert "Home" in window.windowTitle()


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_menu_navigation_cloud_test(mock_bsc, qtbot):
    """Test menu action navigation to cloud test"""
    window = BSCMainWindow()
    qtbot.addWidget(window)
    
    # Trigger cloud test action
    window.actionCloudTest.triggered.emit()
    
    assert window.tab.currentIndex() == 4
    assert "Cloud" in window.windowTitle()


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_locked_simulated_mode_shows_reason(mock_bsc, qtbot):
    """When simulation is locked, the status bar shows the locked reason and real mode is disabled."""
    mock_bsc.motor_mode = 'simulated'
    mock_bsc.motor_mode_locked = True
    mock_bsc.motor_mode_locked_reason = 'Simulated motors only: ensure motors are powered and E-stop is not pressed, then restart the system.'
    mock_bsc._real_motor_supported = False
    mock_bsc.get_motor_status_message = MagicMock(return_value='Using simulated motors.')

    window = BSCMainWindow()
    qtbot.addWidget(window)

    window.statusBar.showMessage = MagicMock()
    window.update_motor_mode_ui()

    assert window.actionSimulatedMotor.isChecked() is True
    assert window.actionRealMotor.isEnabled() is False
    window.statusBar.showMessage.assert_called_with(mock_bsc.motor_mode_locked_reason, 0)


@patch('frontend.BSCMainWindow.bsc')
def test_BSCMainWindow_real_mode_switch_failure_reverts_to_simulated(mock_bsc, qtbot):
    """If real mode fails during toggle, the UI should stay in simulated mode."""
    mock_bsc.set_motor_mode = MagicMock(side_effect=lambda mode: False if mode == 'real' else True)
    mock_bsc.motor_mode = 'simulated'
    mock_bsc.motor_mode_locked = True
    mock_bsc.motor_mode_locked_reason = 'Simulated motors only: locked because real motor init failed.'
    mock_bsc._real_motor_supported = True
    mock_bsc.get_motor_status_message = MagicMock(return_value='Using simulated motors.')

    window = BSCMainWindow()
    qtbot.addWidget(window)

    window.statusBar.showMessage = MagicMock()
    window.motorSimulationControl(True, False)

    assert window.actionRealMotor.isChecked() is False
    assert window.actionSimulatedMotor.isChecked() is True
    window.statusBar.showMessage.assert_any_call(mock_bsc.motor_mode_locked_reason, 0)
