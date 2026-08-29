import pytest
import os
import sys
import sqlite3
import tempfile
import shutil

# Ensure app root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set SECRET_KEY in environment before importing app modules to satisfy startup check at import time
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-0123456789abcdef"

from app import create_app
from app.database import get_connection, ensure_schema

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    storage_dir = tempfile.mkdtemp()
    
    test_config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
        "DATABASE_PATH": db_path,
        "STORAGE_FOLDER": storage_dir
    }
    app = create_app(test_config)
    from app import limiter
    limiter.enabled = False
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "DATABASE_PATH": db_path,
        "STORAGE_FOLDER": storage_dir
    })
    
    conn = get_connection(db_path)
    ensure_schema(conn)
    
    conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('suprajit', 'Suprajit Internal')")
    conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES ('suprajit', 'TEST_RECIPE')")
    
    from werkzeug.security import generate_password_hash
    pass_hash = generate_password_hash('Password123!')
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, display_name, email, role, is_active) VALUES ('testadmin', ?, 'Administrator', 'admin@example.com', 'admin', 1)", (pass_hash,))
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, display_name, email, role, is_active) VALUES ('testuser', ?, 'Test User', 'user@example.com', 'user', 1)", (pass_hash,))
    conn.commit()
    conn.close()

    yield app
    
    os.close(db_fd)
    try:
        os.remove(db_path)
        shutil.rmtree(storage_dir, ignore_errors=True)
    except Exception:
        pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
