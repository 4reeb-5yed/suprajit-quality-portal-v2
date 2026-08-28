import os
import sys
from dotenv import load_dotenv

# Path configuration
if getattr(sys, 'frozen', False):
    # Running as PyInstaller EXE: BASE_DIR is the folder containing the .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running from source
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

def get_or_create_master_key():
    """
    Secrets management: Reads master encryption key from data/.master_key or generates a secure one.
    Never exposes plain encryption keys or passwords in the primary .env file.
    """
    key_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(key_dir, exist_ok=True)
    key_file = os.path.join(key_dir, '.master_key')
    
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if len(key) >= 32:
                    return key
        except Exception:
            pass
            
    import secrets
    new_key = secrets.token_hex(32)
    try:
        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(new_key)
    except Exception:
        pass
    return new_key

class Config:
    # Master App Secret Key (from .env or persistent .master_key file)
    SECRET_KEY = os.getenv("SECRET_KEY") or get_or_create_master_key()
    
    # OWASP/ASVS 5.0 Session Hardening
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800 # 30 minutes
    
    BASE_DIR = BASE_DIR
    ENV_PATH = ENV_PATH
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, 'data', 'portal.db'))
    STORAGE_FOLDER = os.getenv("STORAGE_FOLDER", os.path.join(BASE_DIR, 'storage'))
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", os.path.join(BASE_DIR, 'data', 'logs', 'suprajit.log'))
    
    # Sync Engine Defaults
    ROOT_SEARCH_PATH = os.getenv("ROOT_SEARCH_PATH", "")
    SYNC_TIME = os.getenv("SYNC_TIME", "01:00")
    
    # Waitress / App bindings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    
    # Mail Config (for password resets & alerts)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    
    # Telemetry / Health Alerts
    DEVELOPER_EMAIL = os.getenv("DEVELOPER_EMAIL", "")
    TELEMETRY_FREQUENCY = os.getenv("TELEMETRY_FREQUENCY", "daily")

def get_config():
    return Config()
