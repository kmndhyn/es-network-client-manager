from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import shutil
from datetime import datetime
from typing import Optional, List

from database import init_db, get_session, Client

app = FastAPI(title="ES Network Client Manager")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# No CORS needed since everything is served from same origin, but keep it simple
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB exists
init_db()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── Helpers ────────────────────────────────────────────────────────────────

COLUMN_ALIASES = {
    "name": ["name", "client name", "client", "company", "company name", "full name", "contact name"],
    "status": ["status", "active", "state", "account status", "client status"],
    "department": ["department", "dept", "division", "team", "category", "type"],
    "email": ["email", "e-mail", "email address", "mail", "contact email"],
    "phone": ["phone", "telephone", "mobile", "contact number", "tel", "phone number"],
    "notes": ["notes", "note", "remarks", "comments", "description", "memo"],
}


def resolve_column(columns: List[str], aliases: List[str]) -> Optional[str]:
    """Find the first column that fuzzy-matches any alias."""
    cols_lower = {c.strip().lower(): c for c in columns}
    for alias in aliases:
        if alias.lower() in cols_lower:
            return cols_lower[alias.lower()]
    # partial match
    for alias in aliases:
        for c_lower, c_orig in cols_lower.items():
            if alias.lower() in c_lower or c_lower in alias.lower():
                return c_orig
    return None


def normalize_dataframe(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """Map Excel columns to unified schema."""
    columns = list(df.columns)
    mapping = {}
    for field, aliases in COLUMN_ALIASES.items():
        found = resolve_column(columns, aliases)
        if found:
            mapping[found] = field

    df = df.rename(columns=mapping)
    # Keep only known columns
    keep = [f for f in COLUMN_ALIASES.keys() if f in df.columns]
    df = df[keep].copy() if keep else pd.DataFrame()

    for col in ["status", "department"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace("nan", "").str.strip()
    # Clean other string values
    for col in df.columns:
        if col not in ["status", "department"] and df[col].dtype == object:
            df[col] = df[col].astype(str).replace("nan", "").str.strip()

    df["source_file"] = filename
    return df


def sync_dataframes(files: List[tuple]) -> dict:
    """Merge multiple dataframes into one unified set, dedupe by name+department."""
    dfs = []
    for filename, df in files:
        if df.empty:
            continue
        df = normalize_dataframe(df, filename)
        dfs.append(df)

    if not dfs:
        return {"imported": 0, "message": "No valid data found."}

    merged = pd.concat(dfs, ignore_index=True)

    # Deduplicate: keep the most recently updated row per name+dept
    merged["_sort_key"] = pd.to_datetime(merged.get("updated_at", datetime.now()), errors="coerce")
    merged = merged.sort_values("_sort_key", ascending=False)
    merged = merged.drop_duplicates(subset=["name", "department"], keep="first")
    merged = merged.drop(columns=["_sort_key"], errors="ignore")

    # Upsert to DB
    session = get_session()
    imported = 0
    for _, row in merged.iterrows():
        client = (
            session.query(Client)
            .filter(Client.name == row.get("name", ""))
            .filter(Client.department == row.get("department", ""))
            .first()
        )
        if client:
            for field in ["status", "email", "phone", "notes", "source_file"]:
                val = row.get(field)
                if val:
                    setattr(client, field, val)
        else:
            client = Client(
                name=row.get("name", ""),
                status=row.get("status", ""),
                department=row.get("department", ""),
                email=row.get("email", ""),
                phone=row.get("phone", ""),
                notes=row.get("notes", ""),
                source_file=row.get("source_file", ""),
            )
            session.add(client)
        imported += 1
    session.commit()
    session.close()
    return {"imported": imported, "message": f"Synced {imported} clients."}


# ─── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")


@app.post("/api/import")
async def import_excel(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least 1 Excel file.")

    saved = []
    dfs = []
    for upload in files:
        filename = upload.filename
        dest = os.path.join(UPLOAD_DIR, filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        saved.append(dest)

        try:
            df = pd.read_excel(dest, engine="openpyxl")
            dfs.append((filename, df))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read {filename}: {e}")

    result = sync_dataframes(dfs)
    return result


@app.get("/api/clients")
async def list_clients(
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    session = get_session()
    q = session.query(Client)
    if status:
        q = q.filter(Client.status.ilike(status))
    if department:
        q = q.filter(Client.department.ilike(department))
    if search:
        q = q.filter(Client.name.ilike(f"%{search}%"))
    clients = q.order_by(Client.name).all()
    result = [
        {
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "department": c.department,
            "email": c.email,
            "phone": c.phone,
            "notes": c.notes,
            "source_file": c.source_file,
        }
        for c in clients
    ]
    session.close()
    return result


@app.get("/api/filters")
async def get_filters():
    session = get_session()
    def unique_normalized(rows):
        seen = {}
        for val, in rows:
            if not val:
                continue
            key = val.strip().lower()
            if key and key not in seen:
                seen[key] = val.strip()
        return sorted(seen.values())
    statuses = unique_normalized(session.query(Client.status).distinct().all())
    departments = unique_normalized(session.query(Client.department).distinct().all())
    session.close()
    return {"statuses": statuses, "departments": departments}


@app.post("/api/clients")
async def add_client(client: dict):
    session = get_session()
    c = Client(
        name=client.get("name", ""),
        status=client.get("status", ""),
        department=client.get("department", ""),
        email=client.get("email", ""),
        phone=client.get("phone", ""),
        notes=client.get("notes", ""),
    )
    session.add(c)
    session.flush()
    client_id = c.id
    session.commit()
    session.close()
    return {"id": client_id, "message": "Client added."}


@app.put("/api/clients/{client_id}")
async def update_client(client_id: int, client: dict):
    session = get_session()
    c = session.query(Client).filter(Client.id == client_id).first()
    if not c:
        session.close()
        raise HTTPException(status_code=404, detail="Client not found.")
    for field in ["name", "status", "department", "email", "phone", "notes"]:
        if field in client:
            setattr(c, field, client[field])
    session.commit()
    session.close()
    return {"message": "Client updated."}


@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: int):
    session = get_session()
    c = session.query(Client).filter(Client.id == client_id).first()
    if not c:
        session.close()
        raise HTTPException(status_code=404, detail="Client not found.")
    session.delete(c)
    session.commit()
    session.close()
    return {"message": "Client deleted."}


@app.post("/api/sync")
async def re_sync():
    """Re-import from stored uploads."""
    if not os.listdir(UPLOAD_DIR):
        return {"imported": 0, "message": "No stored files to sync."}
    dfs = []
    for fname in os.listdir(UPLOAD_DIR):
        fpath = os.path.join(UPLOAD_DIR, fname)
        try:
            df = pd.read_excel(fpath, engine="openpyxl")
            dfs.append((fname, df))
        except Exception:
            continue
    result = sync_dataframes(dfs)
    return result


@app.post("/api/import/reset")
async def reset_import():
    """Clear database and uploaded files. Full reset for fresh import."""
    session = get_session()
    session.query(Client).delete()
    session.commit()
    session.close()
    for fname in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, fname))
    return {"message": "Database cleared. Ready for fresh import."}


@app.get("/api/export")
async def export_excel():
    session = get_session()
    clients = session.query(Client).all()
    session.close()
    data = [
        {
            "Name": c.name,
            "Status": c.status,
            "Department": c.department,
            "Email": c.email,
            "Phone": c.phone,
            "Notes": c.notes,
        }
        for c in clients
    ]
    df = pd.DataFrame(data)
    export_path = "export.xlsx"
    df.to_excel(export_path, index=False, engine="openpyxl")
    return FileResponse(export_path, filename="es_network_clients.xlsx")


@app.post("/api/save-to-excel")
async def save_to_excel():
    """Write current database back to all stored Excel files."""
    session = get_session()
    clients = session.query(Client).all()
    session.close()
    if not clients:
        raise HTTPException(status_code=400, detail="No data to save.")

    data = [
        {
            "Name": c.name,
            "Status": c.status,
            "Department": c.department,
            "Email": c.email,
            "Phone": c.phone,
            "Notes": c.notes,
        }
        for c in clients
    ]
    df = pd.DataFrame(data)

    if not os.listdir(UPLOAD_DIR):
        # No stored files; save to a new file in uploads
        dest = os.path.join(UPLOAD_DIR, "es_network_export.xlsx")
        df.to_excel(dest, index=False, engine="openpyxl")
        return {"message": f"Saved to {dest}"}

    saved = []
    for fname in os.listdir(UPLOAD_DIR):
        fpath = os.path.join(UPLOAD_DIR, fname)
        try:
            df.to_excel(fpath, index=False, engine="openpyxl")
            saved.append(fname)
        except Exception as e:
            continue
    return {"message": f"Saved to {len(saved)} file(s): {', '.join(saved)}"}
