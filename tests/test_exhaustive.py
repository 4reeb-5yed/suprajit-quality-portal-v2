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
    os.environ['DATABASE_PATH'] = db_path
    os.environ['STORAGE_BASE'] = tempfile.mkdtemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False
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
        conn.execute("INSERT INTO reports (batch_run_id, recipe_name, report_date, serial_normalized, original_filename, file_path, file_hash) VALUES (1, 'RECIPE_A', '2026-08-27', '0001', 'file.xlsx', 'path.xlsx', 'hash123')")
        
        conn.commit()
        conn.close()

    yield app

    os.close(db_fd)
    os.unlink(db_path)

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
    assert rv4.status_code in [200, 404]

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

