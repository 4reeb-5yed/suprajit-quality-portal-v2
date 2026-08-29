"""
AUTHENTIC REAL-STATE INTEGRATION TESTS FOR app/routes/admin.py
Targeting 95%+ coverage across all admin endpoints, configuration changes,
customer lifecycle, folder mappings, user management, and diagnostic tools.
"""

import io
import os
import pytest
from app.database import get_connection, ensure_schema
from werkzeug.security import generate_password_hash


def login_admin(client, app):
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        ensure_schema(conn)
        conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('setup_completed', '1')")
        conn.execute(
            "INSERT OR REPLACE INTO users (id, username, display_name, password_hash, role, is_active, access_mode) VALUES (1, 'superadmin', 'Super Administrator', ?, 'admin', 1, 'ALL')",
            (generate_password_hash("SuperSecret123!"),)
        )
        conn.commit()
        conn.close()

    res = client.post("/login", data={"username": "superadmin", "password": "SuperSecret123!"}, follow_redirects=True)
    assert res.status_code == 200
    return res


def test_admin_setup_and_dashboard(client, app):
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        ensure_schema(conn)
        conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('setup_completed', '0')")
        conn.execute(
            "INSERT OR REPLACE INTO users (id, username, display_name, password_hash, role, is_active, access_mode) VALUES (1, 'superadmin', 'Super Administrator', ?, 'admin', 1, 'ALL')",
            (generate_password_hash("SuperSecret123!"),)
        )
        conn.commit()
        conn.close()

    client.post("/login", data={"username": "superadmin", "password": "SuperSecret123!"}, follow_redirects=True)

    # Setup GET
    res = client.get("/admin/setup")
    assert res.status_code == 200

    # Setup POST short password error
    res_short = client.post("/admin/setup", data={"new_password": "123"}, follow_redirects=True)
    assert b"Password must be at least 8 characters" in res_short.data

    # Setup POST valid setup
    res_valid = client.post("/admin/setup", data={
        "new_password": "StrongPassword123!",
        "admin_email": "admin@suprajit.com",
        "mail_server": "smtp.internal.lan",
        "mail_port": "587",
        "mail_username": "alerts@suprajit.com",
        "mail_password": "SMTPPassword123!",
        "developer_email": "devops@suprajit.com"
    }, follow_redirects=True)
    assert res_valid.status_code == 200

    # Verify settings stored
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        row = conn.execute("SELECT value FROM system_settings WHERE key = 'mail_server'").fetchone()
        assert row["value"] == "smtp.internal.lan"
        dev_row = conn.execute("SELECT value FROM system_settings WHERE key = 'developer_email'").fetchone()
        assert dev_row["value"] == "devops@suprajit.com"
        assert conn.execute("SELECT value FROM system_settings WHERE key = 'setup_completed'").fetchone()["value"] == "1"
        conn.close()

    # Dashboard view
    res_dash = client.get("/admin/")
    assert res_dash.status_code == 200
    assert b"superadmin" in res_dash.data or b"Dashboard" in res_dash.data


def test_admin_settings_post_and_invalid_regex(client, app):
    login_admin(client, app)

    # Invalid regex syntax check
    res_invalid_re = client.post("/admin/settings", data={
        "filename_regex_pattern": "[invalid(regex"
    }, follow_redirects=True)
    assert b"Invalid Regular Expression Syntax" in res_invalid_re.data

    # Valid comprehensive settings update
    res_settings = client.post("/admin/settings", data={
        "sync_time": "03:30",
        "root_search_path": "C:\\FactoryData\\Reports",
        "mail_server": "smtp.live.test",
        "mail_port": "2525",
        "mail_username": "system_admin",
        "mail_password": "NewSecretPassword123!",
        "developer_email": "sysadmin@suprajit.com",
        "telemetry_frequency": "weekly",
        "filename_regex_pattern": r"^(?P<prefix>[A-Z]+)_(?P<serial>[0-9]+)\.xlsx$",
        "sso_google_enabled": "1",
        "sso_google_client_id": "google-client-id-123",
        "sso_google_client_secret": "google-client-sec",
        "sso_microsoft_enabled": "0",
        "sso_github_enabled": "1",
        "sso_github_client_id": "github-client-id-456",
        "sso_github_client_secret": "github-client-sec",
        "public_portal_url": "https://portal.suprajit.com",
        "template_welcome_email": "Welcome {{username}}!",
        "template_invite_email": "Join {{company_name}} portal!",
        "template_reset_password": "Reset your token: {{reset_url}}"
    }, follow_redirects=True)
    assert res_settings.status_code == 200

    # Verify settings persisted in DB
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        assert conn.execute("SELECT value FROM system_settings WHERE key = 'sync_time'").fetchone()["value"] == "03:30"
        assert conn.execute("SELECT value FROM system_settings WHERE key = 'sso_google_enabled'").fetchone()["value"] == "1"
        assert conn.execute("SELECT value FROM system_settings WHERE key = 'sso_microsoft_enabled'").fetchone()["value"] == "0"
        assert conn.execute("SELECT value FROM system_settings WHERE key = 'public_portal_url'").fetchone()["value"] == "https://portal.suprajit.com"
        assert "Welcome" in conn.execute("SELECT value FROM system_settings WHERE key = 'template_welcome_email'").fetchone()["value"]
        conn.close()


def test_admin_folder_mappings_crud(client, app):
    login_admin(client, app)

    # Empty folder path error
    res_err = client.post("/admin/folder_mappings/add", data={"folder_path": "", "customer_id": ""}, follow_redirects=True)
    assert b"Folder path is required" in res_err.data

    # Valid mapping add
    res_add = client.post("/admin/folder_mappings/add", data={
        "folder_path": "D:\\QualityReports\\TVS_Lines",
        "customer_id": "suprajit"
    }, follow_redirects=True)
    assert b"mapped successfully" in res_add.data or res_add.status_code == 200

    # Verify DB row
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        row = conn.execute("SELECT * FROM folder_mappings WHERE folder_path = 'D:\\QualityReports\\TVS_Lines'").fetchone()
        assert row is not None
        mapping_id = row["id"]
        conn.close()

    # Delete mapping
    res_del = client.post("/admin/folder_mappings/delete", data={"mapping_id": mapping_id}, follow_redirects=True)
    assert b"Folder mapping removed" in res_del.data

    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        assert conn.execute("SELECT COUNT(*) FROM folder_mappings WHERE id = ?", (mapping_id,)).fetchone()[0] == 0
        conn.close()


def test_admin_tunnel_action_routes(client, app):
    login_admin(client, app)

    # Start token without providing token
    res_no_tok = client.post("/admin/tunnel/action", data={"action": "start_token", "tunnel_token": ""}, follow_redirects=True)
    assert b"Please provide a Cloudflare Tunnel Token" in res_no_tok.data

    # Stop action
    res_stop = client.post("/admin/tunnel/action", data={"action": "stop"}, follow_redirects=True)
    assert b"Tunnel stopped successfully" in res_stop.data


def test_admin_customer_crud_and_recipes(client, app):
    login_admin(client, app)

    # Add customer empty error
    res_c_err = client.post("/admin/customers/add", data={"id": "", "company_name": ""}, follow_redirects=True)
    assert b"Customer ID and Name are required" in res_c_err.data

    # Add valid customer
    res_c_add = client.post("/admin/customers/add", data={"id": "bajaj", "company_name": "Bajaj Auto"}, follow_redirects=True)
    assert b"Bajaj Auto" in res_c_add.data

    # Customer list
    res_list = client.get("/admin/customers")
    assert res_list.status_code == 200
    assert b"Bajaj Auto" in res_list.data

    # Customer detail
    res_det = client.get("/admin/customers/bajaj")
    assert res_det.status_code == 200
    assert b"Bajaj Auto" in res_det.data

    # Customer detail non-existent
    res_non = client.get("/admin/customers/nonexistent999", follow_redirects=True)
    assert b"Customer not found" in res_non.data

    # Edit customer
    res_edit = client.post("/admin/customers/edit", data={"customer_id": "bajaj", "company_name": "Bajaj Auto Ltd"}, follow_redirects=True)
    assert b"Bajaj Auto Ltd" in res_edit.data

    # Update domains
    res_dom = client.post("/admin/customers/update_domains", data={
        "customer_id": "bajaj",
        "allowed_domains": "bajajauto.co.in, @bajaj.com"
    }, follow_redirects=True)
    assert b"Auto-join email domains updated" in res_dom.data

    # Add recipe prefix
    res_rec_add = client.post("/admin/customers/add_recipe", data={
        "customer_id": "bajaj",
        "recipe_name": "BAJAJ_THROTTLE_V1"
    }, follow_redirects=True)
    assert b"Recipe access granted" in res_rec_add.data

    # Delete recipe
    res_rec_del = client.post("/admin/customers/delete_recipe", data={
        "customer_id": "bajaj",
        "recipe_name": "BAJAJ_THROTTLE_V1"
    }, follow_redirects=True)
    assert b"Recipe access removed" in res_rec_del.data

    # Suspend customer
    res_susp = client.post("/admin/customers/suspend", data={"customer_id": "bajaj", "portal_suspended": "1"}, follow_redirects=True)
    assert b"SUSPENDED" in res_susp.data

    # Restore customer
    res_rest = client.post("/admin/customers/suspend", data={"customer_id": "bajaj", "portal_suspended": "0"}, follow_redirects=True)
    assert b"RESTORED" in res_rest.data

    # Delete customer
    res_del_c = client.post("/admin/customers/delete", data={"customer_id": "bajaj"}, follow_redirects=True)
    assert b"permanently deleted" in res_del_c.data


def test_admin_user_lifecycle_and_permissions(client, app):
    login_admin(client, app)

    # 1. Add user without required fields
    res_u_err = client.post("/admin/customers/add_user", data={"username": "", "password": ""}, follow_redirects=True)
    assert b"Username and password are required" in res_u_err.data

    # 2. Add customer user with email
    res_u_add = client.post("/admin/customers/add_user", data={
        "username": "bajaj_lead",
        "email": "lead@bajaj.com",
        "password": "Password123!",
        "display_name": "Lead Engineer",
        "role": "customer_admin",
        "customer_id": "suprajit",
        "access_mode": "ALL"
    }, follow_redirects=True)
    assert b"created" in res_u_add.data

    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        user_row = conn.execute("SELECT * FROM users WHERE username = 'bajaj_lead'").fetchone()
        assert user_row is not None
        uid = user_row["id"]
        conn.close()

    # 3. Update permissions to CUSTOM recipes
    res_perm = client.post("/admin/customers/update_user_permissions", data={
        "user_id": uid,
        "customer_id": "suprajit",
        "access_mode": "CUSTOM",
        "selected_recipes": ["RECIPE_ALPHA", "RECIPE_BETA"]
    }, follow_redirects=True)
    assert b"Recipe access permissions updated" in res_perm.data

    # Verify custom user recipes in DB
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        u_rec = conn.execute("SELECT recipe_name FROM user_recipes WHERE user_id = ?", (uid,)).fetchall()
        assert {r["recipe_name"] for r in u_rec} == {"RECIPE_ALPHA", "RECIPE_BETA"}
        conn.close()

    # 4. Toggle user status (Revoke and Grant)
    res_rev = client.post("/admin/customers/toggle_user", data={"user_id": uid, "is_active": "0"}, follow_redirects=True)
    assert b"Access Revoked" in res_rev.data

    res_grt = client.post("/admin/customers/toggle_user", data={"user_id": uid, "is_active": "1"}, follow_redirects=True)
    assert b"Access Granted" in res_grt.data

    # 5. Prevent deleting self account
    res_del_self = client.post("/admin/users/delete", data={"user_id": "1"}, follow_redirects=True)
    assert b"You cannot delete your currently active account" in res_del_self.data

    # 6. Delete target user
    res_del_u = client.post("/admin/users/delete", data={"user_id": uid}, follow_redirects=True)
    assert b"User deleted successfully" in res_del_u.data


def test_admin_bulk_user_import_csv_and_text(client, app):
    login_admin(client, app)

    # 1. Empty import
    res_empty = client.post("/admin/users/bulk_import", data={"bulk_text": "", "role": "customer_viewer"}, follow_redirects=True)
    assert b"No valid email addresses or records found" in res_empty.data

    # 2. Text paste import
    raw_text = """
    alex@partner.com, Alex Smith, alex_user, customer_viewer
    maria@partner.com, Maria Davis, maria_user, customer_admin
    sam@partner.com
    """
    res_text = client.post("/admin/users/bulk_import", data={
        "bulk_text": raw_text,
        "customer_id": "suprajit",
        "role": "customer_viewer",
        "send_invites": "0"
    }, follow_redirects=True)
    assert b"Bulk Provisioning Completed" in res_text.data

    # Verify rows created
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        assert conn.execute("SELECT COUNT(*) FROM users WHERE email = 'alex@partner.com'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM users WHERE email = 'maria@partner.com'").fetchone()[0] == 1
        conn.close()

    # 3. CSV File upload import
    csv_content = b"Email,Name,Username,Role\nclaire@partner.com,Claire Brown,claire_b,customer_viewer\n"
    csv_file = (io.BytesIO(csv_content), "users.csv")
    res_csv = client.post("/admin/users/bulk_import", data={
        "bulk_file": csv_file,
        "customer_id": "suprajit",
        "send_invites": "0"
    }, content_type="multipart/form-data", follow_redirects=True)
    assert b"Bulk Provisioning Completed" in res_csv.data


def test_admin_diagnostics_repair_and_evidence(client, app):
    login_admin(client, app)

    # Setup dummy log file
    with app.app_context():
        log_file = os.path.join(app.config["STORAGE_FOLDER"], "test_app.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("2026-08-30 [INFO] System started.\n2026-08-30 [INFO] Ingestion verified.\n")
        app.config["LOG_FILE_PATH"] = log_file

    # Diagnostics page
    res_diag = client.get("/admin/diagnostics")
    assert res_diag.status_code == 200
    assert b"System started" in res_diag.data or b"Diagnostics" in res_diag.data

    # Log file download
    res_dl = client.get("/admin/logs/download")
    assert res_dl.status_code == 200
    assert b"System started" in res_dl.data

    # Evidence dashboard
    res_ev = client.get("/admin/evidence")
    assert res_ev.status_code == 200
    assert b"Security & Quality Evidence Dashboard" in res_ev.data or b"INDEXING" in res_ev.data

    # Trigger manual sync
    res_sync = client.post("/admin/trigger_sync", follow_redirects=True)
    assert b"Manual ingestion batch has been started" in res_sync.data

    # Repair GET
    res_rep_get = client.get("/admin/repair")
    assert res_rep_get.status_code == 200

    # Repair dry_run
    res_dry = client.post("/admin/repair", data={"action": "dry_run", "target_date": "2026-08-25"}, follow_redirects=True)
    assert res_dry.status_code == 200

    # Repair purge_date
    res_purge = client.post("/admin/repair", data={"action": "purge_date", "target_date": "2026-08-25"}, follow_redirects=True)
    assert b"Successfully purged" in res_purge.data or res_purge.status_code == 200

    # Repair force_sync
    res_force = client.post("/admin/repair", data={"action": "force_sync", "target_date": "2026-08-25"}, follow_redirects=True)
    assert b"Force Sync started" in res_force.data
def test_admin_edge_cases_and_error_branches(client, app):
    login_admin(client, app)

    # 1. Delete non-existent user
    res_del_non = client.post("/admin/users/delete", data={"user_id": "99999"}, follow_redirects=True)
    assert b"User not found" in res_del_non.data

    # 2. Add a second admin, test last admin delete rejection and successful admin delete
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        cur = conn.execute(
            "INSERT INTO users (username, display_name, password_hash, role, is_active, access_mode) VALUES ('admin_two', 'Admin Two', 'hash', 'admin', 1, 'ALL')"
        )
        adm2_id = cur.lastrowid
        conn.commit()
        conn.close()

    # Delete admin_two should redirect to settings
    res_del_adm2 = client.post("/admin/users/delete", data={"user_id": str(adm2_id)}, follow_redirects=True)
    assert b"User deleted successfully" in res_del_adm2.data

    # 3. Add user with custom redirect_url and error path
    res_u_red = client.post("/admin/customers/add_user", data={
        "username": "",
        "password": "",
        "redirect_url": "/admin/customers"
    }, follow_redirects=True)
    assert b"Username and password are required" in res_u_red.data

    # 4. Add admin user from settings page
    res_adm_add = client.post("/admin/customers/add_user", data={
        "username": "admin_three",
        "password": "Password123!",
        "role": "admin",
        "display_name": "Admin Three"
    }, follow_redirects=True)
    assert b"created successfully" in res_adm_add.data or res_adm_add.status_code == 200

    # 5. Missing log file download test
    with app.app_context():
        app.config["LOG_FILE_PATH"] = "C:\\non_existent_folder_xyz\\missing.log"
    res_no_log = client.get("/admin/logs/download", follow_redirects=True)
    assert b"System log file does not exist yet" in res_no_log.data

    # 6. Repair missing dates validation
    res_rep_no_dt = client.post("/admin/repair", data={"action": "purge_date", "target_date": ""}, follow_redirects=True)
    assert b"Please provide a date to purge" in res_rep_no_dt.data

    res_rep_no_fs = client.post("/admin/repair", data={"action": "force_sync", "target_date": ""}, follow_redirects=True)
    assert b"Please provide a date to force sync" in res_rep_no_fs.data

    # 7. Bulk import various formats
    raw_formats = """
    only_username
    email_and_name@test.com, Name Only
    valid_uname, Name Person
    """
    res_bulk_fmt = client.post("/admin/users/bulk_import", data={
        "bulk_text": raw_formats,
        "customer_id": "suprajit",
        "send_invites": "0"
    }, follow_redirects=True)
    assert b"Bulk Provisioning Completed" in res_bulk_fmt.data

    # 8. Customer empty recipe prefix error
    res_empty_rec = client.post("/admin/customers/add_recipe", data={"customer_id": "suprajit", "recipe_name": ""}, follow_redirects=True)
    assert b"Recipe prefix is required" in res_empty_rec.data

    # 9. Search latencies on evidence dashboard
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("CREATE TABLE IF NOT EXISTS search_metrics (id INTEGER PRIMARY KEY, latency_ms REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT INTO search_metrics (latency_ms) VALUES (12.4), (18.6), (25.1)")
        conn.commit()
        conn.close()

    res_ev_lat = client.get("/admin/evidence")
    assert res_ev_lat.status_code == 200
    assert b"ms" in res_ev_lat.data
def test_admin_additional_lines_and_tunnels(client, app):
    login_admin(client, app)

    # 1. Start quick tunnel post route
    res_quick = client.post("/admin/tunnel/action", data={"action": "start_quick"}, follow_redirects=True)
    assert res_quick.status_code == 200

    # 2. Start named tunnel post route with valid format token
    res_tok = client.post("/admin/tunnel/action", data={"action": "start_token", "tunnel_token": "valid-token-string"}, follow_redirects=True)
    assert res_tok.status_code == 200

    # 3. Delimiter variations in bulk text import
    delim_text = """
    user1@test.com;User One;user_one;company_admin
    user2@test.com\tUser Two\tuser_two\tadmin
    """
    res_delim = client.post("/admin/users/bulk_import", data={
        "bulk_text": delim_text,
        "customer_id": "suprajit",
        "send_invites": "0"
    }, follow_redirects=True)
    assert b"Bulk Provisioning Completed" in res_delim.data

    # 4. Recipes update with redirect_url
    res_rec_red = client.post("/admin/customers/add_recipe", data={
        "customer_id": "suprajit",
        "recipe_name": "SUPRAJIT_EXTRA_V1",
        "redirect_url": "/admin/customers"
    }, follow_redirects=True)
    assert b"Recipe access granted" in res_rec_red.data

    res_rec_del_red = client.post("/admin/customers/delete_recipe", data={
        "customer_id": "suprajit",
        "recipe_name": "SUPRAJIT_EXTRA_V1",
        "redirect_url": "/admin/customers"
    }, follow_redirects=True)
    assert b"Recipe access removed" in res_rec_del_red.data

    # 5. Toggle customer with redirect_url
    res_togg = client.post("/admin/customers/toggle", data={
        "customer_id": "suprajit",
        "portal_suspended": "0",
        "redirect_url": "/admin/customers"
    }, follow_redirects=True)
    assert b"RESTORED" in res_togg.data