"""
Development tools module.

This module contains utility tools for testing, debugging, and development tasks.
"""

from pathlib import Path

# Module metadata
__version__ = "1.0.0"
__all__ = ["selector_tester"]

# Ensure results directory exists
TOOLS_DIR = Path(__file__).parent
RESULTS_DIR = TOOLS_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)
