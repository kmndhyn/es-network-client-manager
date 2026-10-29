#!/usr/bin/env python3
"""ES Network Client Manager - Launcher

Starts the FastAPI server and opens the browser automatically.
"""
import os
import sys
import time
import webbrowser
import threading
import subprocess
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def open_browser():
    time.sleep(1.5)
    webbrowser.open(URL)


def main():
    # Ensure we're in the right directory
    base_dir = Path(__file__).parent if getattr(sys, 'frozen', False) else Path.cwd()
    os.chdir(base_dir)

    # Ensure required directories exist
    (base_dir / "uploads").mkdir(exist_ok=True)
    (base_dir / "static").mkdir(exist_ok=True)

    # Start browser in background
    threading.Thread(target=open_browser, daemon=True).start()

    # Start uvicorn
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
