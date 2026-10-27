# Client Manager — Handoff Notes

A local-only WebUI for maintaining the client contact list that lives in the ES Network
Excel workbook (`uploads/test_database.xlsx`, sheet **Email List**).

It is **a convenience layer over the Excel sheet**, not a replacement system:

- The Excel file stays the master artifact. The app imports it, lets you fix/filter/copy
  data quickly, then writes it back (Export / Save to Excel).
- The server runs on `127.0.0.1:8000` only: no cloud, no telemetry, no outbound requests.
- The project **and its database live on the Hermes share**, not on the admin's local disk.

## Project locations

| | |
|---|---|
| Project folder | `\\100.81.47.120\Shared Hermes Agent Database\xiv-PC\es-network` (mapped as `Y:\xiv-PC\es-network`, on the xivi-RPi NAS) |
| Source code | https://github.com/kmndhyn/es-network-client-manager (private) |
| Client data | `es_network.db` + `uploads\` inside that folder — **not** in GitHub |

---

## 1. How to start / stop

Run these from the project folder on the share (`Y:\xiv-PC\es-network`):

| | |
|---|---|
| Windows | Double-click `run.bat` (opens the browser at http://127.0.0.1:8000) |
| Mac | Double-click `run.command` |
| Manual | `venv\Scripts\activate` → `uvicorn main:app --host 127.0.0.1 --port 8000` |
| Stop | Close the terminal window / `Ctrl+C` |

First start after a boot (or after the share was idle) can take **30–60 seconds** while Python
loads from the NAS — the page stays unreachable until the console prints
`Uvicorn running on http://127.0.0.1:8000`. That is normal, don't restart it.

The UI is only reachable from that machine, but the folder itself sits on a shared NAS volume,
so treat the files there as visible to anyone with access to the Hermes share.

---

## 2. Where the data lives

| Path | What it is |
|---|---|
| `es_network.db` | SQLite database. This is what the screen reads and writes. |
| `uploads/` | Copies of every imported workbook. This is the source used by **Sync**. |
| `static/index.html` | The whole front end (HTML + CSS + JS in one file). |
| `main.py` / `database.py` | API and table schema. |

Deleting `es_network.db` or pressing **Reset** wipes all records. The database is a SQLite file
on an SMB share: it is fine for one admin at a time, but do not run the app from two machines
against the same folder, and prefer **Export** over long editing sessions if the NAS connection
is flaky. Back up the folder before any demo or handover.

---

## 3. Screen walkthrough

### Header
- `Client Manager` — the page name.
- Theme switch (sun / crescent): light or dark UI. The choice is remembered per browser and
  is purely cosmetic — it does not touch data.

### Toolbar (filters + actions)
| Control | What it does |
|---|---|
| **All Statuses** dropdown | Filter by status. Options are read from the data (`Subscribed`, `Unsubscribed`, `Bounced`, `UNKNOWN`). |
| **All Departments** dropdown | Filter by "department" (in this workbook it maps to the Excel **Email Type** column: `Primary`, `Technical`, `Billing`, `Marketing`). |
| **Search name…** | Substring match on the **Name** column only (not email/notes). |
| **Apply** | Re-runs the query with the current filters. |
| **📋 Copy all emails** | Copies the emails of the **currently filtered** rows, one per line (see §4). |
| **+ Add Client** | Opens a blank form to create a record manually. |
| **Import** | Opens the file picker; accepts one or many `.xlsx` / `.xls` files. |
| **Sync** | Re-reads every workbook stored in `uploads/` and re-applies it (no file picker). |
| **Save to Excel** | Writes the current database back into the workbooks in `uploads/`. **Read §6 before using.** |
| **Export** | Downloads the whole database as `es_network_clients.xlsx` (safe, read-only). |
| **Reset** | Deletes **all** clients and **all** stored workbooks after a confirmation. Irreversible. |

Below the toolbar: the copy-result line (e.g. `✅ Copied 155 emails · 3 skipped — no valid email`)
and `Last sync: …`.

### Table
Columns: **Name, Status, Department, Email, Phone, Notes, Actions**.

- **Name** is the *company / client name* from Excel, not the contact person.
- **Email** shows the raw value. Values that are not real addresses (`UNKNOWN`, `-`, `N/A`…)
  are displayed muted + italic with a dotted underline and a tooltip: they are visible for
  reference but never copied.
- **Edit** opens the same form pre-filled; **Del** asks for confirmation, then removes the row.
- Empty optional fields display `—`.

### Add / Edit form
Fields: Name (required), Status, Department, Email, Phone, Notes.
Saving writes to the local database immediately. It does **not** touch the Excel file until
you use **Export** or **Save to Excel**.

---

## 4. Email copying rules (the part that matters most day to day)

`Copy all emails` respects whatever filters are active, then:

1. Drops blanks.
2. Drops placeholders: `UNKNOWN`, `NONE`, `NULL`, `NIL`, `N/A`, `NA`, `N.A.`, `not available`,
   `not provided`, `no email`, `no e-mail`, `missing`, `TBD`, `pending`, `-`, `--`, `—`, `?`,
   plus anything starting with "unknown…", "not available…", "no email…", etc.
3. Drops anything not shaped like `name@domain.tld` (so `john@company` is rejected too).
4. Removes case-insensitive duplicates.
5. Copies the rest as newline-separated plain text, ready to paste into an email client's BCC.

If nothing valid survives, it says so instead of copying an empty clipboard.

Current state of the imported sheet: **158 rows → 155 usable emails, 3 rows have `UNKNOWN`**
(Ginhawa Resort Co., Kabayan Engineering Works Enterprises, Buwan Accounting Services Corp.).

---

## 5. How Excel is imported

- Only the **first sheet** of each workbook is read — for this workbook: **Email List**.
  (The other tabs — Workflow, FlowChart, Ref>, Client Contract Details, Contracts Masterlist —
  are neither read nor touched by Import.)
- Columns are matched by name (fuzzy), so the mapping for this workbook is:

| Excel column | App field |
|---|---|
| `Client Name` | Name |
| `Subscription Status` | Status |
| `Email Type` | Department |
| `Email Address` | Email |
| *(no matching column)* | Phone, Notes → stay blank |

- **Not imported at all:** `Email ID`, `Client ID`, `Contact Person`, `Last Emailed`,
  `Email Format Check`, `UNKNOWN Fields (#)`. The contact person is therefore not visible in
  the app — the list is company-level.
- Additional unknown columns are discarded on import.
- Rows are merged on **Name + Department**, so the same company with two email types is two
  records, and two rows with an identical Name + Department collapse into one.
- Re-importing an existing record only fills fields that are **non-empty** in the file —
  blanking a cell in Excel will not blank it in the app. Edit it in the form (or Reset).

---

## 6. ⚠️ Cautions before handoff

1. **"Save to Excel" overwrites the uploaded workbook as a single flat sheet.**
   It writes a brand-new workbook containing only Name / Status / Department / Email / Phone /
   Notes. The five other tabs (`Workflow`, `FlowChart`, `Ref>`, `Client Contract Details`,
   `Contracts Masterlist`) and the extra columns (`Email ID`, `Client ID`, `Contact Person`,
   `Last Emailed`, `Email Format Check`, `UNKNOWN Fields (#)`) are **lost** in that file.
   → Until this is changed, prefer **Export** (writes a separate download) and keep the
   original workbook untouched. Always work on a copy.
2. **Reset is total**: it clears the database *and* deletes everything in `uploads/`.
3. **Deleting a row in Excel does not delete it in the app.** Records only disappear via
   **Del** in the UI or **Reset**.
4. **Sync** is only as good as `uploads/`: if a workbook is removed from that folder, Sync can
   no longer restore its rows.
5. **No login.** The app trusts anyone who can reach `127.0.0.1:8000` on that machine.
6. Known UI limitation: the **Edit** button breaks for rows whose Name/Notes contain an
   apostrophe (`'`), because values are passed inline in the button markup.
7. The import dialog says "Select sheet to import", but sheet selection is not implemented —
   it always takes the first sheet.

---

## 7. Suggested demo flow (5 minutes)

1. Start with `run.bat`, show http://127.0.0.1:8000.
2. Filter by Status = `Subscribed`, then Department = `Primary` — point out the dropdowns
   are built from the data itself.
3. Clear filters, type part of a company name, **Apply**.
4. Press **📋 Copy all emails** → paste into a scratch email's BCC → show that `UNKNOWN`
   rows were skipped and reported.
5. **Edit** one client, change a phone number or fix an `UNKNOWN` email, **Save**.
6. **Export** to show the updated sheet downloads without touching the master file.
7. Mention the theme switch and that everything is local.
8. Explain the "Save to Excel" caution (item 1 above) so nobody overwrites the master workbook.

---

## 8. Technical summary

- FastAPI + SQLAlchemy + SQLite backend, single static HTML page front end, `openpyxl`/`pandas`
  for Excel.
- Endpoints: `GET /`, `GET/POST /api/clients`, `PUT/DELETE /api/clients/{id}`,
  `GET /api/filters`, `POST /api/import`, `POST /api/sync`, `POST /api/import/reset`,
  `GET /api/export`, `POST /api/save-to-excel`.
- Binds `127.0.0.1:8000` only. Suitable for hundreds of rows; not built for multi-user or
  concurrent editing.
