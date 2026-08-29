import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# ─── DATABASE INITIALIZATION ───

def get_connection(db_path):
    """Returns a configured sqlite3 connection using WAL mode for concurrency."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000") # 5 second timeout for concurrent writes
    return conn

def ensure_schema(conn):
    """Idempotent schema initialization."""
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id              TEXT PRIMARY KEY,
                company_name    TEXT NOT NULL,
                portal_suspended INTEGER NOT NULL DEFAULT 0,
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
                customer_id     TEXT,
                access_mode     TEXT NOT NULL DEFAULT 'ALL',
                is_active       INTEGER NOT NULL DEFAULT 1,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until    TEXT,
                last_login_at   TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
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

            CREATE TABLE IF NOT EXISTS reports (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_run_id        INTEGER,
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
                FOREIGN KEY (batch_run_id) REFERENCES batch_runs(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_reports_recipe ON reports(recipe_name, report_date, serial_normalized);

            
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

        # Auto-migration for schema changes
        user_cols = [r['name'] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'access_mode' not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN access_mode TEXT NOT NULL DEFAULT 'ALL'")
        if 'customer_id' not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN customer_id TEXT")

        cust_cols = [r['name'] for r in conn.execute("PRAGMA table_info(customers)").fetchall()]
        if 'portal_suspended' not in cust_cols:
            conn.execute("ALTER TABLE customers ADD COLUMN portal_suspended INTEGER NOT NULL DEFAULT 0")
        if 'allowed_domains' not in cust_cols:
            conn.execute("ALTER TABLE customers ADD COLUMN allowed_domains TEXT")

# ─── QUERY CATALOG ───

# Customers
GET_ALL_CUSTOMERS = "SELECT * FROM customers ORDER BY company_name"
GET_CUSTOMER_BY_ID = "SELECT * FROM customers WHERE id = ?"
INSERT_CUSTOMER = "INSERT INTO customers (id, company_name) VALUES (?, ?)"
UPDATE_CUSTOMER = "UPDATE customers SET company_name=? WHERE id=?"
DELETE_CUSTOMER = "DELETE FROM customers WHERE id=?"
TOGGLE_CUSTOMER_SUSPENSION = "UPDATE customers SET portal_suspended=? WHERE id=?"

# Customer Recipes
GET_CUSTOMER_RECIPES = "SELECT recipe_name FROM customer_recipes WHERE customer_id = ?"
INSERT_CUSTOMER_RECIPE = "INSERT INTO customer_recipes (customer_id, recipe_name) VALUES (?, ?)"
DELETE_CUSTOMER_RECIPE = "DELETE FROM customer_recipes WHERE customer_id = ? AND recipe_name = ?"

# User Recipes (Granular Access)
GET_USER_RECIPES = "SELECT recipe_name FROM user_recipes WHERE user_id = ?"
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

# Reports
INSERT_REPORT = """
    INSERT OR IGNORE INTO reports 
    (batch_run_id, recipe_name, report_date, report_time, serial_raw, 
     serial_normalized, original_filename, file_path, file_hash, file_size_bytes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
GET_REPORT_BY_ID = "SELECT * FROM reports WHERE id = ?"

# System Settings
GET_SETTING = "SELECT value FROM system_settings WHERE key = ?"
SET_SETTING = "INSERT OR REPLACE INTO system_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))"