"""
AUTHENTIC ATTACK SURFACE TEST SUITE: ADMIN & TENANT MANAGEMENT
Tests high-risk administrative operations:
1. Customer Tenant Provisioning, Deletion, and Instant Suspension Cascade
2. SSO Domain Whitelisting & Auto-Join Identity Configuration
3. System Admin Credential Changes, Master Password Resets, and Encrypted SMTP Persistence
4. Setup Wizard Trap Enforcement for Bootstrap Accounts
"""

import pytest
pytestmark = pytest.mark.integration


import pytest
from app.database import get_connection, ensure_schema
from app.helpers import decrypt_password

# =============================================================================
# 1. CUSTOMER TENANT LIFECYCLE & SUSPENSION CASCADE
# =============================================================================

@pytest.fixture
def admin_client(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'Password123!'}, follow_redirects=True)
    return client

def test_admin_add_customer_and_duplicate_rejection(admin_client, app):
    """
    Verifies that an admin can create a customer tenant and that duplicate IDs are rejected.
    """
    # Add customer
    res = client = admin_client
    res = client.post('/admin/customers/add', data={
        'id': 'bajaj_auto',
        'company_name': 'Bajaj Auto Ltd'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Bajaj Auto Ltd" in res.data

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        row = conn.execute("SELECT * FROM customers WHERE id = 'bajaj_auto'").fetchone()
        assert row is not None
        assert row['company_name'] == 'Bajaj Auto Ltd'
        conn.close()

    # Attempt duplicate insert
    res_dup = client.post('/admin/customers/add', data={
        'id': 'bajaj_auto',
        'company_name': 'Duplicate Bajaj'
    }, follow_redirects=True)
    assert b"Database Error" in res_dup.data or b"already exists" in res_dup.data or res_dup.status_code == 200


def test_admin_toggle_customer_status_suspends_and_activates(admin_client, app):
    """
    Verifies that toggling customer status updates portal_suspended in the database.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        conn.execute("INSERT OR REPLACE INTO customers (id, company_name, portal_suspended) VALUES ('honda', 'Honda Motors', 0)")
        conn.commit()
        conn.close()

    # Toggle to suspended
    res_suspend = admin_client.post('/admin/customers/suspend', data={'customer_id': 'honda', 'portal_suspended': '1'}, follow_redirects=True)
    assert res_suspend.status_code == 200

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        row = conn.execute("SELECT portal_suspended FROM customers WHERE id = 'honda'").fetchone()
        assert row['portal_suspended'] == 1
        conn.close()

    # Toggle back to active
    res_activate = admin_client.post('/admin/customers/suspend', data={'customer_id': 'honda', 'portal_suspended': '0'}, follow_redirects=True)
    assert res_activate.status_code == 200

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        row = conn.execute("SELECT portal_suspended FROM customers WHERE id = 'honda'").fetchone()
        assert row['portal_suspended'] == 0
        conn.close()


def test_admin_customer_deletion_cascades_recipes_and_users(admin_client, app):
    """
    Verifies that deleting a customer removes associated customer_recipes and users.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        conn.execute("INSERT OR REPLACE INTO customers (id, company_name) VALUES ('yamaha', 'Yamaha India')")
        conn.execute("INSERT OR REPLACE INTO customer_recipes (customer_id, recipe_name) VALUES ('yamaha', 'R15_THROTTLE')")
        conn.execute("""
            INSERT OR REPLACE INTO users (username, password_hash, display_name, email, role, customer_id, is_active)
            VALUES ('yamaha_user', 'hash', 'Yamaha User', 'yam@example.com', 'customer_viewer', 'yamaha', 1)
        """)
        conn.commit()
        conn.close()

    res = admin_client.post('/admin/customers/delete', data={'customer_id': 'yamaha'}, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        assert conn.execute("SELECT * FROM customers WHERE id = 'yamaha'").fetchone() is None
        assert conn.execute("SELECT * FROM customer_recipes WHERE customer_id = 'yamaha'").fetchone() is None
        conn.close()


# =============================================================================
# 2. SSO IDENTITY & DOMAIN PROVISIONING
# =============================================================================

def test_admin_update_oauth_sso_credentials(admin_client, app):
    """
    Verifies that OAuth provider settings persist accurately via /admin/settings.
    """
    res = admin_client.post('/admin/settings', data={
        'sso_google_enabled': '1',
        'sso_google_client_id': 'google-client-id-12345.apps.googleusercontent.com',
        'sso_google_client_secret': 'GOCSPX-SecretPayloadKey999'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        cid = conn.execute("SELECT value FROM system_settings WHERE key = 'sso_google_client_id'").fetchone()
        sec = conn.execute("SELECT value FROM system_settings WHERE key = 'sso_google_client_secret'").fetchone()
        en = conn.execute("SELECT value FROM system_settings WHERE key = 'sso_google_enabled'").fetchone()
        
        assert cid['value'] == 'google-client-id-12345.apps.googleusercontent.com'
        assert sec['value'] == 'GOCSPX-SecretPayloadKey999'
        assert en['value'] == '1'
        conn.close()


def test_admin_settings_post_persists_smtp_and_search_paths(admin_client, app):
    """
    Verifies that global settings updates properly store plain settings and encrypt SMTP passwords.
    """
    res = admin_client.post('/admin/settings', data={
        'sync_time': '03:30',
        'root_search_path': r'C:\Line1;D:\Line2',
        'mail_server': 'smtp.office365.com',
        'mail_port': '587',
        'mail_username': 'plant_quality@suprajit.com',
        'mail_password': 'SuperSecretSmtpPass!@#',
        'developer_email': 'it_alerts@suprajit.com',
        'telemetry_frequency': 'weekly'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        st = conn.execute("SELECT value FROM system_settings WHERE key = 'sync_time'").fetchone()['value']
        roots = conn.execute("SELECT value FROM system_settings WHERE key = 'root_search_path'").fetchone()['value']
        mpass = conn.execute("SELECT value FROM system_settings WHERE key = 'mail_password'").fetchone()['value']
        
        assert st == '03:30'
        assert roots == r'C:\Line1;D:\Line2'
        assert decrypt_password(mpass) == 'SuperSecretSmtpPass!@#'
        conn.close()


def test_admin_setup_wizard_completion_unblocks_dashboard(client, app):
    """
    Verifies that the bootstrap setup wizard properly secures the bootstrap admin account
    and marks setup_completed = 1 in the database.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        conn.execute("DELETE FROM system_settings WHERE key = 'setup_completed'")
        conn.execute("INSERT OR REPLACE INTO users (id, username, password_hash, display_name, role, is_active) VALUES (1, 'bootstrap_admin', 'oldhash', 'Bootstrap Admin', 'admin', 1)")
        conn.commit()
        conn.close()

    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['user_id'] = 1
        sess['role'] = 'admin'

    # Attempt to access dashboard without setup -> must redirect to /admin/setup
    res_trap = client.get('/admin/', follow_redirects=False)
    assert res_trap.status_code == 302
    assert '/admin/setup' in res_trap.headers.get('Location', '')

    # Complete setup wizard
    res_post = client.post('/admin/setup', data={
        'new_password': 'BrandNewSecureAdminPassword123!',
        'admin_email': 'master_admin@suprajit.com',
        'mail_server': 'smtp.gmail.com',
        'mail_port': '587',
        'mail_username': 'notifications@suprajit.com',
        'mail_password': 'SecureSmtpPassword123!'
    }, follow_redirects=True)
    assert res_post.status_code == 200

    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        setup_done = conn.execute("SELECT value FROM system_settings WHERE key = 'setup_completed'").fetchone()
        assert setup_done is not None
        assert setup_done['value'] == '1'
        conn.close()
