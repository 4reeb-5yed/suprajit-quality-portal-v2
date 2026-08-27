import pytest
import os
import sqlite3
from app import create_app
from app.database import init_db

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    
    db_path = app.config['DATABASE_PATH']
    init_db(db_path)
    
    # Create test users
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('testadmin', 'scrypt:32768:8:1$1uR9x$a', 'admin')")
    conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('testuser', 'scrypt:32768:8:1$1uR9x$a', 'user')")
    conn.commit()
    conn.close()

    yield app

@pytest.fixture
def client(app):
    return app.test_client()
