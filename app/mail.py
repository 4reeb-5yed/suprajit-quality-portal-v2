import smtplib
from email.message import EmailMessage

from flask import current_app, request

from app.database import get_connection

DEFAULT_WELCOME_TEMPLATE = """Welcome to the Suprajit Quality Portal!

An administrator has created an account for you.
You can log in here: {portal_url}

Your Username: {username}
Your Temporary Password: {temporary_password}

For security reasons, please log in and change your password immediately.

--
Suprajit Quality Assurance Team"""

DEFAULT_INVITE_TEMPLATE = """Hello,

You have been invited{company_tag} to access the Suprajit Quality Inspection Portal.

----------------------------------------
Portal URL: {portal_url}
Username  : {username}
Temporary Password: {temporary_password}
----------------------------------------

Next Steps:
1. Open the portal URL: {portal_url}
2. Sign in with your username and temporary password.
3. You can update your password at any time via your account settings.

If you did not expect this invitation, please contact your organization administrator.

--
Suprajit Quality Assurance Team"""

DEFAULT_RESET_TEMPLATE = """Click the link below to reset your Suprajit Portal password:
{reset_url}

This link is valid for 1 hour. If you did not request a password reset, please ignore this email.

--
Suprajit Quality Assurance Team"""


def get_email_setting(key, default=""):
    try:
        conn = get_connection(current_app.config["DATABASE_PATH"])
        row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default
    except Exception:
        return default


def get_effective_portal_url() -> str:
    """
    Resolves the public portal URL.
    1. If custom 'public_portal_url' is set in settings, uses that.
    2. Otherwise uses current request.host_url or localhost.
    """
    configured = get_email_setting("public_portal_url", "").strip()
    if configured:
        return configured.rstrip("/")
    try:
        if request and request.host_url:
            return request.host_url.rstrip("/")
    except Exception:
        pass
    return "http://localhost:5000"


def _send_smtp(subject, recipients, body):
    smtp_server = get_email_setting("mail_server", "smtp.gmail.com")
    smtp_port = int(get_email_setting("mail_port", "587"))
    smtp_user = get_email_setting("mail_username", "")
    smtp_pass_cipher = get_email_setting("mail_password", "")
    smtp_pass = ""
    if smtp_pass_cipher:
        from app.helpers import decrypt_password

        smtp_pass = decrypt_password(smtp_pass_cipher)

    if not smtp_user or not smtp_pass:
        current_app.logger.error("Email credentials not configured in settings.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    use_tls = get_email_setting("mail_use_tls", "1") != "0"

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            if smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"SMTP Error: {e}")
        return False


def get_serializer():
    from itsdangerous import URLSafeTimedSerializer

    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def send_password_reset_email(user_email: str, user_id: int):
    """Generates a token and sends a configurable password reset email."""
    try:
        s = get_serializer()
        token = s.dumps(user_id, salt="password-reset-salt")
        base_url = get_effective_portal_url()
        reset_url = f"{base_url}/reset-password/{token}"

        template = get_email_setting("template_reset_password", DEFAULT_RESET_TEMPLATE)
        body = template.format(reset_url=reset_url)
        return _send_smtp("Suprajit Quality Portal - Password Reset", [user_email], body)
    except Exception as e:
        current_app.logger.error(f"Failed to send reset email: {e}")
        return False


def send_welcome_email(user_email: str, username: str, raw_password: str, login_url: str = ""):
    """Sends a configurable welcome email with initial login credentials."""
    try:
        if not login_url:
            login_url = f"{get_effective_portal_url()}/login"

        template = get_email_setting("template_welcome_email", DEFAULT_WELCOME_TEMPLATE)
        body = template.format(portal_url=login_url, username=username, temporary_password=raw_password)

        return _send_smtp("Welcome to Suprajit Quality Portal - Your Login Info", [user_email], body)
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email: {e}")
        return False


def send_bulk_invite_email(
    user_email: str, username: str, raw_password: str, company_name: str = "", login_url: str = ""
):
    """Sends a configurable bulk invite email with login credentials."""
    try:
        if not login_url:
            login_url = f"{get_effective_portal_url()}/login"

        company_tag = f" on behalf of {company_name}" if company_name else ""
        template = get_email_setting("template_invite_email", DEFAULT_INVITE_TEMPLATE)
        body = template.format(
            portal_url=login_url,
            username=username,
            temporary_password=raw_password,
            company_name=company_name,
            company_tag=company_tag,
        )

        return _send_smtp("Invitation to Suprajit Quality Inspection Portal", [user_email], body)
    except Exception as e:
        current_app.logger.error(f"Failed to send bulk invite email to {user_email}: {e}")
        return False


def send_heartbeat_email(files_processed: int, files_failed: int, status: str, error_msg: str):
    """Sends a daily telemetry/health report to Canspirit developers."""
    try:
        dev_email = get_email_setting("developer_email", "")
        if not dev_email:
            return False

        subject = f"[{status.upper()}] Suprajit Portal Telemetry"

        body = "Automated System Health Report\n\n"
        body += f"Sync Status: {status.upper()}\n"
        body += f"Files Processed: {files_processed}\n"
        body += f"Files Failed: {files_failed}\n"

        if error_msg:
            body += f"\nCRITICAL ERROR LOG:\n{error_msg}\n"

        body += "\n\n--\nGenerated by Canspirit Suprajit Server."

        return _send_smtp(subject, [dev_email], body)
    except Exception as e:
        current_app.logger.error(f"Failed to send telemetry email: {e}")
        return False
