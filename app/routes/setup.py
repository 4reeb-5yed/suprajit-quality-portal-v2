from flask import Blueprint, render_template, request, redirect, url_for, g
from werkzeug.security import generate_password_hash
import os

setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/setup', methods=['GET', 'POST'])
def wizard():
    # If admin exists, block setup
    admin_exists = g.db.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone()
    if admin_exists:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        admin_user = request.form.get('username')
        admin_pass = request.form.get('password')
        admin_email = request.form.get('email')
        
        # Create Admin
        p_hash = generate_password_hash(admin_pass)
        g.db.execute("INSERT INTO users (username, email, password_hash, display_name, role) VALUES (?, ?, ?, ?, ?)",
                     (admin_user, admin_email, p_hash, "System Admin", "admin"))
                     
        # Create Internal Customer (Suprajit)
        g.db.execute("INSERT INTO customers (id, company_name) VALUES ('suprajit', 'Suprajit Internal')")
        
        g.db.commit()
        return redirect(url_for('auth.login'))
        
    return render_template('setup/wizard.html')
