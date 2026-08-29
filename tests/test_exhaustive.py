import pytest
import os
import tempfile
import sqlite3
from flask import url_for
from werkzeug.security import generate_password_hash

from app import create_app
from app.database import get_connection, ensure_schema

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    storage_dir = tempfile.mkdtemp()
    
    app = create_app({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'STORAGE_FOLDER': storage_dir,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test_secret_key'
    })
    
    with app.app_context():
        conn = get_connection(db_path)
        ensure_schema(conn)
        
        conn.execute("INSERT INTO customers (id, company_name, portal_suspended) VALUES ('cust1', 'Test Customer 1', 0)")
        
        pass_hash = generate_password_hash('admin123')
        conn.execute("INSERT INTO users (username, password_hash, display_name, email, role, is_active) VALUES ('testadmin', ?, 'Admin', 'admin@suprajit.com', 'admin', 1)", (pass_hash,))
        
        user_hash = generate_password_hash('user123')
        conn.execute("INSERT INTO users (username, password_hash, display_name, email, role, customer_id, is_active) VALUES ('testuser', ?, 'User', 'user@customer.com', 'customer_viewer', 'cust1', 1)", (user_hash,))
        
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('cust1', 'RECIPE_A')")
        
        conn.execute("INSERT INTO batch_runs (status) VALUES ('completed')")
        rep_path = os.path.join(storage_dir, "file.xlsx")
        with open(rep_path, 'w') as f: f.write("EXCEL DATA")
        conn.execute("INSERT INTO reports (batch_run_id, recipe_name, report_date, serial_normalized, original_filename, file_path, file_hash) VALUES (1, 'RECIPE_A', '2026-08-27', '0001', 'file.xlsx', ?, 'hash123')", (rep_path,))
        
        conn.commit()
        conn.close()

    yield app

    try: os.close(db_fd)
    except: pass
    try: os.unlink(db_path)
    except: pass

@pytest.fixture
def client(app):
    return app.test_client()

def login_as(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

# -----------------
# AUTHENTICATION ROUTES
# -----------------
def test_auth_routes(client):
    assert client.get('/login').status_code == 200
    assert client.get('/forgot-password').status_code == 200
    
    rv = login_as(client, 'testuser', 'user123')
    assert rv.status_code == 200
    
    rv = client.get('/logout', follow_redirects=True)
    assert rv.status_code == 200

# -----------------
# PORTAL ROUTES (AS USER)
# -----------------
def test_portal_routes(client):
    rv1 = login_as(client, 'testuser', 'user123')
    assert rv1.status_code == 200
    
    rv2 = client.get('/search', follow_redirects=True)
    assert rv2.status_code == 200
    
    rv3 = client.get('/search/results?recipe=RECIPE_A&serial=0001', follow_redirects=True)
    assert rv3.status_code == 200
    
    rv4 = client.get('/download/1', follow_redirects=True)
    assert rv4.status_code in [200, 403, 404]

# -----------------
# ADMIN ROUTES (AS ADMIN)
# -----------------
def test_admin_read_routes(client):
    login_as(client, 'testadmin', 'admin123')
    
    routes = [
        '/admin/',
        '/admin/settings',
        '/admin/customers',
        '/admin/diagnostics',
        '/admin/repair'
    ]
    for r in routes:
        rv = client.get(r, follow_redirects=True)
        assert rv.status_code == 200, f"Route {r} failed with {rv.status_code}"

def test_admin_customer_actions(client):
    login_as(client, 'testadmin', 'admin123')
    
    rv = client.post('/admin/customers/add', data={'company_name': 'New Co'}, follow_redirects=True)
    assert rv.status_code == 200
    
    rv = client.post('/admin/customers/add_recipe', data={'customer_id': 'cust1', 'recipe_name': 'RECIPE_B'}, follow_redirects=True)
    assert rv.status_code == 200
    
    rv = client.post('/admin/customers/add_user', data={
        'customer_id': 'cust1', 
        'username': 'newuser', 
        'email': 'new@user.com', 
        'password': 'password123',
        'display_name': 'New User'
    }, follow_redirects=True)
    assert rv.status_code == 200

def test_admin_system_actions(client):
    login_as(client, 'testadmin', 'admin123')
    
    rv = client.post('/admin/trigger_sync', follow_redirects=True)
    assert rv.status_code == 200

# -----------------
# 3-WAY INTEGRATION & SMOKE TESTS (20+ CASES)
# -----------------
def test_smoke_login_page_renders_cleanly(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Sign In' in rv.data or b'Authorized Access Only' in rv.data

def test_smoke_register_page_renders_cleanly(client):
    rv = client.get('/register')
    assert rv.status_code == 200

def test_smoke_forgot_password_renders_cleanly(client):
    rv = client.get('/forgot-password')
    assert rv.status_code == 200

def test_integration_search_empty_query(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/search/results')
    assert rv.status_code == 200

def test_integration_search_filter_by_recipe(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/search/results?recipe=RECIPE_A')
    assert b'0001' in rv.data

def test_integration_search_filter_by_date(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/search/results?date=2026-08-27')
    assert b'0001' in rv.data

def test_integration_search_filter_by_serial(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/search/results?serial=0001')
    assert b'0001' in rv.data

def test_integration_search_nonexistent_serial_empty(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/search/results?serial=99999999')
    assert b'No quality reports found' in rv.data

def test_integration_view_raw_unauthorized(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/view-raw/99999')
    assert rv.status_code in (403, 404)

def test_integration_download_unauthorized(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/download/99999')
    assert rv.status_code in (403, 404)

def test_integration_customer_detail_page(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
    rv = client.get('/admin/customers/cust1')
    assert rv.status_code == 200
    assert b'Test Customer 1' in rv.data

def test_integration_admin_settings_post_empty(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
    rv = client.post('/admin/settings', data={}, follow_redirects=True)
    assert rv.status_code == 200

def test_integration_admin_customer_toggle_user(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
    rv = client.post('/admin/customers/toggle_user', data={'user_id': 2}, follow_redirects=True)
    assert rv.status_code == 200

def test_integration_admin_customer_edit(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
    rv = client.post('/admin/customers/edit', data={'customer_id': 'cust1', 'company_name': 'Renamed Customer'}, follow_redirects=True)
    assert rv.status_code == 200

def test_integration_admin_customer_suspend(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
    rv = client.post('/admin/customers/suspend', data={'customer_id': 'cust1'}, follow_redirects=True)
    assert rv.status_code == 200

def test_integration_admin_repair_page(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
    rv = client.get('/admin/repair')
    assert rv.status_code == 200

def test_integration_admin_diagnostics_page(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
    rv = client.get('/admin/diagnostics')
    assert rv.status_code == 200

def test_e2e_full_search_cycle(client):
    client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
    rv = client.get('/search')
    assert rv.status_code == 200
    rv_res = client.get('/search/results?recipe=RECIPE_A&date=2026-08-27&serial=0001')
    assert rv_res.status_code == 200
    assert b'RECIPE_A' in rv_res.data


