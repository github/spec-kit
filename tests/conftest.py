"""
Pytest configuration file for infrakit-cli tests.

This file sets up the Python path correctly so that the src directory
is included in the import path for all tests.
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
