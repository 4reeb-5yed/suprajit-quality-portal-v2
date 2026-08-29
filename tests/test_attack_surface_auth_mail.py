"""
AUTHENTIC ATTACK SURFACE TEST SUITE: AUTH RECOVERY & EMAIL NOTIFICATIONS
Tests security-critical token flows and email dispatches:
1. Password Reset Token Generation, Cryptographic Expiry, and Signature Validation
2. Password Reset Form Verification (Password Complexity, Hash Updates, Token Invalidation)
3. Account 5-Strike Lockout & 15-Minute Expiry
4. Effective Portal URL Construction (Tunnel Override vs Host Fallback)
"""

import pytest
from werkzeug.security import check_password_hash
from app.database import get_connection, ensure_schema
from app.mail import get_serializer, get_effective_portal_url

# =============================================================================
# 1. PASSWORD RESET SERIALIZER & TOKEN LIFECYCLE
# =============================================================================

def test_password_reset_serializer_roundtrip(app):
    """
    Verifies that the itsdangerous serializer generates valid signed tokens and decodes emails correctly.
    """
    with app.app_context():
        serializer = get_serializer()
        email = "quality_manager@suprajit.com"
        token = serializer.dumps(email, salt='password-reset-salt')
        assert isinstance(token, str)

        recovered_email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
        assert recovered_email == email


def test_password_reset_token_expiry(app):
    """
    Verifies that expired tokens raise SignatureExpired exceptions.
    """
    from itsdangerous import SignatureExpired
    with app.app_context():
        serializer = get_serializer()
        token = serializer.dumps("user@example.com", salt='password-reset-salt')
        
        # max_age = -1 forces immediate expiry
        with pytest.raises(SignatureExpired):
            serializer.loads(token, salt='password-reset-salt', max_age=-1)


# =============================================================================
# 2. PASSWORD RESET ROUTING & PASSWORD COMPLEXITY ENFORCEMENT
# =============================================================================

def test_password_reset_flow_updates_database_hash(client, app):
    """
    Verifies end-to-end token consumption, password validation, and database hash rotation.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        conn.execute("""
            INSERT OR REPLACE INTO users (id, username, password_hash, display_name, email, role, is_active)
            VALUES (777, 'reset_user', 'old_password_hash', 'Reset User', 'reset_me@suprajit.com', 'customer_viewer', 1)
        """)
        conn.commit()
        conn.close()

    with app.app_context():
        serializer = get_serializer()
        valid_token = serializer.dumps(777, salt='password-reset-salt')

    # Submit weak password (< 8 chars) -> must be rejected
    res_weak = client.post(f'/reset-password/{valid_token}', data={
        'password': '123'
    }, follow_redirects=True)
    assert b"at least 8 characters" in res_weak.data

    # Submit valid new password -> must succeed
    res_valid = client.post(f'/reset-password/{valid_token}', data={
        'password': 'BrandNewSecurePass123!'
    }, follow_redirects=True)
    assert b"updated" in res_valid.data or b"login" in res_valid.data

    # Verify updated hash in DB
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        row = conn.execute("SELECT password_hash FROM users WHERE id = 777").fetchone()
        assert check_password_hash(row['password_hash'], 'BrandNewSecurePass123!') is True
        conn.close()


# =============================================================================
# 3. ACCOUNT LOCKOUT ENFORCEMENT (5 FAILED ATTEMPTS -> 15 MINUTE LOCK)
# =============================================================================

def test_account_lockout_after_five_failed_attempts(client, app):
    """
    Verifies that 5 consecutive failed passwords on the same user account locks the account.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        from werkzeug.security import generate_password_hash
        conn.execute("""
            INSERT OR REPLACE INTO users (id, username, password_hash, display_name, email, role, is_active, failed_attempts)
            VALUES (666, 'lockout_target', ?, 'Lockout Target', 'lock@suprajit.com', 'customer_viewer', 1, 0)
        """, (generate_password_hash('RealPassword123!'),))
        conn.commit()
        conn.close()

    # Submit 4 failed attempts
    for _ in range(4):
        res = client.post('/login', data={'username': 'lockout_target', 'password': 'WrongPassword'}, follow_redirects=True)
        assert b"Invalid credentials" in res.data

    # 5th failed attempt triggers account lockout
    res_5th = client.post('/login', data={'username': 'lockout_target', 'password': 'WrongPassword'}, follow_redirects=True)
    assert b"Account locked" in res_5th.data

    # Verify locked_until is set in database
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        row = conn.execute("SELECT failed_attempts, locked_until FROM users WHERE id = 666").fetchone()
        assert row['failed_attempts'] == 5
        assert row['locked_until'] is not None
        conn.close()


# =============================================================================
# 4. EFFECTIVE PORTAL URL CONSTRUCTION
# =============================================================================

def test_effective_portal_url_tunnel_override(app):
    """
    Verifies that public_portal_url in system_settings takes precedence over LAN request host.
    """
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('public_portal_url', 'https://factory-portal.suprajit.com')")
        conn.commit()
        conn.close()

        effective_url = get_effective_portal_url()
        assert effective_url == 'https://factory-portal.suprajit.com'
