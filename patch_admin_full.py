# -*- coding: utf-8 -*-
import io
import re

with io.open(r'C:\Users\humza\suprajit_v2\app\routes\admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update the trap
c = c.replace("if current_user.username == 'admin' and request.endpoint", "if current_user.username == 'bootstrap_admin' and request.endpoint")
c = c.replace("current_user.username == 'admin' and check_password_hash", "current_user.username == 'bootstrap_admin' and check_password_hash")

# 2. Update the setup route
setup_target = '''@admin_bp.route('/setup', methods=['GET', 'POST'])
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
            
    return render_template('admin/setup.html')'''

setup_replacement = '''@admin_bp.route('/setup', methods=['GET', 'POST'])
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
            
    return render_template('admin/setup.html')'''

c = c.replace(setup_target, setup_replacement)

# 3. Update the settings route return statement using regex because we missed it last time
pattern = re.compile(r"return render_template\('admin/settings\.html',\s*developer_email=dev_email,\s*telemetry_frequency=tel_freq,\s*sync_time=sync_time,\s*root_search_path=root_search_path,\s*mail_server=m_srv,\s*mail_port=m_prt,\s*mail_username=m_usr,\s*mail_password=m_pwd\)")

settings_replacement = '''system_admins = g.db.execute("SELECT * FROM users WHERE role = 'admin'").fetchall()
    return render_template('admin/settings.html', 
                           developer_email=dev_email,
                           telemetry_frequency=tel_freq,
                           sync_time=sync_time, 
                           root_search_path=root_search_path,
                           mail_server=m_srv,
                           mail_port=m_prt,
                           mail_username=m_usr,
                           mail_password=m_pwd,
                           system_admins=system_admins)'''

c = pattern.sub(settings_replacement, c)

with io.open(r'C:\Users\humza\suprajit_v2\app\routes\admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
