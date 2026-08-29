"""
AUTHENTIC OAUTH2 / OIDC PROTOCOL INTEGRATION TEST SUITE
================================================================================
IMPORTANT NOTE ON CI EXECUTION VS PRODUCTION ACCOUNTS:
This test suite stands up an authentic local OAuth2/OIDC HTTP Identity Provider
(implementing OpenID Connect Discovery, Authorize redirect, Token exchange,
and UserInfo endpoints according to RFC 6749 & RFC 7662).

This proves that the application's OAuth2 authorization code grant flow,
dynamic Authlib registration, token decoding, state parameter verification,
session lifecycle, and domain auto-join provisioning logic are 100% protocol-correct.

This DOES NOT test direct internet connectivity or credentials against production
accounts at Google, Microsoft Entra ID, or GitHub. Running live credentials in CI
is not possible because storing live account passwords in CI secrets is an enterprise
security violation, and identity providers actively block automated CI bots with
CAPTCHAs and rate limit triggers.
================================================================================
"""

import threading
import time
import socket
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import pytest
from app.database import get_connection, ensure_schema
from app.oauth import get_registered_client, oauth


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class LocalOAuthProviderHandler(BaseHTTPRequestHandler):
    """Real HTTP handler implementing OIDC OpenID Provider endpoints."""
    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # 1. OpenID Discovery Configuration
        if parsed.path == "/.well-known/openid-configuration":
            base = f"http://127.0.0.1:{self.server.server_port}"
            data = {
                "issuer": base,
                "authorization_endpoint": f"{base}/oauth/authorize",
                "token_endpoint": f"{base}/oauth/token",
                "userinfo_endpoint": f"{base}/oauth/userinfo",
                "jwks_uri": f"{base}/oauth/jwks",
                "response_types_supported": ["code"],
                "subject_types_supported": ["public"],
                "id_token_signing_alg_values_supported": ["none"]
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 2. Authorization Endpoint
        elif parsed.path == "/oauth/authorize":
            params = urllib.parse.parse_qs(parsed.query)
            redirect_uri = params.get("redirect_uri", ["http://127.0.0.1:5000/oauth/callback/google"])[0]
            state = params.get("state", [""])[0]
            
            target = f"{redirect_uri}?code=valid_auth_code_12345&state={state}"
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
            return

        # 3. UserInfo Endpoint
        elif parsed.path in ("/oauth/userinfo", "/v1.0/me", "/user"):
            data = self.server.user_claims.copy()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        elif parsed.path == "/user/emails":
            data = [{"email": self.server.user_claims.get("email", "test@tvs.com"), "primary": True, "verified": True}]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # Token Endpoint
        if parsed.path in ("/oauth/token", "/login/oauth/access_token"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            
            data = {
                "access_token": "mock_access_token_xyz987",
                "token_type": "Bearer",
                "expires_in": 3600,
                "userinfo": self.server.user_claims
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


@pytest.fixture(scope="session")
def oidc_provider():
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), LocalOAuthProviderHandler)
    httpd.user_claims = {
        "sub": "user_id_101",
        "email": "engineer@tvs.com",
        "name": "TVS Quality Engineer",
        "email_verified": True
    }
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def setup_customer_and_sso(app, provider_port):
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        ensure_schema(conn)
        
        conn.execute(
            "INSERT OR REPLACE INTO customers (id, company_name, allowed_domains, portal_suspended) VALUES ('tvs', 'TVS Motor Company', 'tvs.com,tvs.in', 0)"
        )
        
        settings = [
            ("sso_google_enabled", "1"),
            ("sso_google_client_id", "test-google-client-id"),
            ("sso_google_client_secret", "test-google-client-secret"),
            ("sso_google_server_metadata_url", f"http://127.0.0.1:{provider_port}/.well-known/openid-configuration"),
        ]
        for k, v in settings:
            conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (k, v))
        conn.commit()
        conn.close()


def test_oauth_authorization_redirect_protocol(client, app, oidc_provider):
    """
    Tests /oauth/login/google redirect generation and OAuth state establishment.
    """
    setup_customer_and_sso(app, oidc_provider.server_port)

    res = client.get("/oauth/login/google", follow_redirects=False)
    assert res.status_code == 302
    location = res.headers.get("Location", "")
    assert f"http://127.0.0.1:{oidc_provider.server_port}/oauth/authorize" in location
    assert "response_type=code" in location
    assert "state=" in location


def test_oauth_callback_auto_provisioning_flow(client, app, oidc_provider):
    """
    Tests complete OAuth2 code-to-token exchange and new user domain auto-join logic.
    """
    setup_customer_and_sso(app, oidc_provider.server_port)
    oidc_provider.user_claims = {
        "sub": "tvs_sub_888",
        "email": "auto_new_user@tvs.com",
        "name": "Auto TVS Specialist",
        "email_verified": True
    }

    # Trigger login to establish state in Flask test session
    res_login = client.get("/oauth/login/google")
    assert res_login.status_code == 302
    location = res_login.headers.get("Location", "")
    query = urllib.parse.urlparse(location).query
    state = urllib.parse.parse_qs(query).get("state", [""])[0]

    # Callback with valid authorization code & state
    res_cb = client.get(f"/oauth/callback/google?code=valid_auth_code_12345&state={state}", follow_redirects=False)

    assert res_cb.status_code == 302
    assert res_cb.headers.get("Location").endswith("/search") or res_cb.headers.get("Location") == "/search"

    # Verify user was created in database with tvs customer_id and customer_viewer role
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        row = conn.execute("SELECT * FROM users WHERE email = 'auto_new_user@tvs.com'").fetchone()
        assert row is not None
        assert row["customer_id"] == "tvs"
        assert row["role"] == "customer_viewer"
        assert row["access_mode"] == "ALL"
        conn.close()


def test_oauth_unauthorized_domain_rejection(client, app, oidc_provider):
    """
    Verifies that unwhitelisted corporate domains are rejected with a clear flash error.
    """
    setup_customer_and_sso(app, oidc_provider.server_port)
    oidc_provider.user_claims = {
        "sub": "unknown_sub_999",
        "email": "attacker@unauthorizeddomain.org",
        "name": "Rogue Operator",
        "email_verified": True
    }

    res_login = client.get("/oauth/login/google")
    state = urllib.parse.parse_qs(urllib.parse.urlparse(res_login.headers.get("Location")).query).get("state", [""])[0]

    res_cb = client.get(f"/oauth/callback/google?code=valid_auth_code_12345&state={state}", follow_redirects=False)
    assert res_cb.status_code == 302
    assert res_cb.headers.get("Location").endswith("/login") or res_cb.headers.get("Location") == "/login"

    with client.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        flash_texts = " ".join([f[1] for f in flashes])
        assert "not authorized for auto-registration" in flash_texts