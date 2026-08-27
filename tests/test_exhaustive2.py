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
# FULL EXHAUSTIVE ADMIN ACTIONS
# -----------------
def test_all_admin_post_endpoints(client):
    login_as(client, 'testadmin', 'admin123')
    
    # Toggle user active status
    rv = client.post('/admin/customers/toggle_user', data={'user_id': 2}, follow_redirects=True)
    assert rv.status_code == 200
    
    # Edit Customer
    rv = client.post('/admin/customers/edit', data={'customer_id': 'cust1', 'company_name': 'Changed Name'}, follow_redirects=True)
    assert rv.status_code == 200
    
    # Suspend Customer
    rv = client.post('/admin/customers/suspend', data={'customer_id': 'cust1'}, follow_redirects=True)
    assert rv.status_code == 200
    
    # Delete Recipe
    rv = client.post('/admin/customers/delete_recipe', data={'customer_id': 'cust1', 'recipe_name': 'RECIPE_A'}, follow_redirects=True)
    assert rv.status_code == 200
    
    # Delete User
    rv = client.post('/admin/users/delete', data={'user_id': 2}, follow_redirects=True)
    assert rv.status_code == 200
    
    # Delete Customer entirely
    rv = client.post('/admin/customers/delete', data={'customer_id': 'cust1'}, follow_redirects=True)
    assert rv.status_code == 200

# -----------------
# DIAGNOSTICS & SYSTEM ENDPOINTS
# -----------------
def test_all_diagnostics_endpoints(client):
    login_as(client, 'testadmin', 'admin123')
    
    rv = client.get('/admin/diagnostics', follow_redirects=True)
    assert rv.status_code == 200
    
    # We can trigger the sync
    rv = client.post('/admin/trigger_sync', follow_redirects=True)
    assert rv.status_code == 200

# -----------------
# AUTH RESET PASSWORD FLOW
# -----------------
def test_password_reset_flow(client):
    # Attempting to post to forgot-password
    rv = client.post('/forgot-password', data={'email': 'user@customer.com'}, follow_redirects=True)
    assert rv.status_code == 200
    
    # (In a real scenario it would send an email and generate a token, we just check no 500 error occurs here)
    # The mail.py is mostly mocked or skipped if not fully configured but shouldn't 500
