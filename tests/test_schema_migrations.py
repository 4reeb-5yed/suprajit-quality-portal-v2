"""
SCHEMA VERSIONING & MIGRATION TESTS
Verifies fresh database migrations, legacy pre-migration database upgrades,
and rollback on migration failure.
"""

import sqlite3
import pytest

from app.database import (
    LATEST_SCHEMA_VERSION,
    ensure_schema,
    get_connection,
    get_current_schema_version,
)

pytestmark = pytest.mark.integration


def test_fresh_database_runs_all_migrations_to_latest(tmp_path):
    """Assert a fresh database starts at 0 and migrates to LATEST_SCHEMA_VERSION."""
    db_path = str(tmp_path / "fresh.db")
    conn = get_connection(db_path)

    # Initial user_version is 0
    assert get_current_schema_version(conn) == 0

    ensure_schema(conn)

    # Assert user_version equals latest version
    assert get_current_schema_version(conn) == LATEST_SCHEMA_VERSION

    # Assert expected tables and columns exist
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert {"customers", "customer_recipes", "users", "user_recipes", "reports", "system_settings", "audit_log"}.issubset(tables)

    user_cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    assert "access_mode" in user_cols
    assert "customer_id" in user_cols

    cust_cols = {r["name"] for r in conn.execute("PRAGMA table_info(customers)").fetchall()}
    assert "portal_suspended" in cust_cols
    assert "allowed_domains" in cust_cols

    conn.close()


def test_legacy_pre_migration_database_upgrades_without_data_loss(tmp_path):
    """Simulate a legacy database created with no PRAGMA user_version and partial columns."""
    db_path = str(tmp_path / "legacy.db")
    raw_conn = sqlite3.connect(db_path)
    raw_conn.row_factory = sqlite3.Row

    # Create partial legacy schema (missing access_mode, customer_id on users; missing portal_suspended, allowed_domains on customers)
    raw_conn.executescript("""
        CREATE TABLE customers (
            id              TEXT PRIMARY KEY,
            company_name    TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE users (
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
        INSERT INTO customers (id, company_name) VALUES ('legacy_corp', 'Legacy Corporation');
        INSERT INTO users (username, password_hash, display_name) VALUES ('legacy_user', 'hash123', 'Legacy User');
    """)
    raw_conn.commit()

    assert raw_conn.execute("PRAGMA user_version").fetchone()[0] == 0
    raw_conn.close()

    # Now run ensure_schema via app get_connection
    conn = get_connection(db_path)
    ensure_schema(conn)

    # Version should now be at latest
    assert get_current_schema_version(conn) == LATEST_SCHEMA_VERSION

    # Existing data must be preserved
    cust = conn.execute("SELECT * FROM customers WHERE id = 'legacy_corp'").fetchone()
    assert cust is not None
    assert cust["company_name"] == "Legacy Corporation"
    assert cust["portal_suspended"] == 0
    assert cust["allowed_domains"] is None

    user = conn.execute("SELECT * FROM users WHERE username = 'legacy_user'").fetchone()
    assert user is not None
    assert user["display_name"] == "Legacy User"
    assert user["access_mode"] == "ALL"
    assert user["customer_id"] is None

    conn.close()


def test_migration_failure_raises_and_rolls_back(tmp_path, monkeypatch):
    """Simulate a broken migration step; verify it raises and does not advance user_version."""
    from app import database

    db_path = str(tmp_path / "broken.db")
    conn = get_connection(db_path)

    # Define a faulty migration
    def _broken_migration(c):
        c.execute("CREATE TABLE valid_part (id INT);")
        c.execute("INVALID SQL STATEMENT SYNTAX ERROR;")

    custom_migrations = [
        (1, "Valid Step 1", database._migration_v1_base_schema),
        (2, "Broken Step 2", _broken_migration),
    ]

    monkeypatch.setattr(database, "MIGRATIONS", custom_migrations)

    with pytest.raises(Exception):
        database.ensure_schema(conn)

    # user_version must have stopped at 1, not advanced to 2
    assert get_current_schema_version(conn) == 1

    # Table from broken transaction must have rolled back
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "valid_part" not in tables

    conn.close()
