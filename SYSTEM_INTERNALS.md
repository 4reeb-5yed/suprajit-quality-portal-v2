# Suprajit Quality Portal V2 - System Internals & Developer Guide

This document is the absolute source of truth for the Suprajit Quality Portal V2. It explains exactly how the software works, where data lives, how security is enforced, and what every file does.

---

## 1. How Data is Stored

### The Database (`portal.db`)
Unlike V1 which relied on complex setups, V2 uses a single file: `data/portal.db`. 
- **Engine:** SQLite running in **WAL (Write-Ahead Logging) mode**. This allows the background ingestion thread to write to the database at the exact same time a customer is searching it on the frontend, without locking each other out.
- **Location:** The database is stored inside a `data/` folder sitting right next to the `.exe` file.
- **Data Safety:** If you need to backup the entire system or move it to a new server, you only need to copy the `data/` folder.

### The Watched Folder (Storage)
- The system does *not* move or alter the factory's Excel files.
- The path to the watched folder (e.g., `Z:\FactoryData`) is configured in the UI under **Admin -> Settings** and stored in the database's `system_settings` table under the key `root_search_path`.
- The system reads this path, scans the files, extracts metadata, and maps the SQL row's `file_path` directly to the original file. 

---

## 2. Security & Credentials

### Passwords
- **Storage:** Passwords are NEVER stored in plain text. They are hashed using **Werkzeug's `scrypt` algorithm** and stored in the `password_hash` column of the `users` table. 
- **Encryption Process:** When a user logs in, the system hashes the password they typed and compares it to the hash in the database. Even if the database is stolen, passwords cannot be reversed.
- **SMTP/Email Password:** Stored in the `system_settings` table. It is no longer echoed into the HTML frontend, preventing "View Source" leaks.

### Network Defenses (OWASP Compliance)
- **CSRF (Cross-Site Request Forgery):** Powered by `Flask-WTF`. Every form submission requires a hidden security token, preventing attackers from tricking admins into submitting requests via malicious links.
- **Brute Force & Credential Spraying:** Powered by `Flask-Limiter`. The `/login` endpoint strictly allows a maximum of 5 attempts per minute per IP address. Attackers cannot script login attempts.
- **Path Traversal Guard:** Downloads are protected by `app.helpers.is_safe_path()`, meaning a user cannot manipulate the URL to download `C:\Windows\System32\cmd.exe` or the database itself.

---

## 3. The Codebase Architecture (File by File)

### Core Engine
*   **`run.py` & `web_server.py`:** The entry points. `run.py` is for local dev (Flask internal server). `web_server.py` is for production, booting the **Waitress** WSGI server to handle hundreds of concurrent Windows connections.
*   **`app/__init__.py`:** The Factory. This boots the Flask app, connects the database, arms the rate limiters, enforces the unique `SECRET_KEY`, generates the `bootstrap_admin` account, and injects the Enterprise Log Rotation.
*   **`app/config.py`:** Reads environmental variables (`.env`) or provides fallback configurations (like the default Port 5000).
*   **`app/database.py`:** Manages SQLite connections and houses the `ensure_schema()` function which automatically creates the tables if they are missing. It also stores the raw SQL query constants.

### The Ingestion Pipeline (The Magic)
*   **`app/scheduler.py`:** An infinite loop running on a separate background thread. Every 60 seconds, it checks if the current time falls within a 5-minute window of the `sync_time` setting. If so, it triggers the `SyncEngine`. It also acts as the **Zombie Watchdog**, detecting and flagging crashed ingestion runs.
*   **`app/sync_engine.py`:** The workhorse. It traverses the Watched Folder, skips files modified today (N-1 day logic to prevent file locks), checks if files are already in the DB, and orchestrates the insertion of new records.
*   **`app/parser.py`:** The brain of the extraction. It uses **Regex (Regular Expressions)** to instantly extract the Recipe, Date, Time, and Serial Number directly from the filename (e.g., `EV_TPS_13-06-2026_22.33.21_12.xlsx`). Because it uses Regex instead of Excel libraries, it can process 10,000 files in under a second.

### The Web Interface (Routes & Views)
*   **`app/routes/auth.py`:** Handles login, logout, and password resets using secure time-signed URL tokens.
*   **`app/routes/portal.py`:** The Customer Frontend. Handles the search bar, filtering, and the secure downloading of reports (which also triggers an insert into the `audit_log` table).
*   **`app/routes/admin.py`:** The SysAdmin Backend. Manages users, customers, settings, the Diagnostics log viewer, and manual "Force Sync" triggers.
*   **`app/helpers.py`:** Contains utilities like `customer_scope()`, which ensures that when Customer A queries the database, the SQL string is forcefully appended with `AND customer_id = 'CustomerA'`, making cross-tenant data leaks mathematically impossible.

### Telemetry & Diagnostics
*   **`app/mail.py`:** Uses Python's native `smtplib` to send welcome emails, password resets, and (if configured) daily system health telemetry to the developers. 
*   **`logs/suprajit_system.log`:** The active diagnostic file. If the `SyncEngine` crashes due to a corrupt hard drive, Python's raw traceback is written here. The UI downloads this file for the SysAdmin.

---

## 4. How Everything Talks To Each Other

1. **The Scheduler** wakes up and talks to the **Sync Engine**.
2. The **Sync Engine** talks to the **Windows File System** (to find Excel files) and to the **Parser** (to extract text). 
3. The **Sync Engine** then talks to the **Database** (SQLite), injecting thousands of rows in bulk using memory transactions.
4. An **External Customer** connects via browser. The network talks to **Waitress** (the web server). Waitress talks to **Flask** (`portal.py`). 
5. Flask talks to the **Database**, retrieves the results, and renders them via **Jinja2 HTML Templates** back to the customer. 
