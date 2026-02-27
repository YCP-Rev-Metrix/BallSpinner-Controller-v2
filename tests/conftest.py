"""
Pytest Fixtures for Testing

Fixtures are functions that set up test resources (like mock objects or widgets)
and clean them up afterwards. They make tests cleaner and reduce code duplication.

Fixture Pattern:
    @pytest.fixture
    def my_fixture():
        # SETUP: Create resources
        resource = create_something()
        
        # YIELD: Provide resource to test
        yield resource
        
        # CLEANUP: Clean up after test
        resource.close()

How Fixtures Work:
1. pytest discovers fixtures (functions marked with @pytest.fixture)
2. Test functions request fixtures (by including them as parameters)
3. pytest runs fixture setup, passes result to test
4. Test runs
5. pytest runs fixture cleanup (after yield)

Benefits:
- Reusable setup/cleanup code
- Cleaner test code (no setup boilerplate)
- Fixtures can depend on other fixtures
- Automatic cleanup prevents resource leaks
"""

import pytest
from PyQt6 import QtWidgets
from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin
from frontend.BSCMainWindow import BSCMainWindow


# ============================================================================
# HARDWARE MOCKING FIXTURES
# ============================================================================

@pytest.fixture
def mock_device():
    """
    Setup mock GPIO for testing without real hardware.
    
    How it works:
    1. gpiozero is the GPIO library used for motor/sensor control
    2. Device.pin_factory controls how GPIO works
    3. MockFactory creates fake GPIO pins
    4. MockPWMPin fakes PWM (pulse-width modulation) pins used for motors
    
    What it does:
    - SETUP: Configures gpiozero to use mock pins instead of real GPIO
    - All GPIO operations work but don't touch real hardware
    - Motors respond to commands in simulation
    - Tests run fast without hardware dependencies
    
    CLEANUP: Resets pin_factory to None
    - Prevents interference with other tests
    - Cleans up resources
    
    Usage in tests:
    def test_motor(mock_device):
        # mock_device ensures no real GPIO happens
        motor = BDCMotor(pin=2)  # Works without real Raspberry Pi
        motor.start()  # Simulated motor start
    
    Why needed?
    - CI/CD servers don't have Raspberry Pi GPIO
    - Tests should work on any machine (Mac, Linux, Windows)
    - No risk of accidentally controlling real motors during tests
    - Makes tests fast and repeatable
    """
    # SETUP: Replace real GPIO with mock GPIO
    Device.pin_factory = MockFactory(pin_class=MockPWMPin)
    
    # YIELD: Provide to test
    yield
    
    # CLEANUP: Reset GPIO factory
    Device.pin_factory = None


# ============================================================================
# PYQT6 APPLICATION FIXTURES
# ============================================================================

@pytest.fixture
def qapp():
    """
    Create PyQt6 QApplication for testing.
    
    How it works:
    - PyQt6 requires a QApplication instance to run
    - Only ONE QApplication can exist per process
    - This fixture creates or reuses the existing application
    
    Pattern:
    1. Check if QApplication already exists (reuse it)
    2. If not, create new one
    3. YIELD: Provide to test
    4. CLEANUP: Call app.quit()
    
    Why this pattern?
    - Multiple tests in same run need same QApplication
    - Can't create multiple QApplication instances
    - pytest-qt usually provides this, but we define it explicitly
    
    What the test gets:
    - Active QApplication instance that can run widgets
    - Application is ready for GUI operations
    
    Usage in tests:
    def test_my_gui(qapp):
        # qapp is available but usually implicit via qtbot
        window = BSCMainWindow()
        # ... test code ...
    
    Note: You usually don't use qapp directly
    - pytest-qt provides 'qtbot' fixture which uses qapp internally
    """
    # SETUP: Get or create QApplication
    app = QtWidgets.QApplication.instance()
    if app is None:
        # No existing app, create new one
        app = QtWidgets.QApplication([])
    
    # YIELD: Provide to test
    yield app
    
    # CLEANUP: Clean up Qt application
    app.quit()


# ============================================================================
# MAIN WINDOW FIXTURES
# ============================================================================

@pytest.fixture
def main_window(qapp, mock_device):
    """
    Create BSCMainWindow instance for testing.
    
    How it works:
    1. Depends on 'qapp' fixture (Qt application running)
    2. Depends on 'mock_device' fixture (GPIO mocked)
    3. Creates new BSCMainWindow instance
    4. YIELD: Provide to test
    5. CLEANUP: Close window properly
    
    Fixture Dependencies:
    - qapp: Provides QApplication needed to create widgets
    - mock_device: Ensures no real GPIO operations
    
    What the test gets:
    - Fully initialized BSCMainWindow
    - All UI loaded from .ui files
    - All signals/slots connected
    - Backend initialized
    - Ready for interaction
    
    Usage in tests:
    def test_window_opens(main_window):
        assert main_window is not None
        assert main_window.isVisible()
        # ... test code ...
    
    Cleanup:
    - window.close() called automatically
    - Prevents memory leaks
    - Prevents orphaned windows in test suite
    
    This is the most common fixture for GUI testing
    """
    # SETUP: Create main window (depends on qapp and mock_device)
    window = BSCMainWindow()
    
    # YIELD: Provide to test
    yield window
    
    # CLEANUP: Close window to clean up resources
    window.close()


@pytest.fixture(autouse=True)
def suppress_wavelet_helper(monkeypatch):
    """Stub out the wavelet helper dialog for every test.

    The real ``WavletHelperWidget`` pops up a modal dialog when its
    ``exec()`` method is called.  Tests that invoke ``WaveletDialog.performWavelet``
    without supplying a ``wavelet`` argument would hang waiting for user input.
    Some individual tests already monkeypatch the helper to return specific
    values; this globally applied fixture provides a harmless default so no
    test ever shows a real dialog.  The dummy returns ``Accepted`` from
    ``exec()`` and an empty list from ``get_list()``.
    """
    from PyQt6 import QtWidgets
    from frontend import WaveletDialog as _WD

    class DummyHelper:
        def __init__(self, parent=None):
            pass

        def exec(self):
            return QtWidgets.QDialog.DialogCode.Accepted

        def get_list(self):
            return []

    # also override the concrete helper class itself for tests that import it
    import frontend.WavletHelperWidget as _WHW
    def fake_exec(self):
        return QtWidgets.QDialog.DialogCode.Accepted
    _WHW.WavletHelperWidget.exec = fake_exec

    monkeypatch.setattr(_WD, 'WavletHelperWidget', DummyHelper)


@pytest.fixture
def sample_fixture():
    """
    Sample fixture for reference.
    
    How fixtures work in simplest form:
    - Return a value
    - No setup/cleanup needed
    
    Usage:
    def test_something(sample_fixture):
        assert sample_fixture == "Hello, World!"
    """
    return "Hello, World!"
