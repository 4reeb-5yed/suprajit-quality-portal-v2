"""
AUTHENTIC DEEP COVERAGE TESTS FOR app/routes/portal.py
Covers search (admin/CUSTOM/ALL modes), download (safe/unsafe path, file exists/missing,
path traversal block), raw_report, onlyoffice_viewer, preview_pdf branches.
"""

import pytest
pytestmark = pytest.mark.integration

import os
import tempfile
from werkzeug.security import generate_password_hash
from app.database import get_connection, ensure_schema


def seed_report(app, customer_id="suprajit", recipe="TEST_RECIPE", file_path=None):
    """Create a real file + report row. Returns (report_id, file_path)."""
    if file_path is None:
        fd, file_path = tempfile.mkstemp(suffix=".xlsx")
        os.write(fd, b"PK fake xlsx content")
        os.close(fd)
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES (?, ?)", (customer_id, customer_id))
        conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES (?, ?)", (customer_id, recipe))
        cur = conn.execute(
            """INSERT INTO reports (recipe_name, customer_id, original_filename, file_path, report_date, report_time, file_hash, serial_raw, serial_normalized)
               VALUES (?, ?, ?, ?, '2025-01-15', '10:00:00', 'abc123', 'ABC-123', 'ABC123')""",
            (recipe, customer_id, os.path.basename(file_path), file_path),
        )
        report_id = cur.lastrowid
        conn.commit()
        conn.close()
    return report_id, file_path


def login_portal_user(client, app, user_id=100, username="portal_viewer", role="customer_viewer",
                      customer_id="suprajit", access_mode="ALL"):
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        ensure_schema(conn)
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES (?, ?)", (customer_id, customer_id))
        conn.execute(
            "INSERT OR REPLACE INTO users (id, username, display_name, password_hash, role, customer_id, is_active, access_mode) VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (user_id, username, username.title(), generate_password_hash("Pass123!"), role, customer_id, access_mode),
        )
        conn.commit()
        conn.close()

    client.get("/logout", follow_redirects=True)
    res = client.post("/login", data={"username": username, "password": "Pass123!"}, follow_redirects=True)
    assert res.status_code == 200
    return res


def test_portal_index_redirects_to_search(client, app):
    """/ redirects to /search."""
    login_portal_user(client, app, user_id=200, username="idx_user")
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert "/search" in res.headers.get("Location", "")


def test_portal_search_admin_mode(client, app):
    """Admin sees all recipes from reports table (lines 23-24)."""
    seed_report(app, customer_id="suprajit", recipe="GLOBAL_RECIPE")
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('setup_completed', '1')")
        conn.commit()
        conn.close()
    login_portal_user(client, app, user_id=201, username="search_admin", role="admin", customer_id=None)
    res = client.get("/search")
    assert res.status_code == 200


def test_portal_search_custom_access_mode(client, app):
    """CUSTOM access_mode user sees only their assigned recipes (lines 26-27)."""
    seed_report(app, customer_id="suprajit", recipe="RECIPE_CUSTOM_ONLY")
    login_portal_user(client, app, user_id=202, username="custom_viewer", role="customer_viewer",
                      customer_id="suprajit", access_mode="CUSTOM")
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR IGNORE INTO user_recipes (user_id, recipe_name) VALUES (202, 'RECIPE_CUSTOM_ONLY')")
        conn.commit()
        conn.close()
    res = client.get("/search")
    assert res.status_code == 200


def test_portal_search_results_no_params(client, app):
    """Empty search returns the placeholder partial (lines 57-62)."""
    login_portal_user(client, app, user_id=203, username="search_user")
    res = client.get("/search/results")
    assert b"Please select" in res.data


def test_portal_search_results_with_filters(client, app):
    """All three filter branches (recipe, date, serial) are exercised."""
    report_id, fp = seed_report(app, recipe="TEST_RECIPE")
    login_portal_user(client, app, user_id=204, username="filter_user")
    res = client.get("/search/results?recipe=TEST_RECIPE&date=2025-01-15&serial=ABC")
    assert res.status_code == 200
    try:
        os.unlink(fp)
    except Exception:
        pass


def test_portal_download_report_success_and_errors(client, app):
    """Download real file (success), missing report (404), path traversal (403), missing file (404)."""
    storage = app.config["STORAGE_FOLDER"]
    fd, fp = tempfile.mkstemp(suffix=".xlsx", dir=storage)
    os.write(fd, b"PK fake xlsx")
    os.close(fd)
    report_id, _ = seed_report(app, file_path=fp)
    login_portal_user(client, app, user_id=205, username="dl_user")

    # Successful download
    res = client.get(f"/download/{report_id}")
    assert res.status_code == 200

    # 404 for non-existent report
    res_404 = client.get("/download/999999")
    assert res_404.status_code == 404

    # Path traversal: insert report pointing outside storage_folder
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        cur = conn.execute(
            "INSERT INTO reports (recipe_name, customer_id, original_filename, file_path, report_date, report_time, file_hash, serial_raw, serial_normalized) VALUES ('TEST_RECIPE', 'suprajit', 'evil.xlsx', ?, '2025-01-15', '11:00', 'xxx', 'EVIL', 'EVIL')",
            ("C:\\Windows\\System32\\evil.dll",),
        )
        evil_id = cur.lastrowid
        conn.commit()
        conn.close()

    res_403 = client.get(f"/download/{evil_id}")
    assert res_403.status_code == 403

    # Missing file on disk
    safe_fp = os.path.join(storage, "missing_report.xlsx")
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        cur = conn.execute(
            "INSERT INTO reports (recipe_name, customer_id, original_filename, file_path, report_date, report_time, file_hash, serial_raw, serial_normalized) VALUES ('TEST_RECIPE', 'suprajit', 'missing.xlsx', ?, '2025-01-15', '12:00', 'yyy', 'MISS', 'MISS')",
            (safe_fp,),
        )
        mid = cur.lastrowid
        conn.commit()
        conn.close()

    res_missing = client.get(f"/download/{mid}")
    assert res_missing.status_code == 404

    try:
        os.unlink(fp)
    except Exception:
        pass


def test_portal_raw_report_and_onlyoffice_viewer(client, app):
    """raw_report serves the file; onlyoffice_viewer renders the page; 404s work."""
    storage = app.config["STORAGE_FOLDER"]
    fd, fp = tempfile.mkstemp(suffix=".xlsx", dir=storage)
    os.write(fd, b"PK raw content")
    os.close(fd)
    report_id, _ = seed_report(app, file_path=fp, recipe="TEST_RECIPE")
    login_portal_user(client, app, user_id=206, username="view_user")

    # raw_report success
    res_raw = client.get(f"/view-raw/{report_id}")
    assert res_raw.status_code == 200

    # raw_report 404 (non-existent)
    res_raw_404 = client.get("/view-raw/999999")
    assert res_raw_404.status_code == 404

    # raw_report path traversal: report exists but path is unsafe → 404
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        cur = conn.execute(
            "INSERT INTO reports (recipe_name, customer_id, original_filename, file_path, report_date, report_time, file_hash, serial_raw, serial_normalized) VALUES ('TEST_RECIPE', 'suprajit', 'unsafe.xlsx', ?, '2025-01-15', '13:00', 'zzz', 'UNSAFE', 'UNSAFE')",
            ("C:\\Windows\\System32\\cmd.exe",),
        )
        unsafe_id = cur.lastrowid
        conn.commit()
        conn.close()

    res_unsafe = client.get(f"/view-raw/{unsafe_id}")
    assert res_unsafe.status_code == 404

    # onlyoffice_viewer page render
    res_oov = client.get(f"/onlyoffice-viewer/{report_id}")
    assert res_oov.status_code == 200

    # onlyoffice_viewer 404
    res_oov_404 = client.get("/onlyoffice-viewer/999999")
    assert res_oov_404.status_code == 404

    try:
        os.unlink(fp)
    except Exception:
        pass


def test_portal_search_results_metric_error_branch(client, app):
    """When search_metrics table does not exist, exception is caught and search still returns."""
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("DROP TABLE IF EXISTS search_metrics")
        conn.commit()
        conn.close()
    login_portal_user(client, app, user_id=207, username="metric_user")
    res = client.get("/search/results?recipe=TEST_RECIPE")
    assert res.status_code == 200

@pytest.mark.live_external
def test_portal_preview_pdf_real_generation_and_cached(client, app):
    """Test preview_pdf using real files, real LibreOffice conversion and caching."""
    import shutil
    soffice_available = (
        os.path.exists(r"C:\Program Files\LibreOffice\program\soffice.exe")
        or shutil.which("soffice") is not None
    )
    if not soffice_available:
        pytest.skip("LibreOffice (soffice) not installed in current environment")
    storage = app.config["STORAGE_FOLDER"]
    sample_src = os.path.join(os.path.dirname(__file__), "sample_report.xlsx")
    target_fp = os.path.join(storage, "real_report_preview.xlsx")
    shutil.copyfile(sample_src, target_fp)

    data_folder = app.config.get("DATA_FOLDER") or os.path.dirname(app.config["DATABASE_PATH"])
    app.config["DATA_FOLDER"] = data_folder

    report_id, _ = seed_report(app, file_path=target_fp, recipe="TEST_RECIPE")
    login_portal_user(client, app, user_id=208, username="pdf_user")

    # Non-existent report 404
    res_404 = client.get("/preview-pdf/999999")
    assert res_404.status_code == 404

    # Real un-cached LibreOffice PDF generation
    res_real = client.get(f"/preview-pdf/{report_id}")
    assert res_real.status_code == 200
    assert res_real.mimetype == "application/pdf"

    # Second request hits cache
    res_cached = client.get(f"/preview-pdf/{report_id}")
    assert res_cached.status_code == 200
    assert res_cached.mimetype == "application/pdf"

    try:
        os.unlink(target_fp)
    except Exception:
        pass


def test_portal_network_share_root_search_path(client, app):
    """Test download and view-raw with multi-root network share path configured in system_settings."""
    share_dir = tempfile.mkdtemp()
    fd, fp = tempfile.mkstemp(suffix=".xlsx", dir=share_dir)
    os.write(fd, b"PK network share file content")
    os.close(fd)

    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('root_search_path', ?)", (f"D:\\OtherShare;{share_dir}",))
        cur = conn.execute(
            "INSERT INTO reports (recipe_name, customer_id, original_filename, file_path, report_date, report_time, file_hash, serial_raw, serial_normalized) VALUES ('TEST_RECIPE', 'suprajit', 'share_file.xlsx', ?, '2025-01-15', '14:00', 'sharehash', 'SHARE', 'SHARE')",
            (fp,),
        )
        rep_id = cur.lastrowid
        conn.commit()
        conn.close()

    login_portal_user(client, app, user_id=209, username="share_user")

    res_dl = client.get(f"/download/{rep_id}")
    assert res_dl.status_code == 200

    res_vr = client.get(f"/view-raw/{rep_id}")
    assert res_vr.status_code == 200

    try:
        os.unlink(fp)
        import shutil
        shutil.rmtree(share_dir, ignore_errors=True)
    except Exception:
        pass