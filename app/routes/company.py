from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps

company_bp = Blueprint('company', __name__, url_prefix='/company')

def company_admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_authenticated and (current_user.role == 'company_admin' or current_user.is_admin)):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@company_bp.route('/users')
@company_admin_required
def manage_users():
    customer_id = current_user.customer_id
    if not customer_id and current_user.is_admin:
        # If a master admin visits /company/users without customer context, redirect to /admin/customers
        return redirect(url_for('admin.customers'))
        
    customer = g.db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not customer:
        flash("Company profile not found.", "error")
        return redirect(url_for('portal.search'))
        
    users = g.db.execute("SELECT * FROM users WHERE customer_id = ? ORDER BY created_at DESC", (customer_id,)).fetchall()
    allowed_recipes = g.db.execute("SELECT * FROM customer_recipes WHERE customer_id = ? ORDER BY recipe_name", (customer_id,)).fetchall()
    
    user_assigned_recipes = {}
    user_recipe_counts = {}
    for u in users:
        u_recipes = [row['recipe_name'] for row in g.db.execute("SELECT recipe_name FROM user_recipes WHERE user_id = ?", (u['id'],)).fetchall()]
        user_assigned_recipes[u['id']] = u_recipes
        user_recipe_counts[u['id']] = len(u_recipes)
        
    return render_template('company/users.html',
                           customer=customer,
                           users=users,
                           allowed_recipes=allowed_recipes,
                           user_assigned_recipes=user_assigned_recipes,
                           user_recipe_counts=user_recipe_counts)

@company_bp.route('/users/add', methods=['POST'])
@company_admin_required
def add_user():
    customer_id = current_user.customer_id
    role = request.form.get('role', 'customer_viewer')
    # Prevent company admin from creating master admin accounts
    if role not in ('customer_viewer', 'company_admin'):
        role = 'customer_viewer'
        
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    password = request.form.get('password', '')
    display_name = request.form.get('display_name', '').strip() or username
    access_mode = 'ALL' # Default for new team members
    
    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for('company.manage_users'))
        
    pwd_hash = generate_password_hash(password)
    from app.database import INSERT_USER
    try:
        g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, role, customer_id, access_mode))
        g.db.commit()
        
        if email:
            from app.mail import send_welcome_email
            import threading
            from flask import current_app
            app_context = current_app._get_current_object().app_context()
            host_login = f"{request.host_url.rstrip('/')}/login"
            def background_mail(url):
                with app_context:
                    send_welcome_email(email, username, password, url)
            threading.Thread(target=background_mail, args=(host_login,)).start()
            flash(f"User '{username}' created. A welcome email is being sent to {email}.", "success")
        else:
            flash(f"Team member '{username}' created successfully.", "success")
    except Exception as e:
        flash(f"Creation Error: {e}", "error")
        
    return redirect(url_for('company.manage_users'))

@company_bp.route('/users/bulk_add', methods=['POST'])
@company_admin_required
def bulk_add_users():
    """Allows Company Admins to bulk onboard users to their company via CSV or text paste."""
    import secrets
    import string
    import io
    import csv
    import threading
    from flask import current_app
    from app.database import INSERT_USER
    from app.mail import send_bulk_invite_email

    customer_id = current_user.customer_id
    customer = g.db.execute("SELECT company_name FROM customers WHERE id = ?", (customer_id,)).fetchone()
    company_name = customer['company_name'] if customer else ""

    raw_text = request.form.get('bulk_text', '').strip()
    uploaded_file = request.files.get('bulk_file')
    send_invites = request.form.get('send_invites') == '1'

    rows_to_process = []

    # 1. Parse uploaded CSV file if provided
    if uploaded_file and uploaded_file.filename:
        try:
            stream = io.StringIO(uploaded_file.stream.read().decode("utf-8", errors="ignore"))
            reader = csv.reader(stream)
            for row in reader:
                if not row or not any(row):
                    continue
                first_cell = row[0].strip().lower()
                if first_cell in ('email', 'username', 'name', 'full_name'):
                    continue
                rows_to_process.append([c.strip() for c in row])
        except Exception as e:
            flash(f"Error reading CSV file: {e}", "error")
            return redirect(url_for('company.manage_users'))

    # 2. Parse raw text paste
    if raw_text:
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
            elif ';' in line:
                parts = [p.strip() for p in line.split(';')]
            elif '\t' in line:
                parts = [p.strip() for p in line.split('\t')]
            else:
                parts = [line]
            
            if parts and parts[0].lower() not in ('email', 'username', 'name', 'full_name'):
                rows_to_process.append(parts)

    if not rows_to_process:
        flash("No valid email addresses or records found in upload/paste.", "warning")
        return redirect(url_for('company.manage_users'))

    created_count = 0
    skipped_count = 0
    invites_to_dispatch = []

    def generate_random_pwd():
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(10))

    for item in rows_to_process:
        email = None
        display_name = None
        username = None
        user_role = 'customer_viewer'

        if len(item) == 1:
            val = item[0]
            if '@' in val:
                email = val
                username = val.split('@')[0].lower()
                display_name = val.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            else:
                username = val.lower()
                display_name = val
        elif len(item) == 2:
            if '@' in item[0]:
                email, display_name = item[0], item[1]
                username = email.split('@')[0].lower()
            else:
                username, display_name = item[0], item[1]
        elif len(item) >= 3:
            email = item[0] if '@' in item[0] else None
            display_name = item[1]
            username = item[2].lower()
            if len(item) >= 4 and item[3] == 'company_admin':
                user_role = 'company_admin'

        if not username:
            skipped_count += 1
            continue

        username = "".join(c for c in username if c.isalnum() or c in ('_', '-'))

        # Check existing user
        existing = g.db.execute("SELECT id FROM users WHERE username = ? OR (email IS NOT NULL AND email = ?)", (username, email)).fetchone()
        if existing:
            skipped_count += 1
            continue

        temp_pwd = generate_random_pwd()
        pwd_hash = generate_password_hash(temp_pwd)

        try:
            g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name or username, user_role, customer_id, 'ALL'))
            created_count += 1
            if email and send_invites:
                invites_to_dispatch.append((email, username, temp_pwd))
        except Exception:
            skipped_count += 1

    g.db.commit()

    if invites_to_dispatch:
        app_context = current_app._get_current_object().app_context()
        host_login = f"{request.host_url.rstrip('/')}/login"
        def run_invites(inv_list, url, comp_name):
            with app_context:
                for mail, uname, pwd in inv_list:
                    send_bulk_invite_email(mail, uname, pwd, comp_name, url)
        threading.Thread(target=run_invites, args=(invites_to_dispatch, host_login, company_name)).start()

    msg = f"Bulk Provisioning Completed: {created_count} team members added successfully."
    if skipped_count > 0:
        msg += f" {skipped_count} skipped (duplicates or invalid)."
    if invites_to_dispatch:
        msg += f" {len(invites_to_dispatch)} welcome emails dispatched."

    flash(msg, "success" if created_count > 0 else "warning")
    return redirect(url_for('company.manage_users'))

@company_bp.route('/domains/update', methods=['POST'])
@company_admin_required
def update_allowed_domains():
    customer_id = current_user.customer_id
    allowed_domains = request.form.get('allowed_domains', '').strip()

    if customer_id:
        domains_list = [d.strip().lower().lstrip('@') for d in allowed_domains.replace(';', ',').split(',') if d.strip()]
        cleaned_domains = ", ".join(domains_list) if domains_list else None
        
        g.db.execute("UPDATE customers SET allowed_domains = ? WHERE id = ?", (cleaned_domains, customer_id))
        g.db.commit()
        flash("Auto-join email domains updated for your organization.", "success")

    return redirect(url_for('company.manage_users'))

@company_bp.route('/users/toggle', methods=['POST'])
@company_admin_required
def toggle_user():
    user_id = request.form.get('user_id')
    new_status = int(request.form.get('is_active', 1))
    
    # Enforce boundary: Company Admin can ONLY toggle users in their own company!
    user = g.db.execute("SELECT customer_id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user['customer_id'] != current_user.customer_id:
        abort(403)
        
    from app.database import TOGGLE_USER_ACCESS
    g.db.execute(TOGGLE_USER_ACCESS, (new_status, user_id))
    g.db.commit()
    flash("User access status updated.", "success")
    return redirect(url_for('company.manage_users'))

@company_bp.route('/users/permissions', methods=['POST'])
@company_admin_required
def update_user_recipe_permissions():
    user_id = request.form.get('user_id')
    access_mode = request.form.get('access_mode', 'ALL')
    selected_recipes = request.form.getlist('selected_recipes')
    
    # Enforce boundary: verify user belongs to current company
    user = g.db.execute("SELECT customer_id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user['customer_id'] != current_user.customer_id:
        abort(403)
        
    # Enforce boundary: verify all selected recipes actually belong to company's allowed master recipes!
    allowed_db = [r['recipe_name'] for r in g.db.execute("SELECT recipe_name FROM customer_recipes WHERE customer_id = ?", (current_user.customer_id,)).fetchall()]
    
    from app.database import UPDATE_USER_ACCESS_MODE, DELETE_USER_RECIPES, INSERT_USER_RECIPE
    g.db.execute(UPDATE_USER_ACCESS_MODE, (access_mode, user_id))
    g.db.execute(DELETE_USER_RECIPES, (user_id,))
    
    if access_mode == 'CUSTOM':
        for r_name in selected_recipes:
            if r_name in allowed_db:
                g.db.execute(INSERT_USER_RECIPE, (user_id, r_name))
                
    g.db.commit()
    flash("Recipe permissions updated successfully.", "success")
    return redirect(url_for('company.manage_users'))
