from flask import g

from app.database import SET_SETTING


def save_sso_settings(form_data):
    """Saves Google, Microsoft, and GitHub SSO/OAuth 2.0 configuration into system_settings."""
    sso_keys = [
        "sso_google_enabled",
        "sso_google_client_id",
        "sso_google_client_secret",
        "sso_microsoft_enabled",
        "sso_microsoft_client_id",
        "sso_microsoft_client_secret",
        "sso_microsoft_tenant_id",
        "sso_github_enabled",
        "sso_github_client_id",
        "sso_github_client_secret",
    ]
    for sk in sso_keys:
        val = form_data.get(sk)
        if sk.endswith("_enabled"):
            g.db.execute(SET_SETTING, (sk, "1" if val == "1" else "0"))
        elif val is not None:
            g.db.execute(SET_SETTING, (sk, val.strip()))
