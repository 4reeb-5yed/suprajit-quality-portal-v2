import logging
import sqlite3

logger = logging.getLogger(__name__)

# ─── DATABASE INITIALIZATION ───


def get_connection(db_path):
    """Returns a configured sqlite3 connection using WAL mode for concurrency."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")  # 5 second timeout for concurrent writes
    return conn


def _migration_v1_base_schema(conn):
    """V1: Core Base Schema Definition."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id              TEXT PRIMARY KEY,
            company_name    TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS customer_recipes (
            customer_id     TEXT NOT NULL,
            recipe_name     TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            PRIMARY KEY (customer_id, recipe_name)
        );

        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            email           TEXT UNIQUE,
            password_hash   TEXT NOT NULL,
            display_name    TEXT NOT NULL,
            role            TEXT NOT NULL DEFAULT 'customer_viewer',
            is_active       INTEGER NOT NULL DEFAULT 1,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until    TEXT,
            last_login_at   TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_recipes (
            user_id     INTEGER NOT NULL,
            recipe_name TEXT NOT NULL,
            PRIMARY KEY (user_id, recipe_name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS batch_runs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_started     TEXT NOT NULL DEFAULT (datetime('now')),
            run_completed   TEXT,
            target_date     TEXT,
            files_scanned   INTEGER DEFAULT 0,
            files_inserted  INTEGER DEFAULT 0,
            files_skipped   INTEGER DEFAULT 0,
            files_failed    INTEGER DEFAULT 0,
            error_log       TEXT,
            status          TEXT NOT NULL DEFAULT 'running'
        );

        CREATE TABLE IF NOT EXISTS folder_mappings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path     TEXT NOT NULL UNIQUE,
            customer_id     TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS reports (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_run_id        INTEGER,
            customer_id         TEXT,
            recipe_name         TEXT NOT NULL,
            report_date         TEXT NOT NULL,
            report_time         TEXT,
            serial_raw          TEXT,
            serial_normalized   TEXT NOT NULL,
            original_filename   TEXT NOT NULL UNIQUE,
            file_path           TEXT NOT NULL UNIQUE,
            file_hash           TEXT NOT NULL,
            file_size_bytes     INTEGER,
            ingested_at         TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (batch_run_id) REFERENCES batch_runs(id) ON DELETE SET NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_reports_recipe ON reports(recipe_name, report_date, serial_normalized);
        CREATE INDEX IF NOT EXISTS idx_reports_customer ON reports(customer_id);

        CREATE TABLE IF NOT EXISTS search_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latency_ms REAL NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TRIGGER IF NOT EXISTS search_metrics_prune AFTER INSERT ON search_metrics BEGIN
            DELETE FROM search_metrics WHERE id <= (new.id - 10000);
        END;

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            report_id   INTEGER,
            action      TEXT NOT NULL,
            detail      TEXT,
            client_ip   TEXT,
            user_agent  TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS system_settings (
            key         TEXT PRIMARY KEY,
            value       TEXT,
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Virtual table for instant search
        CREATE VIRTUAL TABLE IF NOT EXISTS reports_fts USING fts5(
            serial_normalized,
            recipe_name,
            original_filename,
            content='reports',
            content_rowid='id',
            tokenize='trigram'
        );

        CREATE TRIGGER IF NOT EXISTS reports_fts_insert AFTER INSERT ON reports BEGIN
            INSERT INTO reports_fts(rowid, serial_normalized, recipe_name, original_filename)
            VALUES (new.id, new.serial_normalized, new.recipe_name, new.original_filename);
        END;

        CREATE TRIGGER IF NOT EXISTS reports_fts_delete AFTER DELETE ON reports BEGIN
            INSERT INTO reports_fts(reports_fts, rowid, serial_normalized, recipe_name, original_filename)
            VALUES ('delete', old.id, old.serial_normalized, old.recipe_name, old.original_filename);
        END;

        CREATE TRIGGER IF NOT EXISTS reports_fts_update AFTER UPDATE ON reports BEGIN
            INSERT INTO reports_fts(reports_fts, rowid, serial_normalized, recipe_name, original_filename)
            VALUES ('delete', old.id, old.serial_normalized, old.recipe_name, old.original_filename);
            INSERT INTO reports_fts(rowid, serial_normalized, recipe_name, original_filename)
            VALUES (new.id, new.serial_normalized, new.recipe_name, new.original_filename);
        END;
    """)


def _migration_v2_user_access_mode_and_customer_id(conn):
    """V2: Add access_mode and customer_id columns to users table."""
    user_cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "access_mode" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN access_mode TEXT NOT NULL DEFAULT 'ALL'")
    if "customer_id" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN customer_id TEXT")


def _migration_v3_customer_portal_suspended(conn):
    """V3: Add portal_suspended column to customers table."""
    cust_cols = [r["name"] for r in conn.execute("PRAGMA table_info(customers)").fetchall()]
    if "portal_suspended" not in cust_cols:
        conn.execute("ALTER TABLE customers ADD COLUMN portal_suspended INTEGER NOT NULL DEFAULT 0")


def _migration_v4_customer_allowed_domains(conn):
    """V4: Add allowed_domains column to customers table."""
    cust_cols = [r["name"] for r in conn.execute("PRAGMA table_info(customers)").fetchall()]
    if "allowed_domains" not in cust_cols:
        conn.execute("ALTER TABLE customers ADD COLUMN allowed_domains TEXT")


def _migration_v5_report_customer_id(conn):
    """V5: Ensure customer_id column exists on reports and folder_mappings tables."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "reports" in tables:
        report_cols = [r["name"] for r in conn.execute("PRAGMA table_info(reports)").fetchall()]
        if "customer_id" not in report_cols:
            conn.execute("ALTER TABLE reports ADD COLUMN customer_id TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_customer ON reports(customer_id)")

    if "folder_mappings" in tables:
        folder_cols = [r["name"] for r in conn.execute("PRAGMA table_info(folder_mappings)").fetchall()]
        if "customer_id" not in folder_cols:
            conn.execute("ALTER TABLE folder_mappings ADD COLUMN customer_id TEXT")


MIGRATIONS = [
    (1, "Core Base Schema Definition", _migration_v1_base_schema),
    (2, "User Granular Access Mode & Customer Association", _migration_v2_user_access_mode_and_customer_id),
    (3, "Customer Portal Suspension Support", _migration_v3_customer_portal_suspended),
    (4, "Customer Auto-Join Allowed Domains Support", _migration_v4_customer_allowed_domains),
    (5, "Reports and Folder Mappings Customer Association", _migration_v5_report_customer_id),
]

LATEST_SCHEMA_VERSION = 5


def get_current_schema_version(conn):
    """Reads PRAGMA user_version from SQLite."""
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _infer_legacy_schema_version(conn):
    """Infers the baseline version for existing databases created before PRAGMA user_version tracking."""
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "users" not in tables or "customers" not in tables:
        return 0

    user_cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    cust_cols = {r["name"] for r in conn.execute("PRAGMA table_info(customers)").fetchall()}

    has_access_mode = "access_mode" in user_cols
    has_customer_id = "customer_id" in user_cols
    has_portal_suspended = "portal_suspended" in cust_cols
    has_allowed_domains = "allowed_domains" in cust_cols

    if has_access_mode and has_customer_id and has_portal_suspended and has_allowed_domains:
        return 4
    elif has_access_mode and has_customer_id and has_portal_suspended:
        return 3
    elif has_access_mode and has_customer_id:
        return 2
    else:
        return 1


def ensure_schema(conn):
    """Explicit, ordered, version-tracked migrations using SQLite PRAGMA user_version."""
    current_ver = get_current_schema_version(conn)

    # Backward compatibility: infer version for pre-migration databases
    if current_ver == 0:
        inferred_ver = _infer_legacy_schema_version(conn)
        if inferred_ver > 0:
            conn.execute(f"PRAGMA user_version = {inferred_ver}")
            current_ver = inferred_ver

    for version_num, desc, migration_func in MIGRATIONS:
        if version_num > current_ver:
            logger.info("Applying schema migration v%d: %s", version_num, desc)
            try:
                conn.execute("BEGIN")
                migration_func(conn)
                conn.execute(f"PRAGMA user_version = {version_num}")
                conn.commit()
                current_ver = version_num
            except Exception as e:
                conn.rollback()
                logger.error("Schema migration v%d failed: %s. Rolling back.", version_num, e)
                raise


# ─── QUERY CATALOG ───

# Customers
GET_ALL_CUSTOMERS = "SELECT * FROM customers ORDER BY company_name"
GET_CUSTOMER_BY_ID = "SELECT * FROM customers WHERE id = ?"
INSERT_CUSTOMER = "INSERT INTO customers (id, company_name) VALUES (?, ?)"
UPDATE_CUSTOMER = "UPDATE customers SET company_name=? WHERE id=?"
DELETE_CUSTOMER = "DELETE FROM customers WHERE id=?"
TOGGLE_CUSTOMER_SUSPENSION = "UPDATE customers SET portal_suspended=? WHERE id=?"

# Customer Recipes
INSERT_CUSTOMER_RECIPE = "INSERT INTO customer_recipes (customer_id, recipe_name) VALUES (?, ?)"
DELETE_CUSTOMER_RECIPE = "DELETE FROM customer_recipes WHERE customer_id = ? AND recipe_name = ?"

# User Recipes (Granular Access)
INSERT_USER_RECIPE = "INSERT OR IGNORE INTO user_recipes (user_id, recipe_name) VALUES (?, ?)"
DELETE_USER_RECIPES = "DELETE FROM user_recipes WHERE user_id = ?"

# Users
GET_USER_BY_USERNAME = "SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)"
GET_USER_BY_EMAIL = "SELECT * FROM users WHERE LOWER(email) = LOWER(?)"
GET_USER_BY_ID = "SELECT * FROM users WHERE id = ?"
GET_USERS_BY_CUSTOMER = "SELECT * FROM users WHERE customer_id = ?"
INSERT_USER = "INSERT INTO users (username, email, password_hash, display_name, role, customer_id, access_mode) VALUES (?, ?, ?, ?, ?, ?, ?)"
UPDATE_USER_PASSWORD = "UPDATE users SET password_hash = ? WHERE id = ?"
UPDATE_USER_LOCKOUT = "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?"
TOGGLE_USER_ACCESS = "UPDATE users SET is_active = ? WHERE id = ?"
UPDATE_USER_ACCESS_MODE = "UPDATE users SET access_mode = ? WHERE id = ?"

# System Settings
GET_SETTING = "SELECT value FROM system_settings WHERE key = ?"
SET_SETTING = "INSERT OR REPLACE INTO system_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))"
