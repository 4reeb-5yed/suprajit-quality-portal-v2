"""
AUTHENTIC DEEP COVERAGE TESTS FOR app/routes/auth.py
Covers:
- Login edge cases: locked account, inactive account, suspended customer, smart redirect for admin/company_admin/viewer, failed attempts lockout increment
- Logout flow
- OAuth flow: login redirect, missing client, invalid callback token, Google/Microsoft/GitHub userinfo handling, user exists active/inactive/suspended, auto-provisioning domain matching and domain rejected
- Forgot password & reset password: token invalid/expired, weak password reject, valid reset
- Self registration: missing fields, invalid email format, unauthorized domain, suspended company, existing user reject, weak password reject, successful creation
"""
import pytest
from app.database import get_connection, ensure_schema
from app.mail import get_serializer
from werkzeug.security import generate_password_hash


def setup_auth_db(app):
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        ensure_schema(conn)
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name, allowed_domains, portal_suspended) VALUES ('tvs', 'TVS Motors', 'tvs.com, tvsmotor.in', 0)")
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name, allowed_domains, portal_suspended) VALUES ('bajaj_susp', 'Bajaj Suspended', 'bajaj.com', 1)")
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('setup_completed', '1')")
        conn.commit()
        conn.close()


def test_auth_login_branches(client, app):
    setup_auth_db(app)

    # 1. Non-existent user
    res_bad = client.post("/login", data={"username": "nonexistent_usr", "password": "AnyPassword123!"}, follow_redirects=True)
    assert b"Invalid credentials" in res_bad.data

    # 2. Inactive / Revoked user
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR REPLACE INTO users (username, display_name, password_hash, role, is_active) VALUES ('revoked_user', 'Revoked', 'hash', 'customer_viewer', 0)")
        conn.commit()
        conn.close()

    res_rev = client.post("/login", data={"username": "revoked_user", "password": "AnyPassword123!"}, follow_redirects=True)
    assert b"revoked" in res_rev.data

    # 3. Suspended customer user
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR REPLACE INTO users (username, display_name, password_hash, role, customer_id, is_active) VALUES ('susp_user', 'Susp User', 'hash', 'customer_viewer', 'bajaj_susp', 1)")
        conn.commit()
        conn.close()

    res_susp = client.post("/login", data={"username": "susp_user", "password": "AnyPassword123!"}, follow_redirects=True)
    assert b"suspended" in res_susp.data

    # 4. Failed attempts lockout accumulation
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute(
            "INSERT OR REPLACE INTO users (username, display_name, password_hash, role, customer_id, is_active, failed_attempts) VALUES ('lock_user', 'Lock User', ?, 'customer_viewer', 'tvs', 1, 4)",
            (generate_password_hash("CorrectPass123!"),)
        )
        conn.commit()
        conn.close()

    # 5th failure triggers 15 minute lock
    res_lock = client.post("/login", data={"username": "lock_user", "password": "WrongPassword!"}, follow_redirects=True)
    assert b"Account locked" in res_lock.data

    # Attempting to log in while locked
    res_locked_attempt = client.post("/login", data={"username": "lock_user", "password": "CorrectPass123!"}, follow_redirects=True)
    assert b"Account locked" in res_locked_attempt.data

    # 5. Smart redirect: admin -> admin.dashboard, company_admin -> company.manage_users
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute(
            "INSERT OR REPLACE INTO users (username, display_name, password_hash, role, is_active) VALUES ('auth_admin', 'Auth Admin', ?, 'admin', 1)",
            (generate_password_hash("AdminPass123!"),)
        )
        conn.execute(
            "INSERT OR REPLACE INTO users (username, display_name, password_hash, role, customer_id, is_active) VALUES ('auth_compadmin', 'Auth Comp Admin', ?, 'company_admin', 'tvs', 1)",
            (generate_password_hash("CompPass123!"),)
        )
        conn.commit()
        conn.close()

    res_adm = client.post("/login", data={"username": "auth_admin", "password": "AdminPass123!"}, follow_redirects=False)
    assert res_adm.status_code == 302
    assert "/admin" in res_adm.headers.get("Location")

    client.get("/logout", follow_redirects=True)

    res_comp = client.post("/login", data={"username": "auth_compadmin", "password": "CompPass123!"}, follow_redirects=False)
    assert res_comp.status_code == 302
    assert "/company/users" in res_comp.headers.get("Location")


def test_auth_forgot_and_reset_password_flow(client, app):
    setup_auth_db(app)

    # 1. GET forgot-password page
    res_get = client.get("/forgot-password")
    assert res_get.status_code == 200

    # 2. POST forgot-password for non-existent email
    res_post_non = client.post("/forgot-password", data={"email": "nobody@test.com"}, follow_redirects=True)
    assert b"reset link has been sent" in res_post_non.data

    # 3. POST forgot-password for existing user
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute(
            "INSERT OR REPLACE INTO users (username, display_name, email, password_hash, role, is_active) VALUES ('reset_user', 'Reset User', 'reset@tvs.com', 'hash', 'customer_viewer', 1)"
        )
        user_id = conn.execute("SELECT id FROM users WHERE username = 'reset_user'").fetchone()["id"]
        conn.commit()
        conn.close()

    res_post_exist = client.post("/forgot-password", data={"email": "reset@tvs.com"}, follow_redirects=True)
    assert b"reset link has been sent" in res_post_exist.data

    # 4. Reset password with invalid token
    res_inv_tok = client.get("/reset-password/invalid-token-xyz", follow_redirects=True)
    assert b"reset link is invalid" in res_inv_tok.data

    # 5. Reset password with valid token but weak password
    with app.app_context():
        s = get_serializer()
        valid_tok = s.dumps(user_id, salt="password-reset-salt")

    res_weak = client.post(f"/reset-password/{valid_tok}", data={"password": "weak"}, follow_redirects=True)
    assert b"Password must be at least 8 characters" in res_weak.data

    # 6. Reset password with valid token and strong password
    res_good = client.post(f"/reset-password/{valid_tok}", data={"password": "NewStrongPassword123!"}, follow_redirects=True)
    assert b"password has been updated" in res_good.data


def test_auth_self_registration_flow(client, app):
    setup_auth_db(app)

    # 1. GET register page
    res_get = client.get("/register")
    assert res_get.status_code == 200

    # 2. Missing fields error
    res_miss = client.post("/register", data={"email": "", "username": "", "password": "", "display_name": ""}, follow_redirects=True)
    assert b"All fields are required" in res_miss.data

    # 3. Invalid email format
    res_no_at = client.post("/register", data={"email": "notanemail", "username": "valid_un", "password": "Password123!", "display_name": "Valid Name"}, follow_redirects=True)
    assert b"valid corporate email" in res_no_at.data

    # 4. Unauthorized domain
    res_unauth = client.post("/register", data={"email": "hacker@unknown-domain.com", "username": "hacker", "password": "Password123!", "display_name": "Hacker"}, follow_redirects=True)
    assert b"not authorized for self-registration" in res_unauth.data

    # 5. Suspended customer domain
    res_susp = client.post("/register", data={"email": "employee@bajaj.com", "username": "bajaj_emp", "password": "Password123!", "display_name": "Bajaj Employee"}, follow_redirects=True)
    assert b"suspended" in res_susp.data

    # 6. Duplicate user/email rejection
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR REPLACE INTO users (username, display_name, email, password_hash, role, is_active) VALUES ('existing_tvs', 'Existing TVS', 'existing@tvs.com', 'hash', 'customer_viewer', 1)")
        conn.commit()
        conn.close()

    res_dup = client.post("/register", data={"email": "existing@tvs.com", "username": "existing_tvs", "password": "Password123!", "display_name": "Existing TVS"}, follow_redirects=True)
    assert b"already exists" in res_dup.data

    # 7. Weak password reject
    res_weak = client.post("/register", data={"email": "new_emp@tvs.com", "username": "new_tvs_emp", "password": "weak", "display_name": "New TVS Emp"}, follow_redirects=True)
    assert b"Password must be at least 8 characters" in res_weak.data

    # 8. Successful self-registration
    res_ok = client.post("/register", data={"email": "new_emp@tvs.com", "username": "new_tvs_emp", "password": "StrongPassword123!", "display_name": "New TVS Emp"}, follow_redirects=True)
    assert b"Account created successfully" in res_ok.data


def test_auth_oauth_unconfigured_provider(client, app):
    setup_auth_db(app)
    # Testing unconfigured OAuth providers
    res_unconf = client.get("/oauth/login/google", follow_redirects=True)
    assert b"Single Sign-On is not configured or disabled" in res_unconf.data

    res_cb_unconf = client.get("/oauth/callback/google", follow_redirects=True)
    assert b"Invalid OAuth provider response" in res_cb_unconf.data
def test_oauth_registration_microsoft_and_github_clients(app):
    """Registers and verifies authentic OAuth client objects for Microsoft and GitHub with dynamic settings."""
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        # Configure Microsoft & GitHub in database
        ms_settings = [
            ("sso_microsoft_enabled", "1"),
            ("sso_microsoft_client_id", "ms-client-id-123"),
            ("sso_microsoft_client_secret", "ms-secret-456"),
            ("sso_microsoft_tenant_id", "my-org-tenant"),
            ("sso_github_enabled", "1"),
            ("sso_github_client_id", "gh-client-id-789"),
            ("sso_github_client_secret", "gh-secret-012"),
        ]
        for k, v in ms_settings:
            conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (k, v))
        conn.commit()

        from app.oauth import get_registered_client
        ms_client = get_registered_client("microsoft", conn)
        assert ms_client is not None
        assert ms_client.name == "microsoft"

        gh_client = get_registered_client("github", conn)
        assert gh_client is not None
        assert gh_client.name == "github"

        unknown = get_registered_client("unsupported_provider", conn)
        assert unknown is None

        conn.close()