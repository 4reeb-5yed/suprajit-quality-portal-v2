import pytest
import os
import sqlite3
import tempfile
import shutil
from app import create_app
from app.database import get_connection, ensure_schema

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    storage_dir = tempfile.mkdtemp()
    
    app = create_app()
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
    os.unlink(db_path)
    shutil.rmtree(storage_dir)

@pytest.fixture
def client(app):
    return app.test_client()
