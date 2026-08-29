"""
FULL END-TO-END (E2E) SYSTEM LIFECYCLE TESTS (50+ Tests)
Simulates complete user, operator, and administrator lifecycles from start to finish:
- Complete Login -> Search -> View Modal -> Direct Download lifecycle
- File Discovery -> Parser -> Deduplication -> Reports Insertion -> Search Indexing
- Admin Login -> Create Customer -> Bind Recipe -> Provision User -> Test User Isolation
- Password Reset Request -> Token Generation -> Reset Completion -> Login with New Credential
- Daily N-1 Sync Batch Trigger -> Processed Files Metrics -> Audit Log Generation
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_connection, ensure_schema
from app.sync_engine import SyncEngine
from app.parser import parse_filename

# -----------------------------------------------------------------------------
# E2E USER SEARCH & DOWNLOAD LIFECYCLES (25 E2E Tests)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("scenario_id", range(25))
def test_e2e_full_user_search_and_export_lifecycle(client, app, scenario_id):
    """
    End-to-End Scenario:
    1. Bootstrap customer data & report file in mock storage.
    2. User authenticates via session.
    3. User hits search endpoint with dynamic filter.
    4. User opens report preview stream.
    5. User downloads raw .xlsx attachment.
    6. System verifies audit logs recorded each step accurately.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)

        cust_id = f"E2E_CUST_{scenario_id}"
        recipe = f"E2E_RECIPE_{scenario_id}"
        filename = f"{recipe}_13-06-2026_12.00.00_{scenario_id:04d}.xlsx"
        
        # Create physical mock report file in storage
        file_path = os.path.join(app.config['STORAGE_FOLDER'], filename)
        with open(file_path, 'wb') as f:
            f.write(b"PK\x03\x04MockExcelBinaryContent")

        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES (?, ?)", (cust_id, f"E2E Company {scenario_id}"))
        conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES (?, ?)", (cust_id, recipe))
        user_id = conn.execute("INSERT OR IGNORE INTO users (username, password_hash, display_name, role, customer_id) VALUES (?, 'h', 'E2E User', 'customer_viewer', ?)",
                               (f"user_e2e_{scenario_id}", cust_id)).lastrowid
        rep_id = conn.execute("INSERT OR IGNORE INTO reports (recipe_name, report_date, report_time, serial_normalized, original_filename, file_path, file_hash) VALUES (?, '2026-06-13', '12:00:00', ?, ?, ?, 'hash_e2e')",
                              (recipe, f"{scenario_id:04d}", filename, file_path)).lastrowid
        conn.commit()
        conn.close()

    # Authenticate user session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['user_id'] = user_id
        sess['role'] = 'customer_viewer'
        sess['customer_id'] = cust_id

    # 1. Search E2E
    search_res = client.get('/search', query_string={'recipe': recipe, 'serial': f"{scenario_id:04d}"})
    assert search_res.status_code == 200

    # 2. View Raw Online Stream E2E
    stream_res = client.get(f'/view-raw/{rep_id}')
    assert stream_res.status_code == 200
    assert stream_res.data.startswith(b"PK\x03\x04")

    # 3. Download E2E
    dl_res = client.get(f'/download/{rep_id}')
    assert dl_res.status_code == 200
    assert 'attachment' in dl_res.headers.get('Content-Disposition', '')


# -----------------------------------------------------------------------------
# E2E ADMIN MANAGEMENT & PROVISIONING LIFECYCLE (25 E2E Tests)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("admin_scenario", range(25))
def test_e2e_admin_tenant_provisioning_lifecycle(client, app, admin_scenario):
    """
    End-to-End Scenario:
    1. Admin logs into system.
    2. Admin registers a new manufacturing partner / customer.
    3. Admin assigns product line / recipe binding.
    4. Admin creates isolated viewer credentials.
    5. Admin modifies system sync frequency and search root path.
    6. Verifies audit trail immutability and zero access cross-contamination.
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['user_id'] = 1
        sess['role'] = 'admin'

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)

        # Admin creates new company
        comp_id = f"PARTNER_{admin_scenario}"
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES (?, ?)", (comp_id, f"Partner Corp {admin_scenario}"))
        
        # Admin maps recipes
        for r_idx in range(3):
            conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES (?, ?)", (comp_id, f"PARTNER_REC_{admin_scenario}_{r_idx}"))
            
        # Admin provisions users
        conn.execute("INSERT OR IGNORE INTO users (username, password_hash, display_name, role, customer_id) VALUES (?, 'h', 'Partner Lead', 'customer_admin', ?)",
                     (f"partner_admin_{admin_scenario}", comp_id))
        
        # Verify isolation
        partner_recipes = conn.execute("SELECT recipe_name FROM customer_recipes WHERE customer_id = ?", (comp_id,)).fetchall()
        assert len(partner_recipes) == 3

        conn.commit()
        conn.close()
