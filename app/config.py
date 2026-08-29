import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask Settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("FLASK_ENV") == "testing" or os.getenv("PYTEST_CURRENT_TEST"):
            SECRET_KEY = "test-secret-key-for-testing-only"
        else:
            raise RuntimeError(
                "CRITICAL SECURITY ERROR: SECRET_KEY environment variable is not set. "
                "The application refuses to start with an insecure default key. "
                "Please set SECRET_KEY in your environment or .env file."
            )

    # OWASP/ASVS 5.0 Session Hardening
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

    # Path configuration
    import os
    import sys

    if getattr(sys, "frozen", False):
        # Running as PyInstaller EXE: BASE_DIR is the folder containing the .exe
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        # Running from source
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "data", "portal.db"))
    STORAGE_FOLDER = os.getenv("STORAGE_FOLDER", os.path.join(BASE_DIR, "storage"))

    # Waitress / App bindings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))

    # Mail Config (for password resets)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)


def get_config():
    return Config()
