# Database Schema & Migrations

This document specifies the SQLite database schema, table definitions, foreign key relationships, triggers, full-text search virtual tables, and the `PRAGMA user_version` migration system implemented in [`app/database.py`](../app/database.py).

---

## 1. Engine Configuration & Runtime Pragmas

Database connections are created via `get_connection(db_path)` in `app/database.py`:

```python
conn = sqlite3.connect(db_path, check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA synchronous = NORMAL")
conn.execute("PRAGMA foreign_keys = ON")
conn.execute("PRAGMA busy_timeout = 5000")
```

- **Journal Mode**: `WAL` (Write-Ahead Logging) enables concurrent read access while background ingestion processes write to the database.
- **Synchronous**: `NORMAL` ensures durability across power events without disk sync bottlenecks on every write.
- **Foreign Keys**: `ON` enforces relational constraints and cascading deletes.
- **Busy Timeout**: `5000ms` prevents write-lock exceptions during brief concurrent writes.

---

## 2. Table Catalog

### `customers`
Stores tenant organization entities.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `TEXT` | `PRIMARY KEY` | Unique customer organization identifier (e.g. `tvs`, `mahindra`). |
| `company_name` | `TEXT` | `NOT NULL` | Display name of the customer company. |
| `portal_suspended` | `INTEGER` | `NOT NULL DEFAULT 0` | Boolean flag (1=suspended, 0=active). Suspends all non-admin logins for the company. |
| `allowed_domains` | `TEXT` | `NULLABLE` | Comma-separated list of corporate email domains for auto-join during registration/SSO. |
| `created_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | ISO timestamp of record creation. |

---

### `customer_recipes`
Associates product recipes with a customer organization.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | `TEXT` | `NOT NULL`, `REFERENCES customers(id) ON DELETE CASCADE` | Associated customer ID. |
| `recipe_name` | `TEXT` | `NOT NULL` | Name of the authorized inspection recipe. |

*Primary Key*: `(customer_id, recipe_name)`

---

### `users`
Stores user accounts and authorization roles.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Internal user identifier. |
| `username` | `TEXT` | `NOT NULL UNIQUE` | Login username. |
| `email` | `TEXT` | `UNIQUE` | User email address. |
| `password_hash` | `TEXT` | `NOT NULL` | Salted password hash generated via `generate_password_hash()`. |
| `display_name` | `TEXT` | `NOT NULL` | User full name. |
| `role` | `TEXT` | `NOT NULL DEFAULT 'customer_viewer'` | Role (`admin`, `company_admin`, `customer_viewer`). |
| `customer_id` | `TEXT` | `NULLABLE`, `REFERENCES customers(id) ON DELETE CASCADE` | Tenant company association (NULL for master admins). |
| `access_mode` | `TEXT` | `NOT NULL DEFAULT 'ALL'` | Access mode: `ALL` (all company recipes) or `CUSTOM` (granular user recipes). |
| `is_active` | `INTEGER` | `NOT NULL DEFAULT 1` | Boolean account activation flag. |
| `failed_attempts` | `INTEGER` | `NOT NULL DEFAULT 0` | Consecutive failed login attempts (locks at 5). |
| `locked_until` | `TEXT` | `NULLABLE` | Lockout expiration timestamp. |
| `last_login_at` | `TEXT` | `NULLABLE` | Timestamp of last successful authentication. |
| `created_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | Account creation timestamp. |

---

### `user_recipes`
Stores granular recipe permissions for users with `access_mode = 'CUSTOM'`.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `INTEGER` | `NOT NULL`, `REFERENCES users(id) ON DELETE CASCADE` | Associated user ID. |
| `recipe_name` | `TEXT` | `NOT NULL` | Name of the assigned recipe. |

*Primary Key*: `(user_id, recipe_name)`

---

### `batch_runs`
Tracks ingestion job executions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Ingestion batch ID. |
| `run_started` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | Ingestion start timestamp. |
| `run_completed` | `TEXT` | `NULLABLE` | Ingestion completion timestamp. |
| `target_date` | `TEXT` | `NULLABLE` | Scanned file target date (`YYYY-MM-DD`). |
| `files_scanned` | `INTEGER` | `DEFAULT 0` | Discovered matching files. |
| `files_inserted` | `INTEGER` | `DEFAULT 0` | Newly indexed report records. |
| `files_skipped` | `INTEGER` | `DEFAULT 0` | Duplicate or invalid files skipped. |
| `files_failed` | `INTEGER` | `DEFAULT 0` | Unreadable or locked files failed. |
| `error_log` | `TEXT` | `NULLABLE` | Detailed execution trace or error output. |
| `status` | `TEXT` | `NOT NULL DEFAULT 'running'` | Status (`running`, `completed`, `failed`, `CRASHED_ZOMBIE`). |

---

### `folder_mappings`
Maps watched directories to customer organizations.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Folder mapping ID. |
| `folder_path` | `TEXT` | `NOT NULL UNIQUE` | Absolute or relative folder path on the server or network share. |
| `customer_id` | `TEXT` | `NULLABLE`, `REFERENCES customers(id) ON DELETE SET NULL` | Assigned customer tenant. |
| `created_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | Mapping creation timestamp. |

---

### `reports`
Stores indexed inspection reports.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique report record ID. |
| `batch_run_id` | `INTEGER` | `NULLABLE`, `REFERENCES batch_runs(id) ON DELETE SET NULL` | Associated batch run. |
| `customer_id` | `TEXT` | `NULLABLE`, `REFERENCES customers(id) ON DELETE SET NULL` | Associated customer organization. |
| `recipe_name` | `TEXT` | `NOT NULL` | Product recipe identifier parsed from filename. |
| `report_date` | `TEXT` | `NOT NULL` | Inspection date (`YYYY-MM-DD`). |
| `report_time` | `TEXT` | `NULLABLE` | Inspection time (`HH:MM:SS`). |
| `serial_raw` | `TEXT` | `NULLABLE` | Serial number string as parsed from filename. |
| `serial_normalized` | `TEXT` | `NOT NULL` | Zero-padded or standardized serial number. |
| `original_filename` | `TEXT` | `NOT NULL UNIQUE` | File basename. |
| `file_path` | `TEXT` | `NOT NULL UNIQUE` | Local filesystem storage path. |
| `file_hash` | `TEXT` | `NOT NULL` | SHA-256 cryptographic digest of file contents. |
| `file_size_bytes` | `INTEGER` | `NULLABLE` | File size in bytes. |
| `ingested_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | Ingestion timestamp. |

**Indexes**:
- `idx_reports_recipe`: `ON reports(recipe_name, report_date, serial_normalized)`
- `idx_reports_customer`: `ON reports(customer_id)`

---

### `search_metrics`
Records query latency for quality telemetry.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Record ID. |
| `latency_ms` | `REAL` | `NOT NULL` | Search execution latency in milliseconds. |
| `timestamp` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | Query execution timestamp. |

**Trigger**: `search_metrics_prune` automatically deletes records where `id <= (new.id - 10000)` to cap table growth.

---

### `audit_log`
Forensic event audit trail.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Log ID. |
| `user_id` | `INTEGER` | `NOT NULL`, `REFERENCES users(id) ON DELETE CASCADE` | Actor user ID. |
| `report_id` | `INTEGER` | `NULLABLE` | Target report ID (for views and downloads). |
| `action` | `TEXT` | `NOT NULL` | Action (`login`, `download`, `view_online`, etc.). |
| `detail` | `TEXT` | `NULLABLE` | Context or metadata. |
| `client_ip` | `TEXT` | `NULLABLE` | Client remote IP address. |
| `user_agent` | `TEXT` | `NULLABLE` | Client browser User-Agent header. |
| `created_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | Event timestamp. |

---

### `system_settings`
Key-value configuration store.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `key` | `TEXT` | `PRIMARY KEY` | Configuration key. |
| `value` | `TEXT` | `NULLABLE` | Configuration value. Sensitive secrets are AES-256 encrypted. |
| `updated_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` | Last modification timestamp. |

---

## 3. Full-Text Search Virtual Table (`reports_fts`)

The application provisions a trigram-tokenized SQLite `FTS5` virtual table for full-text search:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS reports_fts USING fts5(
    serial_normalized,
    recipe_name,
    original_filename,
    content='reports',
    content_rowid='id',
    tokenize='trigram'
);
```

### Synchronization Triggers:
1. `reports_fts_insert`: After `INSERT ON reports`, inserts row into `reports_fts`.
2. `reports_fts_delete`: After `DELETE ON reports`, deletes row from `reports_fts`.
3. `reports_fts_update`: After `UPDATE ON reports`, re-indexes row in `reports_fts`.

---

## 4. Migration Architecture (`PRAGMA user_version`)

Schema versioning is managed natively in [`app/database.py`](../app/database.py) using SQLite's built-in `PRAGMA user_version`.

### Version Progression:
- **v1**: Base table creation (`customers`, `customer_recipes`, `users`, `user_recipes`, `batch_runs`, `folder_mappings`, `reports`, `search_metrics`, `audit_log`, `system_settings`, `reports_fts`).
- **v2**: Adds `access_mode` and `customer_id` columns to `users`.
- **v3**: Adds `portal_suspended` column to `customers`.
- **v4**: Adds `allowed_domains` column to `customers`.

### Adding a New Migration:
1. Increment `LATEST_SCHEMA_VERSION` in `app/database.py`.
2. Define a migration function `_migration_vN_<description>(conn)`.
3. Append `(N, "<Description>", _migration_vN_<description>)` to the `MIGRATIONS` list.
4. Add corresponding assertions in [`tests/test_schema_migrations.py`](../tests/test_schema_migrations.py).
