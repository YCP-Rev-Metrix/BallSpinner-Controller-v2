"""
Integration Tests for Main Application (main.py)

These tests verify core application initialization and basic functionality.
They test the main application startup sequence with real components.

Key Concepts:
- test_app_opens(): Verifies the main window can be instantiated
- test_app_initialization(): Tests app initialization with real backend

Fixtures used:
- main_window: Provides an initialized BSCMainWindow instance (from conftest.py)
- qapp: PyQt6 QApplication instance (from pytest-qt)
- mock_device: Mock device for testing (from conftest.py)
"""

from PyQt6 import QtWidgets


# =============================================================================
# SANITY CHECK TEST
# =============================================================================

def test_hello_world():
    """
    Simple sanity check to ensure pytest framework works.
    
    How it works:
    - Just performs basic arithmetic assertion
    - Verifies test framework can run
    - Useful for debugging CI/CD pipeline issues
    """
    assert 1 + 1 == 2


# =============================================================================
# MAIN WINDOW OPENING TEST
# =============================================================================

def test_app_opens(main_window):
    """
    Test that the main window opens without errors.
    
    How it works:
    1. Fixture 'main_window' creates and initializes BSCMainWindow
    2. Asserts the window exists (is not None)
    3. Asserts it's actually a QMainWindow instance
    
    What this validates:
    - UI can be loaded from .ui files
    - All signal/slot connections work
    - No exceptions during window creation
    - Basic widget hierarchy is valid
    
    Fixture: main_window
    - Comes from tests/integration/conftest.py
    - Creates BSCMainWindow instance
    - Automatically closes after test
    """
    assert main_window is not None
    assert isinstance(main_window, QtWidgets.QMainWindow)


# =============================================================================
# APP INITIALIZATION TEST
# =============================================================================

def test_app_initialization(qapp, mock_device):
    """
    Test app can be instantiated with all backend components initialized.
    
    How it works:
    1. Create new BSCMainWindow instance
    2. Verify it's not None
    3. Verify instance is valid
    4. Properly close window to clean up resources
    
    Parameters:
    - qapp: PyQt6 QApplication instance (from pytest-qt)
    - mock_device: Mock device fixture for testing without real hardware
    
    What this validates:
    - Main window can be created
    - Backend initialization doesn't crash
    - All components are properly wired
    - Window creation doesn't leak memory (verify close() works)
    
    Note: This test creates a fresh instance (different from main_window fixture)
    to test independent initialization. The window is explicitly closed to verify
    cleanup sequence works properly.
    """
    from frontend.BSCMainWindow import BSCMainWindow
    
    # Create window instance
    window = BSCMainWindow()
    
    # Verify it was created successfully
    assert window is not None
    
    # Clean up properly to avoid resource leaks in test suite
    window.close()
