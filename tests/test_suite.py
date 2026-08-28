import pytest
import os
import tempfile
import sqlite3
from datetime import date, datetime
from flask import url_for
from werkzeug.security import generate_password_hash

from app import create_app
from app.database import get_connection, ensure_schema
from app.sync_engine import SyncEngine
from app.parser import parse_filename

@pytest.fixture
def app():
    # Setup isolated test database and config
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.environ['DATABASE_PATH'] = db_path
    os.environ['STORAGE_BASE'] = tempfile.mkdtemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'WTF_CSRF_CHECK_DEFAULT': False
    })
    
    with app.app_context():
        conn = get_connection(db_path)
        ensure_schema(conn)
        
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('suprajit', 'Suprajit Internal')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('suprajit', 'TEST_RECIPE')")
        
        pass_hash = generate_password_hash('admin123')
        conn.execute("INSERT INTO users (username, password_hash, display_name, role) VALUES ('bootstrap_admin', ?, 'Administrator', 'admin')", (pass_hash,))
        conn.commit()
        conn.close()

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

# -----------------
# 1. PARSER TESTS
# -----------------
def test_parse_filename():
    assert parse_filename('EV_TPS_13-06-2026_22.33.21_12.xlsx')['recipe_name'] == 'EV_TPS'

# -----------------
# 2. SYNC ENGINE TESTS
# -----------------
def test_sync_engine_ingestion(app):
    with app.app_context():
        db_path = os.environ['DATABASE_PATH']
        storage = os.environ['STORAGE_BASE']
        
        recipe_dir = os.path.join(storage, 'Test Reports', 'TEST_RECIPE')
        os.makedirs(recipe_dir, exist_ok=True)
        dummy_file = os.path.join(recipe_dir, 'TEST_RECIPE_13-06-2026_22.33.21_12.xlsx')
        with open(dummy_file, 'wb') as f:
            f.write(b"dummy data")
            
        engine = SyncEngine(db_path, storage)
        engine._get_search_roots = lambda: [storage]
        
        assert engine.run_batch(full_sync=True) == 1
        assert engine.run_batch(full_sync=True) == 0

# -----------------
# 3. AUTH & ROUTING TESTS
# -----------------
def test_login_redirect_and_auth(client, app):
    # Try logging in
    with client:
        rv = client.post('/login', data={'username': 'bootstrap_admin', 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200
        
        # Test trap logic explicitly
        rv2 = client.get('/admin/settings', follow_redirects=True)
        assert b"System Administrator" in rv2.data or b"Setup" in rv2.data

def test_404_error_handler(client, app):
    rv = client.get('/favicon.ico')
    assert rv.status_code == 404


