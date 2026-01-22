"""
Integration Tests conftest.py - Configuration for Integration Test Suite

Configuration specific to integration tests.

Integration Tests vs Unit Tests (conftest comparison):
┌─────────────────────────────────────────────────────────────────┐
│                        Unit Tests                Integration     │
│─────────────────────────────────────────────────────────────────│
│ Location:      tests/unit/              tests/integration/       │
│ Mocking:       Heavy (@patch)           None (real components)   │
│ Speed:         Fast (~100ms each)       Slower (~1s each)        │
│ Dependencies:  Isolated                 Full app running         │
│ GPIO:          mocked                   real (or mocked for CI)  │
│ Testing:       Component logic          User workflows           │
│─────────────────────────────────────────────────────────────────│
│ conftest:      Mock fixtures            Real component fixtures  │
└─────────────────────────────────────────────────────────────────┘

What goes in integration conftest.py:
- Fixtures that use REAL components (not mocked)
- Fixtures for complete application workflows
- Setup for data persistence testing (databases, files)
- Configuration for slow/expensive resources

What does NOT go here:
- MockFactory (that's in root conftest.py for unit tests)
- Individual component mocks (@patch)
- Fixtures that isolate components

Fixture Inheritance:
- Integration tests can use fixtures from:
  1. tests/integration/conftest.py (this file)
  2. tests/conftest.py (root, shared fixtures)
- Integration fixtures override unit fixtures with same name

Example:
- tests/conftest.py: main_window(qapp, mock_device)
  → Uses mock GPIO
- tests/integration/conftest.py: could define:
  real_main_window(qapp) → Uses real GPIO (if on Raspberry Pi)
"""

import pytest
import sys
import os

# ============================================================================
# PYTHON PATH SETUP
# ============================================================================

# Add parent directories to path for imports
# This allows tests to import from the main application
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Now imports like these work:
# from frontend.BSCMainWindow import BSCMainWindow
# from backend.models.SessionData import SessionData
# from backend.motors.BDCMotor import BDCMotor

# ============================================================================
# INTEGRATION TEST SPECIFIC FIXTURES
# ============================================================================

# Add integration-specific fixtures here
# Example: Real database, real file I/O, real cloud API calls

# Example fixture structure (commented out, uncomment to use):

# @pytest.fixture
# def real_cloud_api():
#     """
#     Create real CloudAPI instance for integration testing.
#     
#     Differs from unit tests which mock the API.
#     Integration tests actually call the API (with test account).
#     
#     Setup: Connect to test cloud server
#     Yield: CloudAPI instance
#     Cleanup: Close connection
#     """
#     from backend.cloud_api.CloudAPI import CloudAPI
#     api = CloudAPI(server="test.example.com")
#     api.connect()
#     yield api
#     api.disconnect()

# @pytest.fixture
# def temporary_database():
#     """
#     Create temporary SQLite database for integration testing.
#     
#     Integration tests need to persist data.
#     Unit tests use in-memory SQLite (no setup needed).
#     
#     Setup: Create temp database file
#     Yield: Database connection
#     Cleanup: Delete temp file
#     """
#     import tempfile
#     import sqlite3
#     
#     # Create temporary file
#     fd, path = tempfile.mkstemp(suffix='.db')
#     os.close(fd)
#     
#     # Create connection
#     conn = sqlite3.connect(path)
#     yield conn
#     
#     # Cleanup
#     conn.close()
#     os.unlink(path)
