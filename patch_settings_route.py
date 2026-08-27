# -*- coding: utf-8 -*-
import io

with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    return render_template('admin/settings.html', 
                             developer_email=dev_email,
                             telemetry_frequency=tel_freq,
                             sync_time=sync_time, 
                             root_search_path=root_search_path,
                             mail_server=m_srv,
                             mail_port=m_prt,
                             mail_username=m_usr,
                             mail_password=m_pwd)'''

replacement = '''    admins = g.db.execute("SELECT * FROM users WHERE role = 'admin'").fetchall()
    return render_template('admin/settings.html', 
                             developer_email=dev_email,
                             telemetry_frequency=tel_freq,
                             sync_time=sync_time, 
                             root_search_path=root_search_path,
                             mail_server=m_srv,
                             mail_port=m_prt,
                             mail_username=m_usr,
                             mail_password=m_pwd,
                             system_admins=admins)'''

c = c.replace(target, replacement)

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
