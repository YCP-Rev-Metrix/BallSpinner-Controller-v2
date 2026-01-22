"""
Unit Tests conftest.py

Configuration specific to unit tests.
Unit tests use mocking and test components in isolation.
"""

import pytest
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
