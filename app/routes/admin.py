from flask import Blueprint, render_template, g, abort, request, current_app
from flask_login import login_required, current_user
from app.database import GET_SETTING, SET_SETTING

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    from flask import request
    if not current_user.is_admin:
        abort(403)
        
    if current_user.username == 'bootstrap_admin' and request.endpoint not in ['admin.setup', 'auth.logout']:
        from werkzeug.security import check_password_hash
        user_row = g.db.execute("SELECT password_hash FROM users WHERE id = ?", (current_user.id,)).fetchone()
        if user_row and check_password_hash(user_row['password_hash'], 'admin123'):
            return __import__('flask').redirect(__import__('flask').url_for('admin.setup'))

@admin_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    from flask import request, flash, redirect, url_for, render_template
    from werkzeug.security import generate_password_hash
    from app.database import SET_SETTING
    
    if request.method == 'POST':
        new_pass = request.form.get('new_password')
        admin_email = request.form.get('admin_email')
        dev_email = request.form.get('developer_email', '')
        
        m_srv = request.form.get('mail_server')
        m_prt = request.form.get('mail_port')
        m_usr = request.form.get('mail_username')
        m_pwd = request.form.get('mail_password')
        
        if new_pass and len(new_pass) >= 8:
            g.db.execute("UPDATE users SET password_hash = ?, email = ? WHERE id = ?", (generate_password_hash(new_pass), admin_email, current_user.id))
            
            if m_srv: g.db.execute(SET_SETTING, ('mail_server', m_srv))
            if m_prt: g.db.execute(SET_SETTING, ('mail_port', m_prt))
            if m_usr: g.db.execute(SET_SETTING, ('mail_username', m_usr))
            if m_pwd: g.db.execute(SET_SETTING, ('mail_password', m_pwd))
            
            if dev_email:
                g.db.execute(SET_SETTING, ('developer_email', dev_email))
                
            g.db.commit()
            flash("Initial configuration complete. Your system is secured and SMTP is ready.", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Password must be at least 8 characters.", "error")
            
    return render_template('admin/setup.html')

@admin_bp.route('/')
def dashboard():
    # Fetch system stats (Active only)
    users_count = g.db.execute("SELECT COUNT(*) FROM users ").fetchone()[0]
    customers_count = g.db.execute("SELECT COUNT(*) FROM customers ").fetchone()[0]
    reports_count = g.db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    
    # Recent batches
    recent_batches = g.db.execute("""
        SELECT * FROM batch_runs 
        ORDER BY run_started DESC 
        LIMIT 10
    """).fetchall()
    
    return render_template('admin/dashboard.html', 
                           users_count=users_count,
                           customers_count=customers_count,
                           reports_count=reports_count,
                           recent_batches=recent_batches)

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    from app.database import GET_SETTING, SET_SETTING
    from flask import flash, request, g
    from flask import render_template
    
    if request.method == 'POST':
        # Batch ingest settings
        new_time = request.form.get('sync_time')
        new_storage = request.form.get('root_search_path')
        
        # Email settings
        m_srv = request.form.get('mail_server')
        m_prt = request.form.get('mail_port')
        m_usr = request.form.get('mail_username')
        m_pwd = request.form.get('mail_password')
        dev_email = request.form.get('developer_email')
        tel_freq = request.form.get('telemetry_frequency')
        
        if new_time: g.db.execute(SET_SETTING, ('sync_time', new_time))
        if new_storage: g.db.execute(SET_SETTING, ('root_search_path', new_storage))
        if m_srv is not None: g.db.execute(SET_SETTING, ('mail_server', m_srv))
        if m_prt is not None: g.db.execute(SET_SETTING, ('mail_port', m_prt))
        if m_usr is not None: g.db.execute(SET_SETTING, ('mail_username', m_usr))
        if m_pwd is not None: g.db.execute(SET_SETTING, ('mail_password', m_pwd))
        if dev_email is not None: g.db.execute(SET_SETTING, ('developer_email', dev_email))
        if tel_freq is not None: g.db.execute(SET_SETTING, ('telemetry_frequency', tel_freq))
            
        g.db.commit()
        flash("System configuration updated.", "success")
        return __import__('flask').redirect(__import__('flask').url_for('admin.settings'))
        
    def get_val(key, default):
        row = g.db.execute(GET_SETTING, (key,)).fetchone()
        return row['value'] if row else default
        
    sync_time = get_val('sync_time', '01:00')
    root_search_path = get_val('root_search_path', '')
    
    m_srv = get_val('mail_server', 'smtp.gmail.com')
    m_prt = get_val('mail_port', '587')
    m_usr = get_val('mail_username', '')
    m_pwd = get_val('mail_password', '')
    dev_email = get_val('developer_email', '')
    tel_freq = get_val('telemetry_frequency', 'daily')
    
    system_admins = g.db.execute("SELECT * FROM users WHERE role = 'admin'").fetchall()
    return render_template('admin/settings.html', 
                           developer_email=dev_email,
                           telemetry_frequency=tel_freq,
                           sync_time=sync_time, 
                           root_search_path=root_search_path,
                           mail_server=m_srv,
                           mail_port=m_prt,
                           mail_username=m_usr,
                           mail_password=m_pwd,
                           system_admins=system_admins)
@admin_bp.route('/customers', methods=['GET'])
def customers():
    from app.database import GET_ALL_CUSTOMERS
    customer_list = g.db.execute(GET_ALL_CUSTOMERS).fetchall()
    
    # Fetch all recipes and group by customer_id
    recipes_raw = g.db.execute("SELECT * FROM customer_recipes").fetchall()
    customer_recipes = {}
    for r in recipes_raw:
        cid = r['customer_id']
        if cid not in customer_recipes:
            customer_recipes[cid] = []
        customer_recipes[cid].append(r)
        
    # Fetch all users
    users_raw = g.db.execute("SELECT * FROM users WHERE role = 'customer_viewer'").fetchall()
    customer_users = {}
    for u in users_raw:
        cid = u['customer_id']
        if cid not in customer_users:
            customer_users[cid] = []
        customer_users[cid].append(u)
        
    available_recipes = [r['recipe_name'] for r in g.db.execute("SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name").fetchall()]
    return render_template('admin/customers.html', 
                           customers=customer_list, 
                           customer_recipes=customer_recipes,
                           customer_users=customer_users,
                           available_recipes=available_recipes)

@admin_bp.route('/customers/add', methods=['POST'])
def add_customer():
    from app.database import INSERT_CUSTOMER
    from flask import request, flash
    c_id = request.form.get('id', '').strip().lower()
    c_name = request.form.get('company_name', '').strip()
    
    if not c_id or not c_name:
        flash("Customer ID and Name are required.", "error")
    else:
        try:
            g.db.execute(INSERT_CUSTOMER, (c_id, c_name))
            g.db.commit()
            flash(f"Customer '{c_name}' added successfully.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")
            
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/add_user', methods=['POST'])
def add_user():
    from app.database import INSERT_USER
    from flask import request, flash
    from werkzeug.security import generate_password_hash
    
    customer_id = request.form.get('customer_id')
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    display_name = request.form.get('display_name', '').strip()
    

    if not username or not password:
        flash("Username and password are required.", "error")
        return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
        
    # Enterprise Password Complexity Enforcer
    import re
    if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[A-Z]", password) or not re.search(r"[@$!%*?&#]", password):
        flash("Password must be at least 8 characters long and contain a number, an uppercase letter, and a special character.", "error")
        return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

        
    pwd_hash = generate_password_hash(password)
    
    try:
        g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, 'customer_viewer', customer_id))
        g.db.commit()
        
        # Send welcome email if email was provided
        if email:
            from app.mail import send_welcome_email
            # Run in a separate thread so the admin page doesn't hang if SMTP is slow
            import threading
            from flask import current_app
            app_context = current_app._get_current_object().app_context()
            from flask import request
            host_login = f"{request.host_url.rstrip('/')}/login"
            def background_mail(url):
                with app_context:
                    send_welcome_email(email, username, password, url)
            threading.Thread(target=background_mail, args=(host_login,)).start()
            flash(f"Login account '{username}' created. A welcome email is being sent to {email}.", "success")
        else:
            flash(f"Login account '{username}' created successfully.", "success")
    except Exception as e:
        flash(f"Database Error: {e}", "error")
        print(f"User Creation Error: {e}")
        
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/toggle_user', methods=['POST'])
def toggle_user():
    from app.database import TOGGLE_USER_ACCESS
    from flask import request, flash

    user_id = request.form.get('user_id')
    new_status = int(request.form.get('is_active', 1))

    if user_id:
        g.db.execute(TOGGLE_USER_ACCESS, (new_status, user_id))
        g.db.commit()
        action = 'Granted' if new_status == 1 else 'Revoked'
        flash(f'Access {action} successfully.', 'success')

    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/add_recipe', methods=['POST'])
def add_recipe():
    from app.database import INSERT_CUSTOMER_RECIPE
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    recipe_name = request.form.get('recipe_name', '').strip()
    
    if not recipe_name:
        flash("Recipe prefix is required.", "error")
    else:
        try:
            g.db.execute(INSERT_CUSTOMER_RECIPE, (customer_id, recipe_name))
            g.db.commit()
            flash(f"Recipe access granted.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")
            
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/delete_recipe', methods=['POST'])
def delete_recipe():
    from app.database import DELETE_CUSTOMER_RECIPE
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    recipe_name = request.form.get('recipe_name')
    if customer_id and recipe_name:
        g.db.execute(DELETE_CUSTOMER_RECIPE, (customer_id, recipe_name))
        g.db.commit()
        flash("Recipe access removed successfully.", "success")
        
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
@admin_bp.route('/customers/edit', methods=['POST'])
def edit_customer():
    from app.database import UPDATE_CUSTOMER
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    company_name = request.form.get('company_name', '').strip()
    
    if company_name:
        g.db.execute(UPDATE_CUSTOMER, (company_name, customer_id))
        g.db.commit()
        flash(f"Customer '{company_name}' updated successfully.", "success")
        
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/suspend', methods=['POST'])
def suspend_customer():
    from app.database import TOGGLE_CUSTOMER_SUSPENSION
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    new_state = int(request.form.get('portal_suspended', 1))
    
    if customer_id:
        g.db.execute(TOGGLE_CUSTOMER_SUSPENSION, (new_state, customer_id))
        g.db.commit()
        if new_state == 1:
            flash(f"Customer '{customer_id}' has been SUSPENDED. None of their users can log in.", "success")
        else:
            flash(f"Customer '{customer_id}' has been RESTORED. Portal access is active.", "success")
            
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
@admin_bp.route('/customers/delete', methods=['POST'])
def delete_customer():
    from app.database import DELETE_CUSTOMER
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    if customer_id:
        try:
            g.db.execute(DELETE_CUSTOMER, (customer_id,))
            g.db.commit()
            flash(f"Customer '{customer_id}' has been permanently deleted.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")
        
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/diagnostics')
def diagnostics():
    # Read the last 100 lines of the suprajit.log file
    log_lines = []
    try:
        from flask import current_app
        log_path = current_app.config.get('LOG_FILE_PATH')
        import os
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                log_lines = lines[-100:]
        else:
            log_lines = ["No log file found. System has not generated any logs yet."]
    except Exception as e:
        log_lines = [f"Error reading log file: {e}"]
        
    # Get last sync info
    last_run = g.db.execute("SELECT * FROM batch_runs ORDER BY run_started DESC LIMIT 1").fetchone()
    
    # Advanced Diagnostics Engine Stats
    import os
    from flask import current_app
    db_path = current_app.config['DATABASE_PATH']
    db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2) if os.path.exists(db_path) else 0.0
    
    total_reports = g.db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    total_customers = g.db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    
    from app.database import GET_SETTING
    sync_time_row = g.db.execute(GET_SETTING, ('sync_time',)).fetchone()
    sync_time_str = sync_time_row['value'] if sync_time_row else "02:00"
    
    return __import__('flask').render_template('admin/diagnostics.html', 
                                               log_lines=log_lines, 
                                               last_run=last_run,
                                               db_size_mb=db_size_mb,
                                               total_reports=total_reports,
                                               total_customers=total_customers,
                                               sync_time_str=sync_time_str)


@admin_bp.route('/repair', methods=['GET', 'POST'])
def repair():
    trace_log = None
    success_msg = None
    error_msg = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        db_path = current_app.config['DATABASE_PATH']
        storage_base = current_app.config['STORAGE_FOLDER']
        from app.sync_engine import SyncEngine
        
        try:
            if action == 'dry_run':
                engine = SyncEngine(db_path, storage_base)
                # Parse date if provided
                from datetime import datetime
                target = request.form.get('target_date')
                dt = datetime.strptime(target, '%Y-%m-%d').date() if target else None
                
                # Execute dry run
                trace_log = engine.execute_dry_run(target_date=dt)
                
            elif action == 'purge_date':
                target = request.form.get('target_date')
                if not target:
                    error_msg = "Please provide a date to purge."
                else:
                    count = g.db.execute("SELECT COUNT(*) FROM reports WHERE report_date = ?", (target,)).fetchone()[0]
                    g.db.execute("DELETE FROM reports WHERE report_date = ?", (target,))
                    g.db.commit()
                    success_msg = f"Successfully purged {count} records for {target}."
                    
            elif action == 'force_sync':
                target = request.form.get('target_date')
                if not target:
                    error_msg = "Please provide a date to force sync."
                else:
                    from datetime import datetime
                    dt = datetime.strptime(target, '%Y-%m-%d').date()
                    engine = SyncEngine(db_path, storage_base)
                    
                    # Run in background to prevent hanging UI
                    import threading
                    def run_force(dt_val):
                        try:
                            engine.run_batch(target_date=dt_val)
                        except Exception as e:
                            print(f"Force sync error: {e}")
                            
                    t = threading.Thread(target=run_force, args=(dt,))
                    t.start()
                    success_msg = f"Force Sync started in the background for {target}. Check Diagnostics in 30 seconds."
                    
        except Exception as e:
            error_msg = str(e)
            
    return __import__('flask').render_template('admin/repair.html', 
                             trace_log=trace_log, 
                             success_msg=success_msg, 
                             error_msg=error_msg)

@admin_bp.route('/trigger_sync', methods=['POST'])
def trigger_sync():
    import threading
    from app.sync_engine import SyncEngine
    from flask import current_app, flash
    
    db_path = current_app.config['DATABASE_PATH']
    storage_base = current_app.config['STORAGE_FOLDER']
    
    def run_job():
        try:
            engine = SyncEngine(db_path, storage_base)
            engine.run_batch(full_sync=True)
        except Exception as e:
            print(f"Manual sync error: {e}")
            
    t = threading.Thread(target=run_job)
    t.start()
    
    flash("Manual ingestion batch has been started in the background! Refresh the page in a few moments to see the results.", "success")
    return __import__('flask').redirect(__import__('flask').url_for('admin.dashboard'))

@admin_bp.route('/users/delete', methods=['POST'])
def delete_user():
    from flask import request, flash, g, redirect, url_for
    from flask_login import current_user
    
    user_id = request.form.get('user_id')
    
    if str(user_id) == str(current_user.id):
        flash("You cannot delete your currently active account.", "error")
        return redirect(url_for('admin.customers'))
        
    user = g.db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('admin.customers'))
        
    if user['role'] == 'admin':
        admin_count = g.db.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'").fetchone()['c']
        if admin_count <= 1:
            flash("Cannot delete the last remaining administrator account. Create a new one first.", "error")
            return redirect(url_for('admin.customers'))
            
    g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    g.db.commit()
    flash("User deleted successfully.", "success")
    if user['role'] == 'admin':
        return redirect(url_for('admin.settings'))
    return redirect(url_for('admin.customers'))
import os
from flask import send_file, current_app

@admin_bp.route('/logs/download')
def download_logs():
    """Allows System Administrators to instantly download the raw system log file for observability."""
    log_path = current_app.config.get('LOG_FILE_PATH')
    if not log_path or not os.path.exists(log_path):
        flash("System log file does not exist yet.", "warning")
        return redirect(url_for('admin.dashboard'))
        
    return send_file(log_path, as_attachment=True, download_name="suprajit_system.log", mimetype="text/plain")



