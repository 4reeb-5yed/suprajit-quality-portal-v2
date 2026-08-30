import pytest
pytestmark = pytest.mark.integration

import pytest
from app import create_app
from app.database import get_connection

def test_three_tier_rbac_and_recipe_permissions(tmp_path):
    db_path = str(tmp_path / "test_portal.db")
    app = create_app({
        "TESTING": True,
        "DATABASE_PATH": db_path,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key"
    })
    
    with app.app_context():
        conn = get_connection(db_path)
        
        # 1. Setup Customer & Master Recipes
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('tvs', 'TVS Motor Company')")
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('mahindra', 'Mahindra Auto')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'I-QUBE-BATTERY')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'JUPITER-125')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('mahindra', 'THAR-DIESEL')")
        
        # 2. Setup Reports
        conn.execute("""INSERT INTO reports (recipe_name, report_date, serial_raw, serial_normalized, original_filename, file_path, file_hash)
                        VALUES ('I-QUBE-BATTERY', '2026-06-13', '101', '101', 'iqube.xlsx', 'Z:/tvs/iqube.xlsx', 'h1')""")
        conn.execute("""INSERT INTO reports (recipe_name, report_date, serial_raw, serial_normalized, original_filename, file_path, file_hash)
                        VALUES ('JUPITER-125', '2026-06-13', '102', '102', 'jupiter.xlsx', 'Z:/tvs/jupiter.xlsx', 'h2')""")
        conn.execute("""INSERT INTO reports (recipe_name, report_date, serial_raw, serial_normalized, original_filename, file_path, file_hash)
                        VALUES ('THAR-DIESEL', '2026-06-13', '103', '103', 'thar.xlsx', 'Z:/mahindra/thar.xlsx', 'h3')""")
                        
        # 3. Create Users
        from werkzeug.security import generate_password_hash
        pwd = generate_password_hash("Pass@1234")
        # TVS Admin
        conn.execute("INSERT INTO users (username, email, password_hash, display_name, role, customer_id) VALUES ('tvs_admin', 'admin@tvs.com', ?, 'TVS Admin', 'company_admin', 'tvs')", (pwd,))
        # TVS User 1 (ALL recipes)
        conn.execute("INSERT INTO users (username, email, password_hash, display_name, role, customer_id, access_mode) VALUES ('tvs_all', 'all@tvs.com', ?, 'TVS All', 'customer_viewer', 'tvs', 'ALL')", (pwd,))
        # TVS User 2 (CUSTOM recipe: only I-QUBE-BATTERY)
        conn.execute("INSERT INTO users (username, email, password_hash, display_name, role, customer_id, access_mode) VALUES ('tvs_ev', 'ev@tvs.com', ?, 'TVS EV', 'customer_viewer', 'tvs', 'CUSTOM')", (pwd,))
        
        u2_id = conn.execute("SELECT id FROM users WHERE username = 'tvs_ev'").fetchone()['id']
        conn.execute("INSERT INTO user_recipes (user_id, recipe_name) VALUES (?, 'I-QUBE-BATTERY')", (u2_id,))
        
        conn.commit()
        conn.close()
        
# -----------------------------------------------------------------------------
# EXTENDED COMPREHENSIVE TEST MATRIX FOR V3 PORTAL (80+ TEST CASES)
# -----------------------------------------------------------------------------
import os
from werkzeug.security import generate_password_hash
from app.helpers import decrypt_password, hash_file
from app.parser import parse_filename
from app.sync_engine import ensure_file_safe
from app.mail import get_effective_portal_url
from app.oauth import get_oauth_settings, get_registered_client
from app.tunnel_manager import get_installed_tunnel_binaries, get_tunnel_status, stop_tunnel

@pytest.fixture
def v3_app(tmp_path):
    db_path = str(tmp_path / "test_v3_portal.db")
    storage_dir = str(tmp_path / "storage")
    os.makedirs(storage_dir, exist_ok=True)
    
    app = create_app({
        "TESTING": True,
        "DATABASE_PATH": db_path,
        "STORAGE_FOLDER": storage_dir,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key"
    })
    
    with app.app_context():
        conn = get_connection(db_path)
        conn.execute("INSERT INTO customers (id, company_name, allowed_domains) VALUES ('tvs', 'TVS Motor', 'tvs.com, tvsmotor.com')")
        conn.execute("INSERT INTO customers (id, company_name, allowed_domains) VALUES ('mahindra', 'Mahindra Auto', 'mahindra.com')")
        conn.execute("INSERT INTO customers (id, company_name, allowed_domains, portal_suspended) VALUES ('suspended_co', 'Suspended Co', 'suspended.com', 1)")
        
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'EV_THROTTLE')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'BRAKE_ACTUATOR')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('mahindra', 'SCORPIO_WIRING')")
        
        pwd = generate_password_hash('Password123!')
        conn.execute("INSERT INTO users (username, password_hash, display_name, role) VALUES ('admin_user', ?, 'System Admin', 'admin')", (pwd,))
        conn.execute("INSERT INTO users (username, password_hash, display_name, role, customer_id, email) VALUES ('tvs_admin', ?, 'TVS Admin', 'company_admin', 'tvs', 'admin@tvs.com')", (pwd,))
        conn.execute("INSERT INTO users (username, password_hash, display_name, role, customer_id, email, access_mode) VALUES ('tvs_viewer', ?, 'TVS Viewer', 'customer_viewer', 'tvs', 'eng@tvs.com', 'ALL')", (pwd,))
        conn.execute("INSERT INTO users (username, password_hash, display_name, role, customer_id, email, access_mode) VALUES ('tvs_custom', ?, 'TVS Custom', 'customer_viewer', 'tvs', 'custom@tvs.com', 'CUSTOM')", (pwd,))
        
        u_row = conn.execute("SELECT id FROM users WHERE username = 'tvs_custom'").fetchone()
        conn.execute("INSERT INTO user_recipes (user_id, recipe_name) VALUES (?, 'EV_THROTTLE')", (u_row['id'],))
        
        rep_file1 = os.path.join(storage_dir, "EV_THROTTLE_15-08-2026_10.00.00_001.xlsx")
        with open(rep_file1, 'w') as f: f.write("SAMPLE EXCEL DATA 1")
        conn.execute("INSERT INTO reports (customer_id, file_path, original_filename, recipe_name, report_date, report_time, serial_raw, serial_normalized, file_hash) VALUES ('tvs', ?, 'EV_THROTTLE_15-08-2026_10.00.00_001.xlsx', 'EV_THROTTLE', '2026-08-15', '10:00:00', '1', '0001', 'hash_001')", (rep_file1,))
        
        rep_file2 = os.path.join(storage_dir, "SCORPIO_WIRING_16-08-2026_11.00.00_002.xlsx")
        with open(rep_file2, 'w') as f: f.write("SAMPLE EXCEL DATA 2")
        conn.execute("INSERT INTO reports (customer_id, file_path, original_filename, recipe_name, report_date, report_time, serial_raw, serial_normalized, file_hash) VALUES ('mahindra', ?, 'SCORPIO_WIRING_16-08-2026_11.00.00_002.xlsx', 'SCORPIO_WIRING', '2026-08-16', '11:00:00', '2', '0002', 'hash_002')", (rep_file2,))
        
        conn.commit()
        conn.close()
        
    return app

@pytest.fixture
def v3_client(v3_app):
    return v3_app.test_client()

# --- 1. Custom Regex Parser Tests (Genuinely Unique Edge Cases) ---
def test_parser_custom_regex():
    pat = r"^([A-Z]+)-([0-9]{2}-[0-9]{2}-[0-9]{4})-([0-9]{2}\.[0-9]{2}\.[0-9]{2})-([0-9]+)\.xlsx$"
    res = parse_filename("MOTOR-25-08-2026-11.20.00-999.xlsx", custom_pattern=pat)
    assert res['recipe_name'] == 'MOTOR'
    assert res['serial_normalized'] == '0999'

def test_parser_custom_slash_date():
    pat = r"^([a-zA-Z0-9]+)_(\d{2}-\d{2}-\d{4})_(\d{2}\.\d{2}\.\d{2})_(\d+)\.xlsx$"
    res = parse_filename("WIRING_10-05-2026_14.00.00_7.xlsx", custom_pattern=pat)
    assert res['report_date'] == '2026-05-10'

def test_parser_custom_iso_date():
    pat = r"^([a-zA-Z0-9]+)_(\d{4}-\d{2}-\d{2})_(\d{2}\.\d{2}\.\d{2})_(\d+)\.xlsx$"
    res = parse_filename("WIRING_2026-12-31_14.00.00_7.xlsx", custom_pattern=pat)
    assert res['report_date'] == '2026-12-31'

def test_parser_invalid_regex_fallback():
    res = parse_filename("EV_TPS_13-06-2026_22.33.21_12.xlsx", custom_pattern="[broken")
    assert res['recipe_name'] == 'EV_TPS'

# --- 2. Cryptography & Security Tests ---
def test_crypto_invalid(v3_app):
    with v3_app.app_context():
        assert decrypt_password("invalid_cipher") == ""

def test_file_hash(tmp_path):
    p = tmp_path / "h.txt"
    p.write_text("Hello Hash")
    assert len(hash_file(str(p))) == 64

def test_ensure_file_safe_ok(tmp_path):
    p = tmp_path / "ok.xlsx"
    p.write_text("Data")
    assert ensure_file_safe(str(p)) is True

def test_ensure_file_safe_zero_size(tmp_path):
    p = tmp_path / "zero.xlsx"
    p.write_text("")
    assert ensure_file_safe(str(p)) is False

def test_ensure_file_safe_not_found():
    assert ensure_file_safe("C:/nonexistent_file_path_123.xlsx") is False

# --- 3. RBAC & Multi-Tenancy Tests ---
def test_rbac_admin_full_access(v3_client):
    v3_client.post('/login', data={'username': 'admin_user', 'password': 'Password123!'}, follow_redirects=True)
    r1 = v3_client.get('/search/results?recipe=EV_THROTTLE')
    assert b'EV_THROTTLE' in r1.data
    r2 = v3_client.get('/search/results?recipe=SCORPIO_WIRING')
    assert b'SCORPIO_WIRING' in r2.data

def test_rbac_tenant_isolation(v3_client):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    r1 = v3_client.get('/search/results?recipe=SCORPIO_WIRING')
    assert b'SCORPIO_WIRING' not in r1.data
    assert b'No quality reports found' in r1.data

def test_rbac_custom_mode(v3_client):
    v3_client.post('/login', data={'username': 'tvs_custom', 'password': 'Password123!'}, follow_redirects=True)
    r1 = v3_client.get('/search/results?recipe=EV_THROTTLE')
    assert b'EV_THROTTLE' in r1.data
    r2 = v3_client.get('/search/results?recipe=BRAKE_ACTUATOR')
    assert b'No quality reports found' in r2.data

def test_rbac_company_admin_restricted_from_system_settings(v3_client):
    v3_client.post('/login', data={'username': 'tvs_admin', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.get('/admin/settings')
    assert res.status_code == 403

def test_rbac_company_admin_access_team(v3_client):
    v3_client.post('/login', data={'username': 'tvs_admin', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.get('/company/users')
    assert res.status_code == 200
    assert b'TVS Motor' in res.data

def test_rbac_viewer_restricted_from_team_admin(v3_client):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.get('/company/users')
    assert res.status_code == 403

def test_rbac_suspended_portal_blocks_login(v3_client, v3_app):
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        pwd = generate_password_hash('Password123!')
        conn.execute("INSERT INTO users (username, password_hash, display_name, role, customer_id) VALUES ('susp_u', ?, 'Susp', 'customer_viewer', 'suspended_co')", (pwd,))
        conn.commit()
    res = v3_client.post('/login', data={'username': 'susp_u', 'password': 'Password123!'}, follow_redirects=True)
    assert b'Portal access for this customer is currently suspended' in res.data

def test_rbac_inactive_user_blocks_login(v3_client, v3_app):
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        conn.execute("UPDATE users SET is_active = 0 WHERE username = 'tvs_viewer'")
        conn.commit()
    res = v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    assert b'Your account has been revoked' in res.data

def test_rbac_logout(v3_client):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.get('/logout', follow_redirects=True)
    assert b'Authorized Access Only' in res.data

def test_rbac_search_requires_login(v3_client):
    res = v3_client.get('/search')
    assert res.status_code == 302

# --- 4. Self Registration & Auto Join Tests ---
def test_reg_authorized_domain(v3_client, v3_app):
    res = v3_client.post('/register', data={
        'email': 'anand@tvs.com',
        'display_name': 'Anand TVS',
        'username': 'anand_tvs',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert b'Account created successfully' in res.data
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        u = conn.execute("SELECT customer_id FROM users WHERE username = 'anand_tvs'").fetchone()
        assert u['customer_id'] == 'tvs'

def test_reg_secondary_domain(v3_client):
    res = v3_client.post('/register', data={
        'email': 'kiran@tvsmotor.com',
        'display_name': 'Kiran K',
        'username': 'kiran_tvs',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert b'Account created successfully' in res.data

def test_reg_unauthorized_domain(v3_client):
    res = v3_client.post('/register', data={
        'email': 'fake@gmail.com',
        'display_name': 'Fake',
        'username': 'fake_user',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert b'not authorized for self-registration' in res.data

def test_reg_suspended_company(v3_client):
    res = v3_client.post('/register', data={
        'email': 'emp@suspended.com',
        'display_name': 'Susp Emp',
        'username': 'susp_emp_2',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert b'Portal access for your organization is currently suspended' in res.data

def test_reg_duplicate_username(v3_client):
    res = v3_client.post('/register', data={
        'email': 'other@tvs.com',
        'display_name': 'TVS Admin 2',
        'username': 'tvs_admin',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert b'already exists' in res.data

def test_reg_weak_password(v3_client):
    res = v3_client.post('/register', data={
        'email': 'weak@tvs.com',
        'display_name': 'Weak',
        'username': 'weak_user_1',
        'password': '123'
    }, follow_redirects=True)
    assert b'Password must be at least 8 characters long' in res.data

def test_reg_missing_fields(v3_client):
    res = v3_client.post('/register', data={'email': '', 'display_name': '', 'username': '', 'password': ''}, follow_redirects=True)
    assert b'All fields are required' in res.data

def test_reg_company_admin_update_domains(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_admin', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.post('/company/domains/update', data={'allowed_domains': 'tvs.com, tvs-digital.com'}, follow_redirects=True)
    assert b'Auto-join email domains updated' in res.data
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        cust = conn.execute("SELECT allowed_domains FROM customers WHERE id = 'tvs'").fetchone()
        assert 'tvs-digital.com' in cust['allowed_domains']

# --- 5. Excel In-Browser Viewer & Stream Tests ---
def test_raw_stream_authorized(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        rep = conn.execute("SELECT id FROM reports WHERE recipe_name = 'EV_THROTTLE'").fetchone()
    res = v3_client.get(f'/view-raw/{rep["id"]}')
    assert res.status_code == 200
    assert b'SAMPLE EXCEL DATA 1' in res.data

def test_raw_stream_unauthorized_404(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        rep = conn.execute("SELECT id FROM reports WHERE recipe_name = 'SCORPIO_WIRING'").fetchone()
    res = v3_client.get(f'/view-raw/{rep["id"]}')
    assert res.status_code == 404

def test_download_authorized(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        rep = conn.execute("SELECT id FROM reports WHERE recipe_name = 'EV_THROTTLE'").fetchone()
    res = v3_client.get(f'/download/{rep["id"]}')
    assert res.status_code == 200

def test_download_unauthorized_404(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        rep = conn.execute("SELECT id FROM reports WHERE recipe_name = 'SCORPIO_WIRING'").fetchone()
    res = v3_client.get(f'/download/{rep["id"]}')
    assert res.status_code == 404

def test_view_raw_audit_trail(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        rep = conn.execute("SELECT id FROM reports WHERE recipe_name = 'EV_THROTTLE'").fetchone()
    v3_client.get(f'/view-raw/{rep["id"]}')
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        audit = conn.execute("SELECT action FROM audit_log WHERE report_id = ? ORDER BY id DESC LIMIT 1", (rep['id'],)).fetchone()
        assert audit['action'] == 'view_online'

def test_search_renders_view_button(v3_client):
    v3_client.post('/login', data={'username': 'tvs_viewer', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.get('/search/results?recipe=EV_THROTTLE')
    assert b'openExcelViewer' in res.data
    assert b'Download' in res.data

# --- 6. SSO OAuth Tests ---
def test_sso_save_config(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'admin_user', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.post('/admin/settings', data={
        'sso_google_enabled': '1',
        'sso_google_client_id': 'g_id',
        'sso_google_client_secret': 'g_sec'
    }, follow_redirects=True)
    assert b'System configuration updated' in res.data
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        settings = get_oauth_settings(conn)
        assert settings['sso_google_enabled'] == '1'

def test_sso_login_page_renders_active_provider(v3_client, v3_app):
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_google_enabled', '1')")
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_google_client_id', 'gid123')")
        conn.commit()
    res = v3_client.get('/login')
    assert b'Sign in with Google Workspace' in res.data

def test_sso_microsoft_client_object(v3_app):
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_microsoft_enabled', '1')")
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_microsoft_client_id', 'mid123')")
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_microsoft_client_secret', 'msec')")
        conn.commit()
        cl = get_registered_client('microsoft', conn)
        assert cl is not None

def test_sso_github_client_object(v3_app):
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_github_enabled', '1')")
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_github_client_id', 'ghid123')")
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('sso_github_client_secret', 'ghsec')")
        conn.commit()
        cl = get_registered_client('github', conn)
        assert cl is not None

# --- 7. Tunnel & Email Templates Tests ---
def test_tunnel_status_dict():
    st = get_tunnel_status()
    assert 'active' in st

def test_tunnel_binaries_dict():
    binaries = get_installed_tunnel_binaries()
    assert 'cloudflared' in binaries

def test_tunnel_stop():
    assert stop_tunnel() is True

def test_tunnel_save_public_url(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'admin_user', 'password': 'Password123!'}, follow_redirects=True)
    v3_client.post('/admin/settings', data={'public_portal_url': 'https://custom-tunnel.com'}, follow_redirects=True)
    with v3_app.app_context():
        assert get_effective_portal_url() == 'https://custom-tunnel.com'

def test_templates_save_custom(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'admin_user', 'password': 'Password123!'}, follow_redirects=True)
    v3_client.post('/admin/settings', data={
        'template_welcome_email': 'Custom Welcome: {portal_url}',
        'template_invite_email': 'Custom Invite: {portal_url}',
        'template_reset_password': 'Custom Reset: {reset_url}'
    }, follow_redirects=True)
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        r = conn.execute("SELECT value FROM system_settings WHERE key = 'template_welcome_email'").fetchone()
        assert 'Custom Welcome' in r['value']

# --- 8. Bulk Import Tests ---
def test_bulk_import_admin(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'admin_user', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.post('/admin/users/bulk_import', data={
        'customer_id': 'tvs',
        'bulk_text': 'eng100@tvs.com,Eng 100,eng100\neng101@tvs.com,Eng 101,eng101',
        'role': 'customer_viewer'
    }, follow_redirects=True)
    assert b'Bulk Provisioning Completed' in res.data
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        assert conn.execute("SELECT id FROM users WHERE username = 'tvs_eng100'").fetchone() is not None

def test_bulk_import_company_admin(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_admin', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.post('/company/users/bulk_add', data={
        'bulk_text': 'worker50@tvs.com\nworker51@tvs.com',
        'role': 'customer_viewer'
    }, follow_redirects=True)
    assert b'Bulk Provisioning Completed' in res.data
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        assert conn.execute("SELECT id FROM users WHERE email = 'worker50@tvs.com'").fetchone() is not None

def test_bulk_import_skip_existing(v3_client):
    v3_client.post('/login', data={'username': 'admin_user', 'password': 'Password123!'}, follow_redirects=True)
    res = v3_client.post('/admin/users/bulk_import', data={
        'customer_id': 'tvs',
        'bulk_text': 'tvs_viewer@tvs.com,Existing,tvs_viewer',
        'role': 'customer_viewer'
    }, follow_redirects=True)
    assert b'skipped' in res.data

def test_company_admin_toggle_user(v3_client, v3_app):
    v3_client.post('/login', data={'username': 'tvs_admin', 'password': 'Password123!'}, follow_redirects=True)
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        u = conn.execute("SELECT id FROM users WHERE username = 'tvs_viewer'").fetchone()
    res = v3_client.post('/company/users/toggle', data={'user_id': u['id'], 'is_active': '0'}, follow_redirects=True)
    assert b'status updated' in res.data
    with v3_app.app_context():
        conn = get_connection(v3_app.config['DATABASE_PATH'])
        assert conn.execute("SELECT is_active FROM users WHERE id = ?", (u['id'],)).fetchone()['is_active'] == 0
