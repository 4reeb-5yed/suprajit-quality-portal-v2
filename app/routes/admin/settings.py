import re

from flask import flash, g, redirect, render_template, request, url_for

from app.database import GET_SETTING, SET_SETTING
from app.helpers import encrypt_password
from app.mail import (
    DEFAULT_INVITE_TEMPLATE,
    DEFAULT_RESET_TEMPLATE,
    DEFAULT_WELCOME_TEMPLATE,
)
from app.oauth import get_oauth_settings
from app.parser import DEFAULT_FILENAME_PATTERN
from app.routes.admin import admin_bp
from app.routes.admin.sso import save_sso_settings
from app.tunnel_manager import get_installed_tunnel_binaries, get_tunnel_status


@admin_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        # Batch ingest settings
        new_time = request.form.get("sync_time")
        new_storage = request.form.get("root_search_path")

        # Email settings
        m_srv = request.form.get("mail_server")
        m_prt = request.form.get("mail_port")
        m_usr = request.form.get("mail_username")
        m_pwd = request.form.get("mail_password")
        dev_email = request.form.get("developer_email")
        tel_freq = request.form.get("telemetry_frequency")

        # Filename Regex Pattern (supports single or multiple newline-separated patterns)
        regex_pattern = request.form.get("filename_regex_pattern")
        if regex_pattern is not None:
            # Validate each non-empty regex pattern line before saving
            lines = [
                line.strip()
                for line in regex_pattern.strip().splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            syntax_errors = []
            for line in lines:
                try:
                    re.compile(line)
                except re.error as e:
                    syntax_errors.append(f"'{line}': {e}")

            if syntax_errors:
                flash(f"Invalid Regular Expression Syntax: {'; '.join(syntax_errors)}", "error")
                return redirect(url_for("admin.settings"))

            g.db.execute(SET_SETTING, ("filename_regex_pattern", regex_pattern.strip()))

        # SSO Settings (Google, Microsoft, GitHub)
        save_sso_settings(request.form)

        # Public Portal URL (for Cloudflare/Tailscale/Ngrok tunnels)
        public_url = request.form.get("public_portal_url")
        if public_url is not None:
            g.db.execute(SET_SETTING, ("public_portal_url", public_url.strip()))

        # Configurable Email Templates
        t_welcome = request.form.get("template_welcome_email")
        t_invite = request.form.get("template_invite_email")
        t_reset = request.form.get("template_reset_password")
        if t_welcome is not None:
            g.db.execute(SET_SETTING, ("template_welcome_email", t_welcome))
        if t_invite is not None:
            g.db.execute(SET_SETTING, ("template_invite_email", t_invite))
        if t_reset is not None:
            g.db.execute(SET_SETTING, ("template_reset_password", t_reset))

        if new_time:
            g.db.execute(SET_SETTING, ("sync_time", new_time))
        if new_storage:
            g.db.execute(SET_SETTING, ("root_search_path", new_storage))
        if m_srv is not None:
            g.db.execute(SET_SETTING, ("mail_server", m_srv))
        if m_prt is not None:
            g.db.execute(SET_SETTING, ("mail_port", m_prt))
        if m_usr is not None:
            g.db.execute(SET_SETTING, ("mail_username", m_usr))
        if m_pwd:
            g.db.execute(SET_SETTING, ("mail_password", encrypt_password(m_pwd)))
        if dev_email is not None:
            g.db.execute(SET_SETTING, ("developer_email", dev_email))
        if tel_freq is not None:
            g.db.execute(SET_SETTING, ("telemetry_frequency", tel_freq))

        g.db.commit()
        flash("System configuration updated.", "success")
        return redirect(url_for("admin.settings"))

    def get_val(key, default):
        row = g.db.execute(GET_SETTING, (key,)).fetchone()
        return row["value"] if row else default

    sync_time = get_val("sync_time", "01:00")
    root_search_path = get_val("root_search_path", "")
    filename_regex_pattern = get_val("filename_regex_pattern", DEFAULT_FILENAME_PATTERN)
    public_portal_url = get_val("public_portal_url", "")

    template_welcome_email = get_val("template_welcome_email", DEFAULT_WELCOME_TEMPLATE)
    template_invite_email = get_val("template_invite_email", DEFAULT_INVITE_TEMPLATE)
    template_reset_password = get_val("template_reset_password", DEFAULT_RESET_TEMPLATE)

    m_srv = get_val("mail_server", "smtp.gmail.com")
    m_prt = get_val("mail_port", "587")
    m_usr = get_val("mail_username", "")
    has_mail_pwd = bool(get_val("mail_password", ""))
    dev_email = get_val("developer_email", "")
    tel_freq = get_val("telemetry_frequency", "daily")

    oauth_settings = get_oauth_settings(g.db)
    tunnel_status = get_tunnel_status()
    tunnel_binaries = get_installed_tunnel_binaries()

    system_admins = g.db.execute("SELECT * FROM users WHERE role = 'admin'").fetchall()
    customers_list = g.db.execute("SELECT id, company_name FROM customers ORDER BY company_name").fetchall()
    folder_mappings = g.db.execute("""
        SELECT fm.id, fm.folder_path, fm.customer_id, c.company_name, fm.created_at
        FROM folder_mappings fm
        LEFT JOIN customers c ON fm.customer_id = c.id
        ORDER BY fm.id ASC
    """).fetchall()

    return render_template(
        "admin/settings/index.html",
        developer_email=dev_email,
        telemetry_frequency=tel_freq,
        sync_time=sync_time,
        root_search_path=root_search_path,
        folder_mappings=folder_mappings,
        customers_list=customers_list,
        filename_regex_pattern=filename_regex_pattern,
        default_regex_pattern=DEFAULT_FILENAME_PATTERN,
        public_portal_url=public_portal_url,
        template_welcome_email=template_welcome_email,
        template_invite_email=template_invite_email,
        template_reset_password=template_reset_password,
        mail_server=m_srv,
        mail_port=m_prt,
        mail_username=m_usr,
        has_mail_password=has_mail_pwd,
        oauth_settings=oauth_settings,
        tunnel_status=tunnel_status,
        tunnel_binaries=tunnel_binaries,
        system_admins=system_admins,
    )


@admin_bp.route("/folder_mappings/add", methods=["POST"])
def add_folder_mapping():
    """Maps a filesystem directory to a specific tenant / customer."""
    folder_path = request.form.get("folder_path", "").strip()
    customer_id = request.form.get("customer_id", "").strip() or None

    if not folder_path:
        flash("Folder path is required.", "error")
    else:
        try:
            g.db.execute(
                "INSERT INTO folder_mappings (folder_path, customer_id) VALUES (?, ?)",
                (folder_path, customer_id),
            )
            g.db.commit()
            flash("Root folder mapped successfully.", "success")
        except Exception as e:
            flash(f"Error mapping folder: {e}", "error")

    return redirect(url_for("admin.settings"))


@admin_bp.route("/folder_mappings/delete", methods=["POST"])
def delete_folder_mapping():
    """Removes a folder mapping."""
    mapping_id = request.form.get("mapping_id")
    if mapping_id:
        g.db.execute("DELETE FROM folder_mappings WHERE id = ?", (mapping_id,))
        g.db.commit()
        flash("Folder mapping removed.", "success")
    return redirect(url_for("admin.settings"))
