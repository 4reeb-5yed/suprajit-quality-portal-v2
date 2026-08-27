import sqlite3
import os

with open('app/database.py', 'r') as f:
    content = f.read()

# Replace the schema creation
new_schema = '''
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
                is_active       INTEGER NOT NULL DEFAULT 1,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until    TEXT,
                last_login_at   TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS batch_runs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_started     TEXT NOT NULL DEFAULT (datetime('now')),
                run_completed   TEXT,
                target_date     TEXT,
                files_scanned   INTEGER DEFAULT 0,
                files_inserted  INTEGER DEFAULT 0,
                files_skipped   INTEGER DEFAULT 0,
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
'''
start_idx = content.find('CREATE TABLE IF NOT EXISTS customers')
end_idx = content.find('\"\"\")', start_idx)
content = content[:start_idx] + new_schema.strip() + '\n        ' + content[end_idx:]

with open('app/database.py', 'w') as f:
    f.write(content)
