# Suprajit Quality Portal (V3 Enterprise Edition) - System Internals & Engineering Reference

This document is the authoritative technical reference for developers, security auditors, and system architects. It details the system's execution pipeline, database schema, cryptographic invariants, and security boundaries.

---

## 💾 1. Database Architecture & Schema (`data/portal.db`)

The database is powered by **SQLite 3** operating in **WAL (Write-Ahead Logging)** mode with `SYNCHRONOUS=NORMAL` and `BUSY_TIMEOUT=5000ms`.

### Complete Table Schema:

```sql
-- Multi-Tenant Customer Organizations
CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    portal_suspended INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Company Email Domain Whitelists (Self-Serve Auto-Join)
CREATE TABLE customer_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    domain_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Accounts & 3-Tier RBAC
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT,
    display_name TEXT,
    role TEXT NOT NULL CHECK(role IN ('admin', 'company_admin', 'customer_viewer')),
    access_mode TEXT DEFAULT 'ALL' CHECK(access_mode IN ('ALL', 'CUSTOM')),
    is_active INTEGER DEFAULT 1,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Granular User Recipe Assignments (When access_mode='CUSTOM')
CREATE TABLE user_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipe_name TEXT NOT NULL,
    UNIQUE(user_id, recipe_name)
);

-- Organization-Wide Recipe Assignments
CREATE TABLE customer_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    recipe_name TEXT NOT NULL,
    UNIQUE(customer_id, recipe_name)
);

-- Ingestion Batch Execution Run Tracking
CREATE TABLE batch_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    files_discovered INTEGER DEFAULT 0,
    files_indexed INTEGER DEFAULT 0,
    files_skipped INTEGER DEFAULT 0,
    duration_seconds REAL DEFAULT 0,
    log_output TEXT
);

-- Indexed Quality Reports
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_run_id INTEGER REFERENCES batch_runs(id),
    recipe_name TEXT NOT NULL,
    report_date TEXT NOT NULL,
    report_time TEXT,
    serial_normalized TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full-Text Search (FTS5) Virtual Table
CREATE VIRTUAL TABLE reports_fts USING fts5(
    recipe_name,
    report_date,
    serial_normalized,
    original_filename,
    content='reports',
    content_rowid='id'
);

-- Forensic Audit Trail & Telemetry
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    customer_id TEXT,
    action TEXT NOT NULL, -- 'login', 'search', 'download', 'view_online', etc.
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Key-Value Configuration & Reversible AES-256 Secrets
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔒 2. Cryptographic Security & Invariants

1. **Password Storage**: Passwords are mathematically hashed using **Werkzeug's `scrypt`** with automatic salt generation. Plaintext passwords never touch logs or disk.
2. **Reversible Secret Encryption (AES-256 Fernet)**: Sensitive configurations stored in `system_settings` (e.g. SMTP passwords, OAuth 2.0 Client Secrets) are encrypted at rest using `cryptography.fernet.Fernet` derived from the server's master `SECRET_KEY`.
3. **File Deduplication (SHA-256)**: Every indexed file is hashed in 64KB blocks. Identical files placed in multiple subdirectories are indexed once, preserving database integrity.
4. **Path Traversal Shield**: All file download and raw streaming endpoints validate paths against `app.helpers.is_safe_path()`, strictly enforcing realpath containment inside the configured root directory.

---

## 🚀 3. Core Subsystems & Execution Lifecycles

### A. Dynamic Filename Parser (`app/parser.py`)
- Reads the dynamic regex stored in `system_settings` under `custom_filename_regex`.
- Matches named capture groups (`recipe`, `year`, `month`, `day`, `hour`, `minute`, `second`, `serial`).
- Cleans Windows copy suffixes (e.g. ` (1).xlsx`, ` - Copy.xlsx`).
- Falls back to built-in manufacturing ISO regex if the custom pattern fails or is unset.

### B. In-Browser Spreadsheet Streamer (`app/routes/portal.py` & SheetJS)
- **Endpoint**: `/view-raw/<int:report_id>`
- **Workflow**:
  1. Validates user authentication and tenancy authorization via `customer_scope()`.
  2. Blocks path traversal.
  3. Returns raw binary stream with header `Content-Disposition: inline`.
  4. Client-side JS fetches the `ArrayBuffer`, parses the workbook using `XLSX.read(data, {type: 'array'})`, and renders interactive HTML tables.
  5. Inserts an immutable `view_online` record into `audit_logs`.

### C. Native Cloudflare Tunnel Runner (`app/tunnel.py`)
- Manages an isolated background subprocess for `cloudflared.exe`.
- Dynamically parses the generated `https://*.trycloudflare.com` tunnel URL from process stderr.
- Updates `system_settings.public_base_url` to guarantee outbound email links always point to the active public endpoint.

---

## 🧪 4. Three-Way Test Defense Matrix

The test framework (`pytest`) verifies all 107 critical paths:
1. `tests/test_v3_company_rbac.py` &rarr; 62 Tests (3-Tier RBAC, Dynamic Regex, SSO Client Registration, Tunnel Runner, Bulk Onboarding).
2. `tests/test_exhaustive.py` & `tests/test_exhaustive2.py` &rarr; 26 Tests (Full route surface, search lifecycle, SheetJS raw streams, Admin CRUD).
3. `tests/test_security_asvs.py` &rarr; 4 Tests (OWASP ASVS 2025 multi-tenant isolation, SQL injection immunization, path traversal blocks).
4. `tests/test_sync_engine_dimensions.py` & `tests/test_suite.py` &rarr; 15 Tests (Batch engine N-1 safety, deduplication, FTS5 sync).


## 4. How Everything Talks To Each Other

1. **The Scheduler** wakes up and talks to the **Sync Engine**.
2. The **Sync Engine** talks to the **Windows File System** (to find Excel files) and to the **Parser** (to extract text). 
3. The **Sync Engine** then talks to the **Database** (SQLite), injecting thousands of rows in bulk using memory transactions.
4. An **External Customer** connects via browser. The network talks to **Waitress** (the web server). Waitress talks to **Flask** (`portal.py`). 
5. Flask talks to the **Database**, retrieves the results, and renders them via **Jinja2 HTML Templates** back to the customer. 
