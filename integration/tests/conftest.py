"""Pytest path setup for the integration submission package."""

from pathlib import Path
import sys


INTEGRATION_CODE = Path(__file__).resolve().parents[1] / "code"

if str(INTEGRATION_CODE) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_CODE))
