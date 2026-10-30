from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os
import json
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any

from database import init_db, get_session, ImportMeta, ClientRow
from paths import STATIC_DIR, UPLOAD_DIR, DATA_DIR

app = FastAPI(title="ES Network Client Manager")

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

init_db()

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── Helpers ────────────────────────────────────────────────────────────────

NULLISH = {
    "", "nan", "none", "null", "nil", "n/a", "na", "-", "--", "---",
    "unknown", "unnamed", "undefined", "missing", "#n/a", "#na", "#null",
    "#ref!", "#value!", "#div/0!", "#name?", "no data", "not available",
    "—", "–", "•", "·",
}

def _clean_value(val):
    """Normalize pandas/numpy values and common null-placeholder strings to empty string."""
    if pd.isna(val):
        return ""
    if hasattr(val, "item"):
        val = val.item()
    if isinstance(val, str):
        stripped = val.strip()
        if stripped.lower() in NULLISH:
            return ""
        return stripped
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.isoformat()
    return str(val)

# Backward-compat alias
make_json_safe = _clean_value


def _looks_like_header(row_values) -> bool:
    """Heuristic: does this row look like column headers rather than data?"""
    non_null = [str(v).strip() for v in row_values if pd.notna(v) and str(v).strip()]
    if not non_null:
        return False
    data_like = 0
    for v in non_null:
        v_lower = v.lower()
        # Emails, URLs, long text, pure numbers, dates → data
        if (
            "@" in v
            or "http" in v_lower
            or len(v) > 40
            or v.replace(",", "").replace(".", "").replace("-", "").replace("/", "").isdigit()
        ):
            data_like += 1
    # If >30% look like actual data, treat as data row, not header
    return (data_like / len(non_null)) < 0.3


def import_excel_file(filepath: str, filename: str) -> Dict[str, Any]:
    """Read an Excel file and return columns + rows, auto-detecting headers."""
    # Read raw to inspect first row
    df_raw = pd.read_excel(filepath, engine="openpyxl", header=None)

    if len(df_raw) == 0:
        return {"source_file": filename, "columns": [], "rows": [], "count": 0}

    if _looks_like_header(df_raw.iloc[0]):
        df = pd.read_excel(filepath, engine="openpyxl")
        columns = [str(c).strip() for c in df.columns]
        # Clean pandas-generated "Unnamed: X" names
        columns = [
            c if not c.lower().startswith("unnamed:") else f"Column {i + 1}"
            for i, c in enumerate(columns)
        ]
        df.columns = columns
    else:
        df = df_raw
        columns = [f"Column {i + 1}" for i in range(len(df.columns))]
        df.columns = columns

    rows = []
    for idx, row in df.iterrows():
        row_data = {col: _clean_value(row[col]) for col in columns}
        rows.append({
            "row_index": int(idx),
            "data": row_data,
        })

    return {
        "source_file": filename,
        "columns": columns,
        "rows": rows,
        "count": len(rows),
    }


# ─── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/import")
async def import_excel(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least 1 Excel file.")

    session = get_session()
    imported_total = 0
    meta_created = []

    for upload in files:
        # Untrusted client filename: keep it inside uploads/
        filename = os.path.basename(upload.filename or "uploaded_file")
        dest = os.path.join(UPLOAD_DIR, filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(upload.file, f)

        try:
            parsed = import_excel_file(dest, filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read {filename}: {e}")

        # Store/update import metadata
        meta = session.query(ImportMeta).filter(ImportMeta.source_file == filename).first()
        if meta:
            meta.columns = json.dumps(parsed["columns"])
        else:
            meta = ImportMeta(
                source_file=filename,
                columns=json.dumps(parsed["columns"]),
            )
            session.add(meta)
        meta_created.append(meta)

        # Remove old rows for this file before re-importing
        session.query(ClientRow).filter(ClientRow.source_file == filename).delete()

        # Insert rows
        for row in parsed["rows"]:
            client_row = ClientRow(
                source_file=filename,
                row_index=row["row_index"],
                data=json.dumps(row["data"]),
            )
            session.add(client_row)
            imported_total += 1

    session.commit()
    session.close()
    return {"imported": imported_total, "message": f"Synced {imported_total} rows."}


@app.get("/api/clients")
async def list_clients(
    request: Request,
    search: Optional[str] = Query(None),
    source_file: Optional[str] = Query(None),
):
    session = get_session()
    q = session.query(ClientRow)
    if source_file:
        q = q.filter(ClientRow.source_file == source_file)
    rows = q.order_by(ClientRow.row_index).all()

    # Every other query param is a column filter from the UI's filter bar.
    filters = {k: v for k, v in request.query_params.items() if k not in ("search", "source_file")}

    results = []
    for row in rows:
        item = row_to_dict(row)
        if search:
            # Search across all data values
            haystack = " ".join(str(v) for v in item["data"].values()).lower()
            if search.lower() not in haystack:
                continue
        if any(str(item["data"].get(k, "")) != v for k, v in filters.items()):
            continue
        results.append(item)

    session.close()
    return results


@app.get("/api/columns")
async def get_columns(source_file: Optional[str] = Query(None)):
    """Return column definitions for the UI."""
    session = get_session()
    if source_file:
        meta = session.query(ImportMeta).filter(ImportMeta.source_file == source_file).first()
        if meta:
            columns = json.loads(meta.columns)
            session.close()
            return {"columns": columns, "source_file": source_file}
    # Return all unique columns across all imports
    metas = session.query(ImportMeta).all()
    sources = [m.source_file for m in metas]
    all_cols = []
    seen = set()
    for m in metas:
        cols = json.loads(m.columns)
        for c in cols:
            if c not in seen:
                all_cols.append(c)
                seen.add(c)
    session.close()
    return {"columns": all_cols, "source_file": source_file, "sources": sources}


@app.get("/api/filters")
async def get_filters(source_file: Optional[str] = Query(None), column: Optional[str] = Query(None)):
    """Return unique values for a column, or all filterable columns."""
    session = get_session()
    q = session.query(ClientRow)
    if source_file:
        q = q.filter(ClientRow.source_file == source_file)
    rows = q.all()

    if column:
        values = sorted({(json.loads(r.data) or {}).get(column, "") for r in rows if r.data})
        values = [v for v in values if v]
        session.close()
        return {"column": column, "values": values}

    # Auto-detect filterable columns: text columns with <= 15 unique values
    all_data = [json.loads(r.data) or {} for r in rows]
    session.close()

    filterable = {}
    if all_data:
        all_keys = sorted({k for d in all_data for k in d.keys()})
        for key in all_keys:
            vals = {str(d.get(key, "")).strip() for d in all_data}
            vals = {v for v in vals if v}
            if len(vals) <= 15:
                filterable[key] = sorted(vals)

    return {"filterable": filterable}


@app.post("/api/clients")
async def add_client(row: Dict[str, Any]):
    session = get_session()
    # Determine source_file from existing metas, or first available
    meta = session.query(ImportMeta).first()
    source_file = row.get("source_file", meta.source_file if meta else "manual")
    
    data = {k: v for k, v in row.items() if k not in ("source_file",)}
    client_row = ClientRow(
        source_file=source_file,
        row_index=-1,  # manually added
        data=json.dumps(data),
    )
    session.add(client_row)
    session.flush()
    client_id = client_row.id
    session.commit()
    session.close()
    return {"id": client_id, "message": "Client added."}


@app.put("/api/clients/{client_id}")
async def update_client(client_id: int, row: Dict[str, Any]):
    session = get_session()
    c = session.query(ClientRow).filter(ClientRow.id == client_id).first()
    if not c:
        session.close()
        raise HTTPException(status_code=404, detail="Client not found.")
    
    current_data = json.loads(c.data) if c.data else {}
    for key, value in row.items():
        if key not in ("source_file", "id"):
            current_data[key] = value
    c.data = json.dumps(current_data)
    session.commit()
    session.close()
    return {"message": "Client updated."}


@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: int):
    session = get_session()
    c = session.query(ClientRow).filter(ClientRow.id == client_id).first()
    if not c:
        session.close()
        raise HTTPException(status_code=404, detail="Client not found.")
    session.delete(c)
    session.commit()
    session.close()
    return {"message": "Client deleted."}


@app.post("/api/import/reset")
async def reset_import():
    """Clear database and uploaded files. Full reset for a fresh import."""
    session = get_session()
    session.query(ClientRow).delete()
    session.query(ImportMeta).delete()
    session.commit()
    session.close()
    for fname in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, fname))
    return {"message": "Database cleared. Ready for a fresh import."}


@app.post("/api/save-to-excel")
async def save_to_excel():
    """Write current database back to the stored Excel files, preserving original structure."""
    session = get_session()
    all_rows = session.query(ClientRow).all()
    session.close()

    if not all_rows:
        raise HTTPException(status_code=400, detail="No data to save.")

    # Group rows by source_file
    by_file: Dict[str, List[ClientRow]] = {}
    for row in all_rows:
        by_file.setdefault(row.source_file, []).append(row)

    saved = []
    for fname, rows in by_file.items():
        fpath = os.path.join(UPLOAD_DIR, fname)
        if not os.path.exists(fpath):
            continue

        try:
            # Read original Excel to preserve structure
            df = pd.read_excel(fpath, engine="openpyxl")
            columns = [str(c).strip() for c in df.columns]

            # Build new data for this file
            # Separate imported rows (row_index >= 0) from manual rows (row_index = -1)
            imported_rows = [r for r in rows if r.row_index is not None and r.row_index >= 0]
            manual_rows = [r for r in rows if r.row_index is None or r.row_index < 0]

            # Sort imported rows by original index
            imported_rows.sort(key=lambda r: r.row_index)

            # Create DataFrame preserving original columns
            data_dict: Dict[str, List[Any]] = {col: [] for col in columns}

            # Rebuild imported rows in original order
            for orig_row in imported_rows:
                row_data = json.loads(orig_row.data) if orig_row.data else {}
                for col in columns:
                    val = row_data.get(col, "")
                    data_dict[col].append(val)

            # Append manual rows
            for mrow in manual_rows:
                row_data = json.loads(mrow.data) if mrow.data else {}
                for col in columns:
                    val = row_data.get(col, "")
                    data_dict[col].append(val)

            new_df = pd.DataFrame(data_dict)
            new_df.to_excel(fpath, index=False, engine="openpyxl")
            saved.append(fname)
        except Exception:
            continue

    if saved:
        return {"message": f"Saved to {len(saved)} file(s): {', '.join(saved)}"}
    else:
        return {"message": "No files saved. Make sure files are still in uploads."}


@app.get("/api/export")
async def export_excel():
    """Download current database as a fresh Excel file."""
    session = get_session()
    rows = session.query(ClientRow).all()
    session.close()

    if not rows:
        raise HTTPException(status_code=400, detail="No data to export.")

    # Get all unique columns across all rows
    all_data = [json.loads(r.data) or {} for r in rows]
    all_keys = sorted({k for d in all_data for k in d.keys()})

    data = []
    for r in rows:
        row_data = json.loads(r.data) or {}
        data.append({k: row_data.get(k, "") for k in all_keys})

    df = pd.DataFrame(data)
    export_path = DATA_DIR / "export.xlsx"
    df.to_excel(export_path, index=False, engine="openpyxl")
    return FileResponse(str(export_path), filename="es_network_export.xlsx")
