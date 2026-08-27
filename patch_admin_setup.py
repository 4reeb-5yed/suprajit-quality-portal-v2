# -*- coding: utf-8 -*-
import io
with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

target1 = '''@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        abort(403)'''

replacement1 = '''@admin_bp.before_request
@login_required
def require_admin():
    from flask import request
    if not current_user.is_admin:
        abort(403)
        
    if current_user.username == 'admin' and request.endpoint not in ['admin.setup', 'auth.logout']:
        from werkzeug.security import check_password_hash
        user_row = g.db.execute("SELECT password_hash FROM users WHERE id = ?", (current_user.id,)).fetchone()
        if user_row and check_password_hash(user_row['password_hash'], 'admin123'):
            return __import__('flask').redirect(__import__('flask').url_for('admin.setup'))'''

target2 = '''@admin_bp.route('/')
def dashboard():'''

replacement2 = '''@admin_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    from flask import request, flash, redirect, url_for, render_template
    from werkzeug.security import generate_password_hash
    if request.method == 'POST':
        new_pass = request.form.get('new_password')
        dev_email = request.form.get('developer_email')
        if new_pass and len(new_pass) >= 8:
            g.db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new_pass), current_user.id))
            g.db.execute(SET_SETTING, ('developer_email', dev_email))
            g.db.commit()
            flash("Setup complete. Your system is now secure.", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Password must be at least 8 characters.", "error")
            
    return render_template('admin/setup.html')

@admin_bp.route('/')
def dashboard():'''

c = c.replace(target1, replacement1)
c = c.replace(target2, replacement2)

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
