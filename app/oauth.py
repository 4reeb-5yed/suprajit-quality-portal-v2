import logging
from typing import Dict, Any, Optional
from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for, g

logger = logging.getLogger(__name__)
oauth = OAuth()

def init_oauth(app):
    """Initializes Authlib with the Flask app."""
    oauth.init_app(app)

def get_oauth_settings(db) -> Dict[str, Any]:
    """Reads OAuth provider configurations from system_settings."""
    keys = [
        'sso_google_enabled', 'sso_google_client_id', 'sso_google_client_secret',
        'sso_microsoft_enabled', 'sso_microsoft_client_id', 'sso_microsoft_client_secret', 'sso_microsoft_tenant_id',
        'sso_github_enabled', 'sso_github_client_id', 'sso_github_client_secret'
    ]
    settings = {}
    for k in keys:
        row = db.execute("SELECT value FROM system_settings WHERE key = ?", (k,)).fetchone()
        settings[k] = row['value'] if row and row['value'] else ""
    return settings

def get_registered_client(provider_name: str, db):
    """
    Dynamically configures and returns an OAuth client based on current database settings.
    """
    settings = get_oauth_settings(db)
    
    if provider_name == 'google':
        if settings.get('sso_google_enabled') != '1' or not settings.get('sso_google_client_id'):
            return None
        return oauth.register(
            name='google',
            client_id=settings.get('sso_google_client_id'),
            client_secret=settings.get('sso_google_client_secret'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
            overwrite=True
        )

    elif provider_name == 'microsoft':
        if settings.get('sso_microsoft_enabled') != '1' or not settings.get('sso_microsoft_client_id'):
            return None
        tenant_id = settings.get('sso_microsoft_tenant_id') or 'common'
        return oauth.register(
            name='microsoft',
            client_id=settings.get('sso_microsoft_client_id'),
            client_secret=settings.get('sso_microsoft_client_secret'),
            server_metadata_url=f'https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile User.Read'},
            overwrite=True
        )

    elif provider_name == 'github':
        if settings.get('sso_github_enabled') != '1' or not settings.get('sso_github_client_id'):
            return None
        return oauth.register(
            name='github',
            client_id=settings.get('sso_github_client_id'),
            client_secret=settings.get('sso_github_client_secret'),
            access_token_url='https://github.com/login/oauth/access_token',
            authorize_url='https://github.com/login/oauth/authorize',
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email read:user'},
            overwrite=True
        )
        
    return None
