import logging
from typing import Any

from authlib.integrations.flask_client import OAuth

logger = logging.getLogger(__name__)
oauth = OAuth()


def init_oauth(app):
    """Initializes Authlib with the Flask app."""
    oauth.init_app(app)


def get_oauth_settings(db) -> dict[str, Any]:
    """Reads OAuth provider configurations from system_settings."""
    keys = [
        "sso_google_enabled",
        "sso_google_client_id",
        "sso_google_client_secret",
        "sso_google_server_metadata_url",
        "sso_microsoft_enabled",
        "sso_microsoft_client_id",
        "sso_microsoft_client_secret",
        "sso_microsoft_tenant_id",
        "sso_microsoft_server_metadata_url",
        "sso_github_enabled",
        "sso_github_client_id",
        "sso_github_client_secret",
        "sso_github_api_base_url",
        "sso_github_access_token_url",
        "sso_github_authorize_url",
    ]
    settings = {}
    for k in keys:
        row = db.execute("SELECT value FROM system_settings WHERE key = ?", (k,)).fetchone()
        settings[k] = row["value"] if row and row["value"] else ""
    return settings


def get_registered_client(provider_name: str, db):
    """
    Dynamically configures and returns an OAuth client based on current database settings.
    """
    settings = get_oauth_settings(db)

    if provider_name == "google":
        if settings.get("sso_google_enabled") != "1" or not settings.get("sso_google_client_id"):
            return None
        metadata_url = (
            settings.get("sso_google_server_metadata_url")
            or "https://accounts.google.com/.well-known/openid-configuration"
        )
        client = oauth.register(
            name="google",
            client_id=settings.get("sso_google_client_id"),
            client_secret=settings.get("sso_google_client_secret"),
            server_metadata_url=metadata_url,
            client_kwargs={"scope": "openid email profile"},
            overwrite=True,
        )
        if hasattr(client, "_server_metadata"):
            client._server_metadata = None
        return client

    elif provider_name == "microsoft":
        if settings.get("sso_microsoft_enabled") != "1" or not settings.get("sso_microsoft_client_id"):
            return None
        tenant_id = settings.get("sso_microsoft_tenant_id") or "common"
        metadata_url = (
            settings.get("sso_microsoft_server_metadata_url")
            or f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
        )
        return oauth.register(
            name="microsoft",
            client_id=settings.get("sso_microsoft_client_id"),
            client_secret=settings.get("sso_microsoft_client_secret"),
            server_metadata_url=metadata_url,
            client_kwargs={"scope": "openid email profile User.Read"},
            overwrite=True,
        )

    elif provider_name == "github":
        if settings.get("sso_github_enabled") != "1" or not settings.get("sso_github_client_id"):
            return None
        api_base = settings.get("sso_github_api_base_url") or "https://api.github.com/"
        access_token_url = settings.get("sso_github_access_token_url") or "https://github.com/login/oauth/access_token"
        authorize_url = settings.get("sso_github_authorize_url") or "https://github.com/login/oauth/authorize"
        return oauth.register(
            name="github",
            client_id=settings.get("sso_github_client_id"),
            client_secret=settings.get("sso_github_client_secret"),
            access_token_url=access_token_url,
            authorize_url=authorize_url,
            api_base_url=api_base,
            client_kwargs={"scope": "user:email read:user"},
            overwrite=True,
        )

    return None
