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
- `static/index.html` — Frontend
- `launcher.py` — Server launcher (opens browser automatically)
- `es_network.db` — Your local database (created on first import)
- `uploads/` — Stored Excel files for import/save

## Build Windows EXE (no Python needed on target machines)

On a Windows PC with Python installed:

1. Open Command Prompt in this folder
2. Run `build_exe.bat`
3. When finished, zip the `dist\ES Client Manager` folder
4. Distribute that zip — users just extract and double-click `ES Client Manager.exe`

The EXE includes everything needed: server, frontend, and browser launcher.
