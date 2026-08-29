"""
RATE LIMITER REGRESSION TEST
Ensures that the login endpoint strictly enforces the configured rate limit (10 requests per minute per client IP)
and returns HTTP 429 Too Many Requests on the 11th attempt.
"""

import tempfile
import os
import shutil
from app import create_app, limiter
from app.database import get_connection, ensure_schema

def test_login_rate_limiter_blocks_on_eleventh_request():
    db_fd, db_path = tempfile.mkstemp()
    storage_dir = tempfile.mkdtemp()

    test_config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": True,
        "DATABASE_PATH": db_path,
        "STORAGE_FOLDER": storage_dir
    }
    
    app = create_app(test_config)
    # Explicitly enable limiter for this regression test
    limiter.enabled = True
    app.config["RATELIMIT_ENABLED"] = True

    conn = get_connection(db_path)
    ensure_schema(conn)
    conn.execute("INSERT OR REPLACE INTO users (username, password_hash, display_name, email, role, is_active) VALUES ('test_rl', 'scrypt:32768:8:1$hash', 'Test RL', 'rl@example.com', 'admin', 1)")
    conn.commit()
    conn.close()

    client = app.test_client()

    responses = []
    # Send 10 requests (allowed within 10 per minute window)
    for i in range(10):
        res = client.post('/login', data={'username': 'test_rl', 'password': 'wrong_password'})
        responses.append(res.status_code)

    # 11th request must be rejected with HTTP 429 Too Many Requests
    eleventh_res = client.post('/login', data={'username': 'test_rl', 'password': 'wrong_password'})

    # Cleanup
    os.close(db_fd)
    try:
        os.remove(db_path)
        shutil.rmtree(storage_dir, ignore_errors=True)
    except Exception:
        pass

    assert all(code in (200, 302) for code in responses), f"Expected 200/302 for first 10 requests, got {responses}"
    assert eleventh_res.status_code == 429, f"Expected 429 on 11th request, but got {eleventh_res.status_code}"
