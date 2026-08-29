import pytest
import os
import sys
import sqlite3
import tempfile
import shutil

# Ensure app root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('testadmin', 'scrypt:32768:8:1$1uR9x$a', 'admin')")
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('testuser', 'scrypt:32768:8:1$1uR9x$a', 'user')")
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
