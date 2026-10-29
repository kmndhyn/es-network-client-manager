# Client Manager

Local web UI for keeping client and contact records in Excel. Runs on your own
machine — no cloud, no telemetry, no external calls.

## Quick Start

### Mac
Double-click `run.command`, then open http://127.0.0.1:8000

### Windows
Double-click `run.bat`, then open http://127.0.0.1:8000

### Manual
```bash
cd ~/es-network
source venv/bin/activate   # or venv\Scripts\activate on Windows
uvicorn main:app --host 127.0.0.1 --port 8000
```

## Optional: use it from another device

The server binds `127.0.0.1` only, so nothing is exposed on your LAN or the
public internet. To reach it from your phone or another computer, publish it on
your Tailscale tailnet:

```bash
tailscale serve --bg 8000     # Mac; run.command does this automatically when installed
```

Then open `https://<machine>.<tailnet>.ts.net/` from any signed-in device.

- Access requires Tailscale running and signed in on both devices.
- The host must stay awake with the terminal open while serving.
- Stop publishing: `tailscale serve --https=443 off` · Check: `tailscale serve status`

## How to Use

1. **Import** — click "Import" and choose 1 or more Excel files (.xlsx/.xls). First sheet only,
   columns auto-detected. Re-importing the same filename replaces that file's rows.
2. **Filter** — dropdowns are built from any column with 15 or fewer distinct values, plus the
   search box which matches every field. Press `/` to jump to search.
3. **Add/Edit/Delete** — "Add client", or the pencil/trash icons on a row.
4. **Copy emails** — copies valid addresses from the rows currently shown, one per line,
   deduplicated. Placeholders like `UNKNOWN` are skipped.
5. **Save to file** — asks which you want:
   - **Download a new sheet** — writes a fresh .xlsx from the database, never touches your files.
   - **Overwrite the imported file** — replaces the workbook in `uploads/` with the current rows.
6. **Export** — downloads the current database as Excel (same as "Download a new sheet").
7. **Reset** — wipes the database and the files in `uploads/`.
8. **Dark mode** — toggle in the top-right; the choice is remembered.

## File Layout

- `main.py` — FastAPI backend
- `database.py` — SQLite schema
- `paths.py` — asset/data locations (source vs. frozen build)
- `static/index.html` — Frontend
- `launcher.py` — Server launcher (opens browser automatically)
- `es_network.db` — Your local database (created on first import)
- `uploads/` — Stored Excel files for import/save

## Build Windows EXE (no Python needed on target machines)

On a Windows PC with Python **3.11+** installed:

1. Open Command Prompt in this folder
2. Run `build_exe.bat`
3. Outputs land in `dist\`:
   - `ES Client Manager.exe` — single self-contained file (easiest to share)
   - `ES Client Manager\` — folder build with faster startup (zip the whole folder if you prefer this one)
4. Copy either build to the work laptops — no Python or packages required

The app opens in its own desktop window (Edge WebView2, present on Windows 10/11
with Edge). It does not open a browser tab. If WebView2 is unavailable it falls
back to the default browser automatically.

Notes:

- `es_network.db`, `uploads\`, `export.xlsx` and `server.log` are created **next to
  the .exe**, so put the exe in a folder the user can write to (e.g. Documents,
  not `C:\Program Files`).
- Windows SmartScreen may warn about an unsigned app: **More info → Run anyway**.
- If it ever fails to start, `startup-error.log` and `server.log` sit next to the
  exe and contain the reason.
- Excel exports are downloaded via the WebView2 download prompt (usually to
  `Downloads`).
