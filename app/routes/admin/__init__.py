from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from werkzeug.security import generate_password_hash

from app.database import SET_SETTING

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
        abort(403)
    # Enforce Setup Wizard Trap: Force bootstrap_admin to complete initial setup if not completed
    setup_done = g.db.execute("SELECT value FROM system_settings WHERE key = 'setup_completed'").fetchone()
    if (
        (not setup_done or setup_done["value"] != "1")
        and current_user.username == "bootstrap_admin"
        and request.endpoint not in ("admin.setup", "auth.logout", "static")
    ):
        return redirect(url_for("admin.setup"))


@admin_bp.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        new_pass = request.form.get("new_password")
        admin_email = request.form.get("admin_email")
        dev_email = request.form.get("developer_email", "")

        m_srv = request.form.get("mail_server")
        m_prt = request.form.get("mail_port")
        m_usr = request.form.get("mail_username")
        m_pwd = request.form.get("mail_password")

        if new_pass and len(new_pass) >= 8:
            g.db.execute(
                "UPDATE users SET password_hash = ?, email = ? WHERE id = ?",
                (generate_password_hash(new_pass), admin_email, current_user.id),
            )
            g.db.execute(SET_SETTING, ("setup_completed", "1"))

            if m_srv:
                g.db.execute(SET_SETTING, ("mail_server", m_srv))
            if m_prt:
                g.db.execute(SET_SETTING, ("mail_port", m_prt))
            if m_usr:
                g.db.execute(SET_SETTING, ("mail_username", m_usr))
            if m_pwd:
                from app.helpers import encrypt_password

                g.db.execute(SET_SETTING, ("mail_password", encrypt_password(m_pwd)))

            if dev_email:
                g.db.execute(SET_SETTING, ("developer_email", dev_email))

            g.db.commit()
            flash("Initial configuration complete. Your system is secured and SMTP is ready.", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Password must be at least 8 characters.", "error")

    return render_template("admin/setup.html")


# Import sibling route modules to register all endpoints on admin_bp
from app.routes.admin import customers, dashboard, diagnostics, settings, sso, tunnel, users  # noqa: E402, F401
