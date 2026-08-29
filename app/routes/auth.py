from datetime import datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import limiter
from app.auth_models import User
from app.database import (
    GET_USER_BY_EMAIL,
    GET_USER_BY_USERNAME,
    INSERT_USER,
    UPDATE_USER_LOCKOUT,
    UPDATE_USER_PASSWORD,
)
from app.mail import get_serializer, send_password_reset_email
from app.oauth import get_oauth_settings, get_registered_client

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("portal.search"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        row = g.db.execute(GET_USER_BY_USERNAME, (username, username)).fetchone()
        if not row:
            flash("Invalid credentials", "error")
            oauth_settings = get_oauth_settings(g.db)
            return render_template("auth/login.html", oauth_settings=oauth_settings)

        # Check Lockout
        if row["locked_until"]:
            locked_until = datetime.strptime(row["locked_until"], "%Y-%m-%d %H:%M:%S")
            if datetime.utcnow() < locked_until:
                flash("Account locked due to too many failed attempts. Try again later.", "error")
                oauth_settings = get_oauth_settings(g.db)
                return render_template("auth/login.html", oauth_settings=oauth_settings)

        # Check if user is disabled
        if row["is_active"] == 0:
            flash("Your account has been revoked. Contact the administrator.", "error")
            oauth_settings = get_oauth_settings(g.db)
            return render_template("auth/login.html", oauth_settings=oauth_settings)

        # Check if customer portal is globally suspended
        if row["role"] != "admin":
            cust = g.db.execute("SELECT portal_suspended FROM customers WHERE id = ?", (row["customer_id"],)).fetchone()
            if cust and cust["portal_suspended"] == 1:
                flash("Portal access for this customer is currently suspended.", "error")
                oauth_settings = get_oauth_settings(g.db)
                return render_template("auth/login.html", oauth_settings=oauth_settings)

        # Check Password
        if check_password_hash(row["password_hash"], password):
            # Reset failures
            g.db.execute(UPDATE_USER_LOCKOUT, (0, None, row["id"]))
            g.db.commit()

            user_obj = User(row)
            login_user(user_obj)

            # Log audit
            try:
                g.db.execute(
                    "INSERT INTO audit_log (user_id, action, client_ip) VALUES (?, ?, ?)",
                    (row["id"], "login", request.remote_addr),
                )
                g.db.commit()
            except Exception as e:
                current_app.logger.error(f"Failed to log audit for user {row['id']}: {e}")

            # Smart role-based destination redirect
            if user_obj.is_admin:
                return redirect(url_for("admin.dashboard"))
            elif user_obj.is_company_admin:
                return redirect(url_for("company.manage_users"))
            else:
                return redirect(url_for("portal.search"))
        else:
            # Increment failures
            failures = row["failed_attempts"] + 1
            locked_until = None
            if failures >= 5:
                locked_until = (datetime.utcnow() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
                flash("Account locked for 15 minutes due to too many failed attempts.", "error")
            else:
                flash("Invalid credentials", "error")

            g.db.execute(UPDATE_USER_LOCKOUT, (failures, locked_until, row["id"]))
            g.db.commit()

    oauth_settings = get_oauth_settings(g.db)
    return render_template("auth/login.html", oauth_settings=oauth_settings)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/oauth/login/<provider>")
def oauth_login(provider):
    """Redirects user to Microsoft / Google / GitHub OAuth."""
    client = get_registered_client(provider, g.db)
    if not client:
        flash(f"{provider.capitalize()} Single Sign-On is not configured or disabled.", "error")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.oauth_callback", provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)


@auth_bp.route("/oauth/callback/<provider>")
def oauth_callback(provider):
    """Handles OAuth response, verifies verified email, auto-provisions or logs in user."""
    client = get_registered_client(provider, g.db)
    if not client:
        flash("Invalid OAuth provider response.", "error")
        return redirect(url_for("auth.login"))

    try:
        token = client.authorize_access_token()
    except Exception as e:
        flash(f"OAuth Authentication Failed: {e}", "error")
        return redirect(url_for("auth.login"))

    email = None
    display_name = None

    if provider == "google":
        user_info = token.get("userinfo")
        if not user_info:
            user_info = client.userinfo()
        email = user_info.get("email")
        display_name = user_info.get("name") or user_info.get("given_name")

    elif provider == "microsoft":
        user_info = token.get("userinfo")
        if not user_info:
            resp = client.get("https://graph.microsoft.com/v1.0/me", token=token)
            user_info = resp.json()
        email = user_info.get("mail") or user_info.get("userPrincipalName")
        display_name = user_info.get("displayName")

    elif provider == "github":
        resp = client.get("user", token=token)
        profile = resp.json()
        display_name = profile.get("name") or profile.get("login")

        # GitHub primary verified email fetch
        emails_resp = client.get("user/emails", token=token)
        emails_data = emails_resp.json()
        if isinstance(emails_data, list):
            for em in emails_data:
                if em.get("primary") and em.get("verified"):
                    email = em.get("email")
                    break
            if not email and emails_data:
                email = emails_data[0].get("email")
        else:
            email = profile.get("email")

    if not email:
        flash("Could not retrieve a verified email address from your identity provider.", "error")
        return redirect(url_for("auth.login"))

    email = email.lower().strip()

    # 1. Check if user already exists
    user_row = g.db.execute(
        "SELECT * FROM users WHERE email = ? OR username = ?", (email, email.split("@")[0])
    ).fetchone()

    if user_row:
        if user_row["is_active"] == 0:
            flash("Your account has been revoked. Contact the administrator.", "error")
            return redirect(url_for("auth.login"))

        if user_row["role"] != "admin" and user_row["customer_id"]:
            cust = g.db.execute(
                "SELECT portal_suspended FROM customers WHERE id = ?", (user_row["customer_id"],)
            ).fetchone()
            if cust and cust["portal_suspended"] == 1:
                flash("Portal access for this customer is currently suspended.", "error")
                return redirect(url_for("auth.login"))

        user_obj = User(user_row)
        login_user(user_obj)
        g.db.execute(
            "INSERT INTO audit_log (user_id, action, client_ip) VALUES (?, ?, ?)",
            (user_row["id"], f"oauth_login_{provider}", request.remote_addr),
        )
        g.db.commit()
        flash(f"Welcome back, {user_row['display_name']}!", "success")
        return redirect(url_for("portal.search"))

    # 2. Auto-Provisioning via Domain Whitelist
    domain = email.split("@")[1].strip() if "@" in email else ""
    customers = g.db.execute(
        "SELECT id, company_name, allowed_domains, portal_suspended FROM customers WHERE allowed_domains IS NOT NULL AND allowed_domains != ''"
    ).fetchall()
    matched_customer = None

    for cust in customers:
        allowed = [d.strip().lower() for d in cust["allowed_domains"].split(",") if d.strip()]
        if domain in allowed:
            matched_customer = cust
            break

    if not matched_customer:
        flash(
            f"Your email domain '@{domain}' is not authorized for auto-registration. Please contact your organization administrator.",
            "error",
        )
        return redirect(url_for("auth.login"))

    if matched_customer["portal_suspended"]:
        flash("Portal access for your organization is currently suspended.", "error")
        return redirect(url_for("auth.login"))

    # Auto-create new user account
    import secrets

    username = email.split("@")[0].lower()
    existing_un = g.db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing_un:
        username = f"{username}_{secrets.token_hex(2)}"

    random_pwd_hash = generate_password_hash(secrets.token_urlsafe(24))
    full_name = display_name or username.replace(".", " ").title()

    g.db.execute(
        INSERT_USER, (username, email, random_pwd_hash, full_name, "customer_viewer", matched_customer["id"], "ALL")
    )
    g.db.commit()

    new_user_row = g.db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    user_obj = User(new_user_row)
    login_user(user_obj)

    g.db.execute(
        "INSERT INTO audit_log (user_id, action, client_ip) VALUES (?, ?, ?)",
        (new_user_row["id"], f"oauth_register_{provider}", request.remote_addr),
    )
    g.db.commit()

    flash(f"Account auto-provisioned! Welcome to {matched_customer['company_name']}.", "success")
    return redirect(url_for("portal.search"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        row = g.db.execute(GET_USER_BY_EMAIL, (email,)).fetchone()
        if row:
            send_password_reset_email(email, row["id"])
        flash("If an account with that email exists, a reset link has been sent.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    s = get_serializer()
    try:
        user_id = s.loads(token, salt="password-reset-salt", max_age=3600)
    except Exception:
        flash("The reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("password")
        import re

        if (
            len(new_password) < 8
            or not re.search(r"\d", new_password)
            or not re.search(r"[A-Z]", new_password)
            or not re.search(r"[@$!%*?&#]", new_password)
        ):
            flash(
                "Password must be at least 8 characters long and contain a number, an uppercase letter, and a special character.",
                "error",
            )
            return render_template("auth/reset_password.html")

        p_hash = generate_password_hash(new_password)
        g.db.execute(UPDATE_USER_PASSWORD, (p_hash, user_id))
        g.db.commit()
        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Allows employees from authorized company email domains to auto-join their company."""
    if current_user.is_authenticated:
        return redirect(url_for("portal.search"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("display_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not username or not password or not full_name:
            flash("All fields are required.", "error")
            return render_template("auth/register.html")

        if "@" not in email:
            flash("Please enter a valid corporate email address.", "error")
            return render_template("auth/register.html")

        domain = email.split("@")[1].strip()

        # Find matching customer with domain whitelist
        customers = g.db.execute(
            "SELECT id, company_name, allowed_domains, portal_suspended FROM customers WHERE allowed_domains IS NOT NULL AND allowed_domains != ''"
        ).fetchall()
        matched_customer = None

        for cust in customers:
            allowed = [d.strip().lower() for d in cust["allowed_domains"].split(",") if d.strip()]
            if domain in allowed:
                matched_customer = cust
                break

        if not matched_customer:
            flash(
                f"The email domain '@{domain}' is not authorized for self-registration. Please contact your organization administrator.",
                "error",
            )
            return render_template("auth/register.html")

        if matched_customer["portal_suspended"]:
            flash("Portal access for your organization is currently suspended.", "error")
            return render_template("auth/register.html")

        # Check existing username or email
        existing = g.db.execute(
            "SELECT id FROM users WHERE username = ? OR (email IS NOT NULL AND email = ?)", (username, email)
        ).fetchone()
        if existing:
            flash(
                "An account with that username or email address already exists. Please log in or reset your password.",
                "error",
            )
            return render_template("auth/register.html")

        # Validate password complexity
        import re

        if (
            len(password) < 8
            or not re.search(r"\d", password)
            or not re.search(r"[A-Z]", password)
            or not re.search(r"[@$!%*?&#]", password)
        ):
            flash(
                "Password must be at least 8 characters long and contain a number, an uppercase letter, and a special character.",
                "error",
            )
            return render_template("auth/register.html")

        pwd_hash = generate_password_hash(password)

        try:
            g.db.execute(
                INSERT_USER, (username, email, pwd_hash, full_name, "customer_viewer", matched_customer["id"], "ALL")
            )
            g.db.commit()
            flash(
                f"Account created successfully! Welcome to {matched_customer['company_name']}. You can now log in.",
                "success",
            )
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Registration Error: {e}", "error")
            return render_template("auth/register.html")

    return render_template("auth/register.html")
