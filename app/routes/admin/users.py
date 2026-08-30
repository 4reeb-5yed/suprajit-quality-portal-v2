import csv
import io
import secrets
import string
import threading

from flask import current_app, flash, g, redirect, request, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

from app.database import INSERT_USER, TOGGLE_USER_ACCESS
from app.mail import send_bulk_invite_email, send_welcome_email
from app.routes.admin import admin_bp


@admin_bp.route("/customers/add_user", methods=["POST"])
def add_user():
    customer_id = request.form.get("customer_id") or None
    role = request.form.get("role", "customer_viewer")
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip() or None
    password = request.form.get("password", "")
    display_name = request.form.get("display_name", "").strip() or username
    access_mode = request.form.get("access_mode", "ALL")
    redirect_url = request.form.get("redirect_url")

    if not username or not password:
        flash("Username and password are required.", "error")
        if redirect_url:
            return redirect(redirect_url)
        if role == "admin":
            return redirect(url_for("admin.settings"))
        return redirect(url_for("admin.customers"))

    pwd_hash = generate_password_hash(password)

    try:
        g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, role, customer_id, access_mode))
        g.db.commit()

        # Send welcome email if email was provided
        if email:
            app_context = current_app._get_current_object().app_context()
            host_login = f"{request.host_url.rstrip('/')}/login"

            def background_mail(url):
                with app_context:
                    send_welcome_email(email, username, password, url)

            threading.Thread(target=background_mail, args=(host_login,)).start()
            flash(f"Account '{username}' created. A welcome email is being sent to {email}.", "success")
        else:
            flash(f"Account '{username}' created successfully.", "success")
    except Exception as e:
        flash(f"Database Error: {e}", "error")
        print(f"User Creation Error: {e}")

    if redirect_url:
        return redirect(redirect_url)
    if role == "admin":
        return redirect(url_for("admin.settings"))
    return redirect(url_for("admin.customers"))


@admin_bp.route("/users/bulk_import", methods=["POST"])
def bulk_import_users():
    """Allows bulk onboarding of users / admins via CSV upload or raw text paste."""
    customer_id = request.form.get("customer_id") or None
    target_role = request.form.get("role", "customer_viewer")
    redirect_url = request.form.get("redirect_url")
    raw_text = request.form.get("bulk_text", "").strip()
    uploaded_file = request.files.get("bulk_file")
    send_invites = request.form.get("send_invites") == "1"

    # Get company name for email context
    company_name = ""
    if customer_id:
        cust_row = g.db.execute("SELECT company_name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if cust_row:
            company_name = cust_row["company_name"]

    rows_to_process = []

    # 1. Parse uploaded CSV file if provided
    if uploaded_file and uploaded_file.filename:
        try:
            stream = io.StringIO(uploaded_file.stream.read().decode("utf-8", errors="ignore"))
            reader = csv.reader(stream)
            for row in reader:
                if not row or not any(row):
                    continue
                # Skip header row if present
                first_cell = row[0].strip().lower()
                if first_cell in ("email", "username", "name", "full_name"):
                    continue
                rows_to_process.append([c.strip() for c in row])
        except Exception as e:
            flash(f"Error reading CSV file: {e}", "error")
            return redirect(redirect_url or url_for("admin.customers"))

    # 2. Parse raw text paste (comma, semicolon, or newline separated)
    if raw_text:
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if "," in line:
                parts = [p.strip() for p in line.split(",")]
            elif ";" in line:
                parts = [p.strip() for p in line.split(";")]
            elif "\t" in line:
                parts = [p.strip() for p in line.split("\t")]
            else:
                parts = [line]

            if parts and parts[0].lower() not in ("email", "username", "name", "full_name"):
                rows_to_process.append(parts)

    if not rows_to_process:
        flash("No valid email addresses or records found in upload/paste.", "warning")
        return redirect(redirect_url or url_for("admin.customers"))

    created_count = 0
    skipped_count = 0
    errors = []
    invites_to_dispatch = []

    def generate_random_pwd():
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(10))

    for item in rows_to_process:
        # Schema flexible parsing:
        # Format 1: [email]
        # Format 2: [email, name]
        # Format 3: [email, name, username]
        # Format 4: [email, name, username, role]
        email = None
        display_name = None
        username = None
        user_role = target_role

        if len(item) == 1:
            val = item[0]
            if "@" in val:
                email = val
                username = val.split("@")[0].lower()
                display_name = val.split("@")[0].replace(".", " ").replace("_", " ").title()
            else:
                username = val.lower()
                display_name = val
        elif len(item) == 2:
            if "@" in item[0]:
                email, display_name = item[0], item[1]
                username = email.split("@")[0].lower()
            else:
                username, display_name = item[0], item[1]
        elif len(item) >= 3:
            email = item[0] if "@" in item[0] else None
            display_name = item[1]
            username = item[2].lower()
            if len(item) >= 4 and item[3] in ("customer_viewer", "company_admin", "admin"):
                user_role = item[3]

        if not username:
            skipped_count += 1
            continue

        # Clean username
        username = "".join(c for c in username if c.isalnum() or c in ("_", "-"))

        # Check existing user
        existing = g.db.execute(
            "SELECT id FROM users WHERE username = ? OR (email IS NOT NULL AND email = ?)", (username, email)
        ).fetchone()
        if existing:
            skipped_count += 1
            continue

        temp_pwd = generate_random_pwd()
        pwd_hash = generate_password_hash(temp_pwd)

        try:
            g.db.execute(
                INSERT_USER, (username, email, pwd_hash, display_name or username, user_role, customer_id, "ALL")
            )
            created_count += 1
            if email and send_invites:
                invites_to_dispatch.append((email, username, temp_pwd))
        except Exception as e:
            skipped_count += 1
            errors.append(f"{username}: {e}")

    g.db.commit()

    # Dispatch invite emails in background thread
    if invites_to_dispatch:
        app_context = current_app._get_current_object().app_context()
        host_login = f"{request.host_url.rstrip('/')}/login"

        def run_invites(inv_list, url, comp_name):
            with app_context:
                for mail, uname, pwd in inv_list:
                    send_bulk_invite_email(mail, uname, pwd, comp_name, url)

        threading.Thread(target=run_invites, args=(invites_to_dispatch, host_login, company_name)).start()

    msg = f"Bulk Provisioning Completed: {created_count} accounts created successfully."
    if skipped_count > 0:
        msg += f" {skipped_count} skipped (duplicates or invalid)."
    if invites_to_dispatch:
        msg += f" {len(invites_to_dispatch)} welcome invite emails dispatched."

    flash(msg, "success" if created_count > 0 else "warning")
    return redirect(redirect_url or url_for("admin.customers"))


@admin_bp.route("/customers/toggle_user", methods=["POST"])
def toggle_user():
    user_id = request.form.get("user_id")
    new_status = int(request.form.get("is_active", 1))
    redirect_url = request.form.get("redirect_url")

    if user_id:
        g.db.execute(TOGGLE_USER_ACCESS, (new_status, user_id))
        g.db.commit()
        action = "Granted" if new_status == 1 else "Revoked"
        flash(f"Access {action} successfully.", "success")

    if redirect_url:
        return redirect(redirect_url)
    return redirect(url_for("admin.customers"))


@admin_bp.route("/users/delete", methods=["POST"])
def delete_user():
    user_id = request.form.get("user_id")

    if str(user_id) == str(current_user.id):
        flash("You cannot delete your currently active account.", "error")
        return redirect(url_for("admin.customers"))

    user = g.db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.customers"))

    if user["role"] == "admin":
        admin_count = g.db.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'").fetchone()["c"]
        if admin_count <= 1:
            flash("Cannot delete the last remaining administrator account. Create a new one first.", "error")
            return redirect(url_for("admin.customers"))

    g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    g.db.commit()
    flash("User deleted successfully.", "success")
    if user["role"] == "admin":
        return redirect(url_for("admin.settings"))
    return redirect(url_for("admin.customers"))
