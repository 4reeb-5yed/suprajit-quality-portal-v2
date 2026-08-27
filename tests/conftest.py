import pytest
import os
import sqlite3
import tempfile
from app import create_app
from app.database import get_connection, ensure_schema

@pytest.fixture
def app():
    # Use an in-memory or temp DB for tests so we don't pollute real data
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "DATABASE_PATH": db_path
    })
    
    conn = get_connection(db_path)
    ensure_schema(conn)
    
    # Create test users
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('testadmin', 'scrypt:32768:8:1$1uR9x$a', 'admin')")
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('testuser', 'scrypt:32768:8:1$1uR9x$a', 'user')")
    conn.commit()
    conn.close()

    yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()
