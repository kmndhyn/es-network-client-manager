# Client Manager

Local WebUI served over your Tailscale tailnet. No cloud, no telemetry, no external calls.

## Quick Start

### Mac
Double-click `run.command`

On the Mac the app is published on the tailnet (Tailscale Serve) rather than localhost:

    https://kims-macbook-pro.tail9a2e96.ts.net/

Open that URL from any device signed in to the same tailnet (your PC, phone, etc.).
The server still binds `127.0.0.1` only; Tailscale provides the HTTPS entry point, so
nothing is exposed on the local LAN or the public internet.

### Windows
Double-click `run.bat`

### Manual
```bash
cd ~/es-network
source venv/bin/activate   # or venv\Scripts\activate on Windows
tailscale serve --bg 8000  # Mac only
uvicorn main:app --host 127.0.0.1 --port 8000
```

## Tailnet Notes

- Access requires Tailscale running and signed in on both devices.
- The Mac must stay awake with the terminal open while serving.
- Stop publishing: `tailscale serve --https=443 off` · Check: `tailscale serve status`


## How to Use

1. **Import** — click "Import" and select 1 or more Excel files (.xlsx/.xls). Columns are auto-detected, first sheet only.
2. **Filter** — use the Status and Department dropdowns (built from your data) + name search.
3. **Copy all emails** — copies the filtered rows' valid emails, one per line (placeholders like `UNKNOWN` are skipped).
4. **Add/Edit/Delete** — manual entry or edit existing rows.
5. **Sync** — re-imports the same uploaded files.
6. **Export** — downloads the current DB as Excel.
7. **Save to Excel** — writes the DB back into the workbooks in `uploads/`; this replaces the
   whole workbook (only these six columns survive), so back up the master file first.

## File Layout

- `main.py` — FastAPI backend
- `database.py` — SQLite schema
- `static/index.html` — Frontend
- `es_network.db` — Your local database (created on first import)
- `uploads/` — Stored Excel files for re-sync
