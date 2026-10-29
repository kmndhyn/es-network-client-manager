"""Where the app finds bundled assets and writes user data.

Running from source:
    assets and data both live in this file's folder.

Frozen with PyInstaller (one-folder or one-file):
    bundled read-only assets (static/) live in sys._MEIPASS
    writable data (database, uploads, exports) lives next to the .exe
"""
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)

if FROZEN:
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    DATA_DIR = Path(sys.executable).parent
else:
    RESOURCE_DIR = Path(__file__).resolve().parent
    DATA_DIR = RESOURCE_DIR

STATIC_DIR = RESOURCE_DIR / "static"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "es_network.db"
