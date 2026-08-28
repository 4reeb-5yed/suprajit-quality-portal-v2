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
