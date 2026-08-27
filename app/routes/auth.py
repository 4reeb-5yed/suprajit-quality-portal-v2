from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from app.database import UPDATE_USER_LOCKOUT, GET_USER_BY_USERNAME, GET_USER_BY_EMAIL, UPDATE_USER_PASSWORD
from app.mail import send_password_reset_email, get_serializer

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('portal.search'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        row = g.db.execute(GET_USER_BY_USERNAME, (username,)).fetchone()
        if not row:
            flash("Invalid credentials", "error")
            return render_template('auth/login.html')
            
        # Check Lockout
        if row['locked_until']:
            locked_until = datetime.strptime(row['locked_until'], '%Y-%m-%d %H:%M:%S')
            if datetime.utcnow() < locked_until:
                flash("Account locked due to too many failed attempts. Try again later.", "error")
                return render_template('auth/login.html')
            
        # Check if user is disabled
        if row['is_active'] == 0:
            flash("Your account has been revoked. Contact the administrator.", "error")
            return render_template('auth/login.html')
            
        # Check if customer portal is globally suspended
        if row['role'] != 'admin':
            cust = g.db.execute("SELECT portal_suspended FROM customers WHERE id = ?", (row['customer_id'],)).fetchone()
            if cust and cust['portal_suspended'] == 1:
                flash("Portal access for this customer is currently suspended.", "error")
                return render_template('auth/login.html')
                
        # Check Password
        if check_password_hash(row['password_hash'], password):
            # Reset failures
            g.db.execute(UPDATE_USER_LOCKOUT, (0, None, row['id']))
            g.db.commit()
            
            # Use the UserMixin object defined in __init__ (loaded implicitly via login_user)
            from app.auth_models import User
            user_obj = User(row)
            login_user(user_obj)
            
            # Log audit
            g.db.execute("INSERT INTO audit_log (user_id, action, client_ip) VALUES (?, ?, ?)", 
                         (row['id'], 'login', request.remote_addr))
            g.db.commit()
            
            return redirect(url_for('portal.search'))
        else:
            # Increment failures
            failures = row['failed_attempts'] + 1
            locked_until = None
            if failures >= 5:
                locked_until = (datetime.utcnow() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                flash("Account locked for 15 minutes due to too many failed attempts.", "error")
            else:
                flash("Invalid credentials", "error")
                
            g.db.execute(UPDATE_USER_LOCKOUT, (failures, locked_until, row['id']))
            g.db.commit()
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        row = g.db.execute(GET_USER_BY_EMAIL, (email,)).fetchone()
        if row:
            send_password_reset_email(email, row['id'])
        # Always say success to prevent email enumeration
        flash("If an account with that email exists, a reset link has been sent.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = get_serializer()
    try:
        user_id = s.loads(token, salt='password-reset-salt', max_age=3600) # 1 hour
    except Exception:
        flash("The reset link is invalid or has expired.", "error")
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        new_password = request.form.get('password')
        p_hash = generate_password_hash(new_password)
        g.db.execute(UPDATE_USER_PASSWORD, (p_hash, user_id))
        g.db.commit()
        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html')
