# Client Manager

Local web UI for keeping client and contact records in Excel. Runs on your own
machine — no cloud, no telemetry, no external calls.

## Quick Start

Double-click **`launch.command`** (Mac) or **`launch.bat`** (Windows).  
It creates a local virtual environment, installs dependencies on first run, and opens http://127.0.0.1:8000 automatically.

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

`launch.command` already does this automatically when Tailscale is installed.

```bash
tailscale serve --bg 8000
```

Then open `https://<machine>.<tailnet>.ts.net/` from any signed-in device.

- Access requires Tailscale running and signed in on both devices.
- The host must stay awake with the terminal open while serving.
- Stop publishing: `tailscale serve --https=443 off` · Check: `tailscale serve status`

## How to Use

1. **Import** — click "Import" and choose 1 or more Excel files (.xlsx/.xls). Every sheet
   is imported as its own table; pick one from the sheet dropdown above the table. The real
   header row is found automatically (title rows above it are skipped), and re-importing the
   same filename replaces all of that file's sheets.
2. **Filter** — dropdowns are built from columns with 2–15 repeated values that are mostly
   filled; numbered or blank columns are skipped. The search box matches every field.
   Press `/` to jump to search.
3. **Add/Edit/Delete** — "Add client", or the pencil/trash icons on a row.
4. **Copy emails** — copies valid addresses from the rows currently shown, one per line,
   deduplicated. Placeholders like `UNKNOWN` are skipped.
5. **Save to file** — asks which you want:
   - **Download a new sheet** — writes a fresh .xlsx from the database, one tab per imported
     sheet. Never touches your files.
   - **Overwrite the imported file** — rebuilds every imported sheet in the workbook in
     `uploads/` from the current rows. Other sheets are left alone, but formatting, formulas
     and title rows above the header are lost.
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

## Build standalone EXE (no Python needed on target machine)

GitHub holds source only — `build/`, `dist/` and your data files are never committed.
Build on a Windows machine with Python 3.11+:

1. Open the project folder in Command Prompt.
2. Double-click **`build_exe.bat`** (installs dependencies, then builds both flavours).
3. Distribute either:
   - `dist\ES Client Manager.exe` — one file, nothing else needed (slower first launch), or
   - `dist\ES Client Manager\` — folder version, faster start; zip the whole folder.

The EXE contains only code and `static/`. It never includes `uploads/`, `es_network.db`
or any workbook. Those live next to the EXE and are created on first import, so replacing
the EXE keeps the existing data.

If an old checkout still has `build.bat`, delete it — it built `main.py`, which has no
launcher and produces an EXE that opens nothing.
