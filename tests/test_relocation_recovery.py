import os
import shutil
import pytest
from app.sync_engine import SyncEngine

pytestmark = pytest.mark.integration


def test_file_relocation_in_sync_engine_and_portal(app, client):
    """
    Verifies that when an indexed file is moved to another folder:
    1. The sync engine detects the identical hash and updates reports.file_path.
    2. The portal dynamically locates the moved file on download/view and serves it cleanly.
    """
    with app.app_context():
        folder_a = os.path.join(app.config["STORAGE_FOLDER"], "folder_a")
        folder_b = os.path.join(app.config["STORAGE_FOLDER"], "folder_b")
        os.makedirs(folder_a, exist_ok=True)
        os.makedirs(folder_b, exist_ok=True)

        from app.database import get_connection

        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('tvs', 'TVS Motors')")
        conn.commit()
        conn.close()

        engine = SyncEngine(app.config["DATABASE_PATH"], app.config["STORAGE_FOLDER"])
        engine._get_folder_customer_mapping = lambda: {folder_a: "tvs", folder_b: "tvs"}

        # 1. Place file in folder_a and index it
        file_a = os.path.join(folder_a, "EV_TPS_20-08-2026_10.00.00_001.xlsx")
        with open(file_a, "w") as f:
            f.write("RELOCATION_TEST_CONTENT_12345")

        inserted = engine.run_batch(full_sync=True)
        assert inserted == 1

        from app.database import get_connection

        conn = get_connection(app.config["DATABASE_PATH"])
        row = conn.execute("SELECT * FROM reports WHERE original_filename = 'EV_TPS_20-08-2026_10.00.00_001.xlsx'").fetchone()
        assert row is not None
        assert row["file_path"] == file_a
        report_id = row["id"]
        conn.close()

        # 2. Move file from folder_a to folder_b
        file_b = os.path.join(folder_b, "EV_TPS_20-08-2026_10.00.00_001.xlsx")
        shutil.move(file_a, file_b)
        assert not os.path.exists(file_a)
        assert os.path.exists(file_b)

        # 3. Log in as admin
        client.post("/login", data={"username": "bootstrap_admin", "password": "admin123"}, follow_redirects=True)

        # 4. Download file - portal should automatically locate it in folder_b
        dl_res = client.get(f"/download/{report_id}")
        assert dl_res.status_code == 200
        assert b"RELOCATION_TEST_CONTENT_12345" in dl_res.data
        dl_res.close()

        # Verify database path was updated
        conn = get_connection(app.config["DATABASE_PATH"])
        row_updated = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        assert row_updated["file_path"] == file_b
        conn.close()

        # 5. Move file to another subfolder and run sync engine batch
        folder_c = os.path.join(folder_b, "sub_archive")
        os.makedirs(folder_c, exist_ok=True)
        file_c = os.path.join(folder_c, "EV_TPS_20-08-2026_10.00.00_001.xlsx")
        shutil.move(file_b, file_c)

        engine._get_folder_customer_mapping = lambda: {folder_a: "tvs", folder_b: "tvs", folder_c: "tvs"}
        engine.run_batch(full_sync=True)

        conn = get_connection(app.config["DATABASE_PATH"])
        row_batch_updated = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        assert row_batch_updated["file_path"] == file_c
        conn.close()
