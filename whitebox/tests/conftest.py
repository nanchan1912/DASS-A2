"""Pytest path setup for the whitebox submission package."""

from pathlib import Path
import sys


WHITEBOX_CODE = Path(__file__).resolve().parents[1] / "code"

if str(WHITEBOX_CODE) not in sys.path:
    sys.path.insert(0, str(WHITEBOX_CODE))
