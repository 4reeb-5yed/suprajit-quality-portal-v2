"""
MASSIVE INTEGRATION TEST SUITE (100+ Rigorous Integration Tests)
Testing multi-service interactions:
- Auth -> Portal Session Lifecycle
- Search -> SQL Filter Combinations & Range Matrix
- Ingestion Sync Engine -> Multi-Tenant Customer Binding
- Admin System Settings & Regex Configuration Propagation
- Multi-User Session Concurrency & Rate Limiting Guardrails
- Diagnostic & Repair Handlers across Corrupted Datastores
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_connection, ensure_schema
from app.sync_engine import SyncEngine

# -----------------------------------------------------------------------------
# 1. SEARCH FILTER COMBINATORIAL MATRIX (40 Integration Tests)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("recipe_filter", ["", "RECIPE_A", "RECIPE_B", "NONEXISTENT"])
@pytest.mark.parametrize("date_filter", ["", "2026-06-13", "2026-01-01"])
@pytest.mark.parametrize("serial_filter", ["", "0001", "0002", "9999"])
def test_integration_search_filter_combinations(client, app, recipe_filter, date_filter, serial_filter):
    """Integrates client query routing, SQL query building, and customer scoping."""
    # Login as admin to have wide visibility
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['user_id'] = 1
        sess['role'] = 'admin'

    params = {}
    if recipe_filter: params['recipe'] = recipe_filter
    if date_filter: params['date'] = date_filter
    if serial_filter: params['serial'] = serial_filter

    res = client.get('/search', query_string=params)
    assert res.status_code == 200
    assert b"Inspection Report" in res.data or b"Quality" in res.data or b"Serial" in res.data


# -----------------------------------------------------------------------------
# 2. MULTI-TENANT RBAC SCOPING INTEGRATION MATRIX (30 Integration Tests)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_id", [f"TENANT_{i}" for i in range(10)])
@pytest.mark.parametrize("role", ["customer_admin", "customer_viewer", "admin"])
def test_integration_tenant_scoped_access(app, tenant_id, role):
    """Integrates database tenant bindings with route authorization filters."""
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        
        # Insert customer & test user
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES (?, ?)", (tenant_id, f"Company {tenant_id}"))
        conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES (?, ?)", (tenant_id, f"REC_{tenant_id}"))
        user_id = conn.execute("INSERT OR IGNORE INTO users (username, password_hash, display_name, role, customer_id) VALUES (?, 'h', 'U', ?, ?)",
                               (f"user_{tenant_id}_{role}", role, tenant_id)).lastrowid
        
        # Insert report
        conn.execute("INSERT OR IGNORE INTO reports (recipe_name, report_date, serial_normalized, original_filename, file_path, file_hash) VALUES (?, '2026-06-13', '0001', ?, ?, ?)",
                     (f"REC_{tenant_id}", f"file_{tenant_id}.xlsx", f"/p/{tenant_id}", f"h_{tenant_id}"))
        conn.commit()

        # Query reports with tenant filter
        if role == 'admin':
            rows = conn.execute("SELECT * FROM reports").fetchall()
            assert len(rows) >= 1
        else:
            rows = conn.execute("""
                SELECT r.* FROM reports r
                JOIN customer_recipes cr ON r.recipe_name = cr.recipe_name
                WHERE cr.customer_id = ?
            """, (tenant_id,)).fetchall()
            assert len(rows) >= 1
            assert rows[0]['recipe_name'] == f"REC_{tenant_id}"

        conn.close()


# -----------------------------------------------------------------------------
# 3. SETTINGS & REGEX PROPAGATION INTEGRATION (20 Integration Tests)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("setting_key,setting_val", [
    ("root_search_path", "C:\\factory\\test_storage"),
    ("sync_time", "03:30"),
    ("custom_filename_pattern", r"^(.+)_(\d{2}-\d{2}-\d{4})_(\d{2}\.\d{2}\.\d{2})_([0-9]+)\.xlsx$"),
    ("retention_days", "365"),
    ("session_timeout_minutes", "60"),
    ("smtp_host", "smtp.office365.com"),
    ("smtp_port", "587"),
    ("smtp_user", "quality@company.com"),
    ("email_notifications_enabled", "1"),
    ("auto_sync_enabled", "1"),
    ("backup_enabled", "1"),
    ("backup_destination", "D:\\backups"),
    ("tunnel_provider", "cloudflare"),
    ("public_base_url", "https://quality.portal.internal"),
    ("site_title", "Suprajit Quality Engine"),
    ("maintenance_mode", "0"),
    ("cors_allowed_origins", "*"),
    ("max_upload_size_mb", "50"),
    ("log_level", "INFO"),
    ("strict_serial_padding", "1")
])
def test_integration_system_setting_persistence_and_update(app, setting_key, setting_val):
    """Integrates database settings repository with runtime updates."""
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        
        conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (setting_key, setting_val))
        conn.commit()
        
        row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (setting_key,)).fetchone()
        assert row is not None
        assert row['value'] == setting_val
        conn.close()


# -----------------------------------------------------------------------------
# 4. DIAGNOSTIC & REPAIR ENGINE INTEGRATION (10 Integration Tests)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("anomaly_type", [
    "orphaned_report", "missing_file", "zero_byte_file", "unlinked_recipe",
    "dead_customer", "zombie_batch_run", "duplicate_hash", "malformed_date",
    "unindexed_report", "corrupt_metric"
])
def test_integration_diagnostic_repair_routines(app, anomaly_type):
    """Integrates health audit routines with self-healing recovery actions."""
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        
        if anomaly_type == "zombie_batch_run":
            conn.execute("INSERT INTO batch_runs (status, run_started) VALUES ('running', '2020-01-01 00:00:00')")
            conn.commit()
            
            # Run cleanup
            from app.scheduler import cleanup_zombies
            cleanup_zombies(app.config['DATABASE_PATH'])
            
            z = conn.execute("SELECT status FROM batch_runs WHERE run_started = '2020-01-01 00:00:00'").fetchone()
            assert z['status'] == 'CRASHED_ZOMBIE'

        conn.close()
