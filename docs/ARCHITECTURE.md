# System Architecture

This document describes the design, execution lifecycles, and architectural decisions governing the Suprajit Quality Portal.

---

## 1. High-Level Design & Component Overview

The application is structured into four primary layers:

1. **Presentation Layer (Web UI)**:
   - Built with Flask and Jinja2 server-rendered templates.
   - Client-side spreadsheet rendering via SheetJS (`xlsx.full.min.js`), allowing in-browser parsing of `.xlsx` and `.csv` files inside an interactive viewer without server-side compute overhead.
   - Interactive components styled with Tailwind CSS / DaisyUI with zero full-page single-page application (SPA) build toolchain requirements.
2. **Routing & Authorization Layer**:
   - Four distinct Flask blueprints: `auth`, `portal`, `company`, and `admin`.
   - 3-tier Role-Based Access Control (`admin`, `company_admin`, `customer_viewer`).
   - Session authentication managed via `Flask-Login` with rate limiting enforced by `Flask-Limiter`.
3. **Storage & Search Engine**:
   - Single-file SQLite database running in Write-Ahead Logging (`WAL`) mode with `NORMAL` synchronicity and 5-second busy timeout.
   - Trigram-tokenized Full-Text Search via SQLite `FTS5` virtual table (`reports_fts`) kept in sync with automatic database triggers.
   - Explicit versioned migrations tracked via SQLite `PRAGMA user_version`.
4. **Ingestion & Process Management**:
   - `SyncEngine`: Ingests files matching configurable regular expressions from watched directories.
   - `scheduler`: Background daemon checking nightly execution windows and pruning crashed zombie batch records.
   - `tunnel_manager`: Manages background subprocesses for Cloudflare Zero Trust tunnels (`cloudflared`).

```
[Factory Machine / Network Share]
               │
               ▼ (N-1 File Discovery)
         [SyncEngine] ──────────────┐
               │                    ▼
               │ (Metadata Extraction via Regex)
               ▼
       [SQLite Database] ◄── [FTS5 Search Index (Trigram)]
         (portal.db)
               ▲
               │ (Parameterized SQL Queries)
    [Flask Application (Waitress WSGI)]
      ├── /auth      (Login, OAuth, Password Reset)
      ├── /portal    (Report Search, Raw Stream, Download)
      ├── /company   (Company-Admin Delegated User Management)
      └── /admin     (Master Config, Users, Tenancy, Tunnels)
```

---

## 2. Request Lifecycle & Application Factory

The application factory `create_app(test_config=None)` in [`app/__init__.py`](../app/__init__.py) initializes and configures the portal:

1. **PyInstaller Frozen Path Resolution**:
   - Detects `getattr(sys, "frozen", False)`. When frozen into a binary, sets template and static paths to `sys._MEIPASS`. When executed from source, resolves paths relative to the repository root.
2. **Configuration Loading**:
   - Instantiates `Config` from [`app/config.py`](../app/config.py), loading environment variables from `.env` via `python-dotenv`.
3. **Security Extensions Initialization**:
   - `CSRFProtect`: Injects CSRF validation across state-changing HTTP requests.
   - `LoginManager`: Manages session user loading via `load_user(user_id)`.
   - `Limiter`: Enforces IP-based rate limiting (default: `1000 per day`, `100 per hour`).
   - `init_oauth`: Registers Authlib client instance with the application.
4. **Database Connection Hooks**:
   - `@app.before_request`: Opens a dedicated SQLite connection per request into `flask.g.db` with `PRAGMA journal_mode = WAL`, `PRAGMA foreign_keys = ON`, and `PRAGMA busy_timeout = 5000`.
   - `@app.teardown_request`: Closes `flask.g.db` on request termination.
5. **Blueprint Registration**:
   - Registers `auth_bp` (`/login`, `/logout`, `/register`, `/oauth/*`, `/reset-password/*`).
   - Registers `portal_bp` (`/`, `/search`, `/search/results`, `/download/<id>`, `/view-raw/<id>`).
   - Registers `company_bp` (URL prefix `/company`: `/users`, `/users/add`, `/users/bulk_import`, `/recipes/update`).
   - Registers `admin_bp` (URL prefix `/admin`: `/`, `/customers/*`, `/users/*`, `/settings`, `/sso`, `/tunnel/action`, `/diagnostics`, `/repair`).

---

## 3. Multi-Tenancy & Customer Scoping Model

Multi-tenancy isolation is enforced at the database query level through the `customer_scope(user)` helper in [`app/helpers.py`](../app/helpers.py):

```python
def customer_scope(user):
    if user.is_admin:
        return "1=1", []

    if getattr(user, "access_mode", "ALL") == "CUSTOM":
        where = "customer_id = ? AND recipe_name IN (SELECT recipe_name FROM user_recipes WHERE user_id = ?)"
        params = [user.customer_id, int(user.id)]
    else:
        where = "customer_id = ? AND recipe_name IN (SELECT recipe_name FROM customer_recipes WHERE customer_id = ?)"
        params = [user.customer_id, user.customer_id]

    return where, params
```

- **Master Admin (`is_admin=True`)**: Unrestricted global scope (`1=1`).
- **Standard Company Viewer (`access_mode='ALL'`)**: Scoped to the user's `customer_id` and restricted to recipes granted to the customer company in `customer_recipes`.
- **Granular Viewer (`access_mode='CUSTOM'`)**: Scoped to the user's `customer_id` and restricted to the specific subset of recipes assigned to that individual user in `user_recipes`.
- **Global Customer Suspension**: When `customers.portal_suspended = 1`, non-admin users belonging to that customer are immediately denied login and redirected with a suspension notification.

---

## 4. Ingestion Pipeline & N-1 Batch Processing

The ingestion engine in [`app/sync_engine.py`](../app/sync_engine.py) processes factory reports:

### N-1 Strategy
Manufacturing machines write Excel reports continuously over the local network. Scanning active files introduces race conditions and Windows file locks. The `SyncEngine` defaults to scanning files generated on the previous calendar day ($N-1$):

```python
target_date = date.today() - timedelta(days=1)
```

### Ingestion Stages:
1. **Source Discovery**:
   - Queries `folder_mappings` to obtain all monitored folder paths and their associated customer IDs (with fallback to `system_settings.root_search_path`).
2. **File Safety Verification (`ensure_file_safe`)**:
   - Checks for read lock by attempting to read 1 byte.
   - Rejects zero-byte files (`os.path.getsize(filepath) == 0`).
   - For files modified within the last 60 seconds, sleeps 0.5s and checks if file size changes to detect active in-flight network copies.
3. **Metadata Extraction via Regex (`app/parser.py`)**:
   - Extracts `recipe_name`, `report_date`, `report_time`, and `serial_raw` from the filename using configured regular expressions.
   - Normalizes serial numbers (e.g. `12` &rarr; `0012`).
4. **Cryptographic Deduplication**:
   - Calculates the SHA-256 hash of the file in 64 KB chunks (`hash_file`).
   - If `file_hash` already exists in `reports`, the duplicate is skipped and recorded in `files_skipped`.
5. **Storage Relocation & Indexing**:
   - Copies file to `STORAGE_FOLDER/YYYY-MM-DD/filename.xlsx`.
   - Inserts record into `reports` within an explicit database transaction. Triggers automatically populate the `reports_fts` full-text search index.

---

## 5. Background Scheduler & Watchdog

[`app/scheduler.py`](../app/scheduler.py) runs as a daemon thread initialized on server startup (`start_background_scheduler`):

- **Trigger Window**: Reads `sync_time` from `system_settings` (default: `02:00`). Executes when current time falls within a 5-minute window of the configured time and has not already executed on the current calendar date (`last_sync_date != today`).
- **Zombie Batch Watchdog**: Checks for batch executions stuck in `status = 'running'` for more than 45 minutes and marks them as `CRASHED_ZOMBIE` with a diagnostic log entry.

---

## 6. Architectural Decision Records (ADRs)

### ADR 1: SQLite WAL Mode vs External Database Server
- **Decision**: Dedicated single-file SQLite database configured with `PRAGMA journal_mode = WAL`, `PRAGMA synchronous = NORMAL`, and `PRAGMA busy_timeout = 5000`.
- **Context**: The portal is designed for single factory server deployments without dedicated database administrators.
- **Consequences**: Avoids managing separate PostgreSQL/MySQL services or credentials. SQLite WAL permits concurrent reads while batch ingestion writes proceed without lock contention. Backups consist of copying `data/portal.db`.

### ADR 2: Client-Side SheetJS Rendering vs Server-Side LibreOffice Conversion
- **Decision**: Stream raw report binaries to authenticated clients and render workbooks in the browser using SheetJS WebAssembly (`xlsx.full.min.js`).
- **Context**: Converting multi-sheet Excel files to HTML or PDF on the server using headless LibreOffice or Python libraries consumes substantial CPU and memory during multi-user traffic.
- **Consequences**: Eliminates server-side rendering bottlenecks and maintains interactive multi-sheet tab navigation.

### ADR 3: Dynamic Filename Regex Engine vs Hardcoded String Slicing
- **Decision**: Persist configurable regular expression patterns in `system_settings` with named capture groups (`recipe`, `date`, `time`, `serial`).
- **Context**: Factory part naming conventions change over time.
- **Consequences**: Administrators can adjust filename parsing rules directly via the Web UI with live preview and validation without modifying code or redeploying binaries.

### ADR 4: Cloudflare Zero Trust Tunnel Subprocess vs Public Port Forwarding
- **Decision**: Native process orchestration of `cloudflared` directly from Python.
- **Context**: Factory PCs reside behind NAT and corporate firewalls. Opening inbound ports creates security risks.
- **Consequences**: Outbound-only encrypted tunnels allow remote access over HTTPS without router modifications or inbound port forwarding.
