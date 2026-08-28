import pytest
from flask import url_for

def test_customer_cannot_access_other_customer_reports(client, app):
    """ASVS: Verify tenant isolation at the search results level."""
    with app.app_context():
        from app.database import get_connection
        conn = get_connection(app.config['DATABASE_PATH'])
        from werkzeug.security import generate_password_hash
        p_hash = generate_password_hash('admin123')
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('CUST_A', 'Company A')")
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('CUST_B', 'Company B')")
        conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role, customer_id) VALUES ('cust_a', ?, 'user', 'CUST_A')", (p_hash,))
        conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role, customer_id) VALUES ('cust_b', ?, 'user', 'CUST_B')", (p_hash,))
        conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES ('CUST_A', 'Recipe_A')")
        conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES ('CUST_B', 'Recipe_B')")
        conn.execute("INSERT OR IGNORE INTO reports (file_path, original_filename, recipe_name, report_date, report_time, serial_raw) VALUES ('dummy/path/a.csv', 'a.csv', 'Recipe_A', '2026-01-01', '120000', '123')")
        conn.execute("INSERT OR IGNORE INTO reports (file_path, original_filename, recipe_name, report_date, report_time, serial_raw) VALUES ('dummy/path/b.csv', 'b.csv', 'Recipe_B', '2026-01-01', '120000', '456')")
        conn.commit()

    client.post('/login', data={'username': 'cust_a', 'password': 'admin123'}, follow_redirects=True)
    rv = client.get('/search/results')
    assert b'a.csv' in rv.data
    assert b'b.csv' not in rv.data

def test_customer_cannot_access_admin_routes(client, app):
    """ASVS: Verify Broken Access Control prevention on admin routes."""
    with app.app_context():
        from app.database import get_connection
        conn = get_connection(app.config['DATABASE_PATH'])
        from werkzeug.security import generate_password_hash
        p_hash = generate_password_hash('admin123')
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('CUST_A', 'Company A')")
        conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role, customer_id) VALUES ('standard_user', ?, 'user', 'CUST_A')", (p_hash,))
        conn.commit()
        
    client.post('/login', data={'username': 'standard_user', 'password': 'admin123'}, follow_redirects=True)
    rv = client.get('/admin/diagnostics')
    assert rv.status_code == 403

def test_path_traversal_blocked(client, app):
    """ASVS: Verify absolute blocking of OS path traversal via /download."""
    with app.app_context():
        from app.database import get_connection
        conn = get_connection(app.config['DATABASE_PATH'])
        from werkzeug.security import generate_password_hash
        p_hash = generate_password_hash('admin123')
        conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('hacker', ?, 'admin')", (p_hash,))
        conn.execute("INSERT OR IGNORE INTO reports (id, file_path, original_filename, recipe_name, report_date, report_time, serial_raw) VALUES (9999, 'C:/Windows/System32/cmd.exe', 'cmd.exe', 'Hacked', '2026-01-01', '120000', '123')")
        conn.commit()
        
    client.post('/login', data={'username': 'hacker', 'password': 'admin123'}, follow_redirects=True)
    rv = client.get('/download/9999')
    assert rv.status_code == 403

def test_security_headers_present(client):
    """ASVS: Verify HTTP deployment hardening headers."""
    rv = client.get('/login')
    assert rv.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert rv.headers.get('X-Content-Type-Options') == 'nosniff'
    assert 'default-src' in rv.headers.get('Content-Security-Policy', '')
