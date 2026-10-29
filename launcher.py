#!/usr/bin/env python3
"""ES Network Client Manager - Launcher

Starts the FastAPI server in-process and shows the UI in a native desktop
window (Edge WebView2). Falls back to the default browser if WebView2 is not
available.
"""
import os
import socket
import sys
import time
import traceback
import urllib.request
import webbrowser
import threading

import paths

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
APP_TITLE = "ES Network Client Manager"


def find_free_port(host: str, start: int = DEFAULT_PORT) -> int:
    """Return the first free port at or after `start`."""
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found between {start} and {start + 19}.")


def wait_until_ready(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=0.5).close()
            return True
        except Exception:
            time.sleep(0.15)
    return False


def start_server(app, port: int):
    import uvicorn

    config = uvicorn.Config(
        app, host=HOST, port=port, log_level="warning", access_log=False
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="es-server", daemon=True)
    thread.start()
    return server, thread


def run_desktop_window(url: str) -> None:
    import webview

    # Exports use a download link; pywebview cancels downloads unless enabled.
    webview.settings["ALLOW_DOWNLOADS"] = True

    storage = paths.DATA_DIR / ".webview"
    storage.mkdir(exist_ok=True)
    window = webview.create_window(
        APP_TITLE,
        url,
        width=1280,
        height=840,
        min_size=(960, 600),
        background_color="#0f1115",
    )
    # Blocks on the main thread until the window is closed.
    webview.start(
        gui="edgechromium",
        debug=False,
        private_mode=False,
        storage_path=str(storage),
    )
    del window


def _show_error(message: str) -> None:
    """Windowed builds have no console, so surface fatal errors in a dialog."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, APP_TITLE, 0x10)
    except Exception:
        pass


def _redirect_stdio() -> None:
    """A windowed build has sys.stdout/stderr = None, which breaks uvicorn's
    logging setup (it calls .isatty()). Point them at a log file instead."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        log = open(paths.DATA_DIR / "server.log", "a", encoding="utf-8", buffering=1)
    except Exception:
        return
    if sys.stdout is None:
        sys.stdout = log
    if sys.stderr is None:
        sys.stderr = log


def main() -> None:
    _redirect_stdio()
    os.chdir(paths.DATA_DIR)
    paths.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Import the app directly (not as "main:app") so the bundled build
    # includes every FastAPI/uvicorn submodule the app needs.
    from main import app

    port = find_free_port(HOST)
    url = f"http://{HOST}:{port}"
    server, server_thread = start_server(app, port)
    if not wait_until_ready(url):
        raise RuntimeError("The local server did not start in time. See server.log.")

    force_browser = os.environ.get("ES_OPEN_BROWSER") == "1" or "--browser" in sys.argv
    try:
        if force_browser:
            raise RuntimeError("Browser mode requested.")
        run_desktop_window(url)
    except Exception:
        if not force_browser:
            traceback.print_exc()
        webbrowser.open(url)
        # No app window owns the process in browser mode; keep serving.
        server_thread.join()
        return
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_path = paths.DATA_DIR / "startup-error.log"
        try:
            log_path.write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            log_path = None
        message = traceback.format_exc()
        if log_path is not None:
            message += f"\n\nSaved to:\n{log_path}"
        _show_error(message)
        raise
