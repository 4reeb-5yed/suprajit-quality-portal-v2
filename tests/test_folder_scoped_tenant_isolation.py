"""
TENANT ISOLATION ARCHITECTURE REGRESSION TESTS (FOLDER-SCOPED INGESTION & STORED CUSTOMER_ID)

Proves:
1. Two customers can each have the identically-named recipe (e.g. 'THROTTLE_V1') in customer_recipes without error.
2. Ingestion stamps reports.customer_id based on folder_mappings.
3. A file in an unmapped folder ingests as customer_id = NULL and is invisible to all tenant searches.
4. Reports ingested for Customer A are only visible to Customer A, even if Customer B shares the same recipe name.
5. Reassigning or editing customer_recipes does NOT retroactively change reports.customer_id on existing rows.
6. customer_scope() filters strictly on reports.customer_id, ignoring mismatched customer_recipes live state.
"""

import os
import pytest
from app import create_app
from app.database import get_connection, ensure_schema
from app.helpers import customer_scope
from app.auth_models import User
from app.sync_engine import SyncEngine

@pytest.fixture
def tenant_env(tmp_path):
    db_path = str(tmp_path / "test_tenant.db")
    storage_base = str(tmp_path / "storage")
    os.makedirs(storage_base, exist_ok=True)

    folder_tvs = str(tmp_path / "tvs_inbox")
    folder_mahindra = str(tmp_path / "mahindra_inbox")
    folder_unmapped = str(tmp_path / "unmapped_inbox")

    os.makedirs(folder_tvs, exist_ok=True)
    os.makedirs(folder_mahindra, exist_ok=True)
    os.makedirs(folder_unmapped, exist_ok=True)

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-tenant-secret-key-123",
        "DATABASE_PATH": db_path,
        "STORAGE_FOLDER": storage_base,
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        conn = get_connection(db_path)
        ensure_schema(conn)

        # 1. Seed customers
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('tvs', 'TVS Motor')")
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('mahindra', 'Mahindra Auto')")

        # 2. Seed identically named recipe across both customers (Composite PK allows this)
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'THROTTLE_V1')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('mahindra', 'THROTTLE_V1')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'TVS_EXCLUSIVE')")

        # 3. Seed folder mappings
        conn.execute("INSERT INTO folder_mappings (folder_path, customer_id) VALUES (?, 'tvs')", (folder_tvs,))
        conn.execute("INSERT INTO folder_mappings (folder_path, customer_id) VALUES (?, 'mahindra')", (folder_mahindra,))
        conn.execute("INSERT INTO folder_mappings (folder_path, customer_id) VALUES (?, NULL)", (folder_unmapped,))

        # 4. Seed users
        conn.execute("""
            INSERT INTO users (id, username, email, password_hash, display_name, role, customer_id, access_mode)
            VALUES (101, 'tvs_user', 'tvs@tvs.com', 'pwd', 'TVS User', 'customer_viewer', 'tvs', 'ALL')
        """)
        conn.execute("""
            INSERT INTO users (id, username, email, password_hash, display_name, role, customer_id, access_mode)
            VALUES (102, 'mahindra_user', 'm@m.com', 'pwd', 'Mahindra User', 'customer_viewer', 'mahindra', 'ALL')
        """)

        conn.commit()
        conn.close()

    return {
        "app": app,
        "db_path": db_path,
        "storage_base": storage_base,
        "folder_tvs": folder_tvs,
        "folder_mahindra": folder_mahindra,
        "folder_unmapped": folder_unmapped,
    }


def test_recipe_name_shared_across_multiple_customers(tenant_env):
    """
    Test 1: Proves customer_recipes allows the same recipe_name across different customers
    (composite PK (customer_id, recipe_name) allows collision without throwing UNIQUE error).
    """
    conn = get_connection(tenant_env["db_path"])
    rows = conn.execute("SELECT customer_id, recipe_name FROM customer_recipes WHERE recipe_name = 'THROTTLE_V1'").fetchall()
    conn.close()

    assert len(rows) == 2
    customers = {r["customer_id"] for r in rows}
    assert customers == {"tvs", "mahindra"}


def test_ingestion_binds_customer_from_source_folder(tenant_env):
    """
    Test 2: Proves ingestion stamps reports.customer_id based on folder_mappings.
    - TVS folder file -> customer_id = 'tvs'
    - Mahindra folder file -> customer_id = 'mahindra'
    - Unmapped folder file -> customer_id = NULL
    """
    f_tvs = os.path.join(tenant_env["folder_tvs"], "THROTTLE_V1_25-08-2026_10.00.00_0001.xlsx")
    f_mah = os.path.join(tenant_env["folder_mahindra"], "THROTTLE_V1_25-08-2026_10.00.00_0002.xlsx")
    f_unmapped = os.path.join(tenant_env["folder_unmapped"], "THROTTLE_V1_25-08-2026_10.00.00_0003.xlsx")

    with open(f_tvs, "wb") as fp:
        fp.write(b"PK\x03\x04MockExcelDataTVS")
    with open(f_mah, "wb") as fp:
        fp.write(b"PK\x03\x04MockExcelDataMahindra")
    with open(f_unmapped, "wb") as fp:
        fp.write(b"PK\x03\x04MockExcelDataUnmapped")

    engine = SyncEngine(tenant_env["db_path"], tenant_env["storage_base"])
    inserted = engine.run_batch(full_sync=True)
    assert inserted == 3

    conn = get_connection(tenant_env["db_path"])
    r1 = conn.execute("SELECT customer_id FROM reports WHERE original_filename = 'THROTTLE_V1_25-08-2026_10.00.00_0001.xlsx'").fetchone()
    r2 = conn.execute("SELECT customer_id FROM reports WHERE original_filename = 'THROTTLE_V1_25-08-2026_10.00.00_0002.xlsx'").fetchone()
    r3 = conn.execute("SELECT customer_id FROM reports WHERE original_filename = 'THROTTLE_V1_25-08-2026_10.00.00_0003.xlsx'").fetchone()
    conn.close()

    assert r1["customer_id"] == "tvs"
    assert r2["customer_id"] == "mahindra"
    assert r3["customer_id"] is None


def test_customer_scope_isolates_shared_recipe_reports(tenant_env):
    """
    Test 3: Both TVS and Mahindra have reports with recipe_name 'THROTTLE_V1'.
    customer_scope() for TVS user returns ONLY TVS report.
    customer_scope() for Mahindra user returns ONLY Mahindra report.
    Neither user sees the unmapped (customer_id = NULL) report.
    """
    # Ingest files first
    f_tvs = os.path.join(tenant_env["folder_tvs"], "THROTTLE_V1_25-08-2026_10.00.00_0001.xlsx")
    f_mah = os.path.join(tenant_env["folder_mahindra"], "THROTTLE_V1_25-08-2026_10.00.00_0002.xlsx")
    f_unmapped = os.path.join(tenant_env["folder_unmapped"], "THROTTLE_V1_25-08-2026_10.00.00_0003.xlsx")

    with open(f_tvs, "wb") as fp:
        fp.write(b"PK\x03\x04MockExcelDataTVS")
    with open(f_mah, "wb") as fp:
        fp.write(b"PK\x03\x04MockExcelDataMahindra")
    with open(f_unmapped, "wb") as fp:
        fp.write(b"PK\x03\x04MockExcelDataUnmapped")

    engine = SyncEngine(tenant_env["db_path"], tenant_env["storage_base"])
    engine.run_batch(full_sync=True)

    tvs_user = User({"id": 101, "username": "tvs_user", "email": "tvs@tvs.com", "display_name": "TVS User", "role": "customer_viewer", "customer_id": "tvs", "access_mode": "ALL", "is_active": 1})
    mah_user = User({"id": 102, "username": "mahindra_user", "email": "m@m.com", "display_name": "Mahindra User", "role": "customer_viewer", "customer_id": "mahindra", "access_mode": "ALL", "is_active": 1})

    where_tvs, params_tvs = customer_scope(tvs_user)
    where_mah, params_mah = customer_scope(mah_user)

    conn = get_connection(tenant_env["db_path"])
    tvs_reports = conn.execute(f"SELECT original_filename, customer_id FROM reports WHERE {where_tvs}", params_tvs).fetchall()
    mah_reports = conn.execute(f"SELECT original_filename, customer_id FROM reports WHERE {where_mah}", params_mah).fetchall()
    conn.close()

    # TVS user sees only TVS file
    assert len(tvs_reports) == 1
    assert tvs_reports[0]["original_filename"] == "THROTTLE_V1_25-08-2026_10.00.00_0001.xlsx"
    assert tvs_reports[0]["customer_id"] == "tvs"

    # Mahindra user sees only Mahindra file
    assert len(mah_reports) == 1
    assert mah_reports[0]["original_filename"] == "THROTTLE_V1_25-08-2026_10.00.00_0002.xlsx"
    assert mah_reports[0]["customer_id"] == "mahindra"


def test_customer_recipes_reassignment_does_not_retroactively_mutate_report_ownership(tenant_env):
    """
    Test 4: Proves editing customer_recipes or folder_mappings does NOT alter existing report.customer_id.
    """
    conn = get_connection(tenant_env["db_path"])
    conn.execute("""
        INSERT INTO reports (id, customer_id, recipe_name, report_date, serial_normalized, original_filename, file_path, file_hash)
        VALUES (99, 'tvs', 'TVS_EXCLUSIVE', '2026-08-25', '0099', 'TVS_EXCLUSIVE_25-08-2026_10.00.00_0099.xlsx', '/path/99', 'hash99')
    """)
    conn.commit()

    # Delete recipe from TVS and assign to Mahindra
    conn.execute("DELETE FROM customer_recipes WHERE customer_id = 'tvs' AND recipe_name = 'TVS_EXCLUSIVE'")
    conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('mahindra', 'TVS_EXCLUSIVE')")
    conn.commit()

    # Report row still has customer_id = 'tvs'
    row = conn.execute("SELECT customer_id FROM reports WHERE id = 99").fetchone()
    assert row["customer_id"] == "tvs"

    # Mahindra user still cannot see it because report.customer_id is 'tvs' (not 'mahindra')
    mah_user = User({"id": 102, "username": "mahindra_user", "email": "m@m.com", "display_name": "Mahindra User", "role": "customer_viewer", "customer_id": "mahindra", "access_mode": "ALL", "is_active": 1})
    where_mah, params_mah = customer_scope(mah_user)
    mah_visible = conn.execute(f"SELECT * FROM reports WHERE id = 99 AND {where_mah}", params_mah).fetchall()
    conn.close()

    assert len(mah_visible) == 0


def test_isolation_comes_from_stored_row_customer_id_spoof_resistance(tenant_env):
    """
    Test 5 (The strongest test): Seed a report directly with customer_id = 'tvs', but with recipe_name 'MAHINDRA_ONLY'.
    Even if customer_recipes says 'MAHINDRA_ONLY' is owned by 'mahindra', Mahindra user cannot see it,
    proving customer_scope() respects the stored customer_id on the row first.
    """
    conn = get_connection(tenant_env["db_path"])
    conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('mahindra', 'MAHINDRA_ONLY')")
    conn.execute("""
        INSERT INTO reports (id, customer_id, recipe_name, report_date, serial_normalized, original_filename, file_path, file_hash)
        VALUES (100, 'tvs', 'MAHINDRA_ONLY', '2026-08-25', '0100', 'MAHINDRA_ONLY_25-08-2026_10.00.00_0100.xlsx', '/path/100', 'hash100')
    """)
    conn.commit()

    mah_user = User({"id": 102, "username": "mahindra_user", "email": "m@m.com", "display_name": "Mahindra User", "role": "customer_viewer", "customer_id": "mahindra", "access_mode": "ALL", "is_active": 1})
    where_mah, params_mah = customer_scope(mah_user)
    mah_visible = conn.execute(f"SELECT * FROM reports WHERE id = 100 AND {where_mah}", params_mah).fetchall()
    conn.close()

    assert len(mah_visible) == 0
