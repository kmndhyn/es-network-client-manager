# Client Manager

Local-only WebUI. No cloud, no telemetry, no external calls.

See `HANDOFF.md` for the full feature walkthrough and cautions.

## Quick Start

### Mac
Double-click `run.command`

### Windows
Double-click `run.bat`

### Manual
```bash
cd ~/es-network
source venv/bin/activate   # or venv\Scripts\activate on Windows
uvicorn main:app --host 127.0.0.1 --port 8000
```
Then open http://127.0.0.1:8000

## How to Use

1. **Import** — click "Import" and select 1 or more Excel files (.xlsx/.xls). Columns are auto-detected, first sheet only.
2. **Filter** — use the Status and Department dropdowns (built from your data) + name search.
3. **Copy all emails** — copies the filtered rows' valid emails, one per line (placeholders like `UNKNOWN` are skipped).
4. **Add/Edit/Delete** — manual entry or edit existing rows.
5. **Sync** — re-imports the same uploaded files.
6. **Export** — downloads the current DB as Excel.
7. **Save to Excel** — writes the DB back into the workbooks in `uploads/`; this replaces the
   whole workbook, so back up the master file first (see `HANDOFF.md` §6).

## File Layout

- `main.py` — FastAPI backend
- `database.py` — SQLite schema
- `static/index.html` — Frontend
- `es_network.db` — Your local database (created on first import)
- `uploads/` — Stored Excel files for re-sync
