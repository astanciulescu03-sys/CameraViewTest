import sys
from pathlib import Path


def resource_path(relative_path):
    """Resolves a bundled resource path both when running from source and
    when frozen into a single-file executable by PyInstaller (sys._MEIPASS)."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return str(base / relative_path)
