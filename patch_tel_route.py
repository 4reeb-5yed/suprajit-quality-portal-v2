with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_post = '''        m_pwd = request.form.get('mail_password')
        dev_email = request.form.get('developer_email')'''
new_post = '''        m_pwd = request.form.get('mail_password')
        dev_email = request.form.get('developer_email')
        tel_freq = request.form.get('telemetry_frequency')'''
c = c.replace(old_post, new_post)

old_save = '''        if m_pwd is not None: g.db.execute(SET_SETTING, ('mail_password', m_pwd))
        if dev_email is not None: g.db.execute(SET_SETTING, ('developer_email', dev_email))'''
new_save = '''        if m_pwd is not None: g.db.execute(SET_SETTING, ('mail_password', m_pwd))
        if dev_email is not None: g.db.execute(SET_SETTING, ('developer_email', dev_email))
        if tel_freq is not None: g.db.execute(SET_SETTING, ('telemetry_frequency', tel_freq))'''
c = c.replace(old_save, new_save)

old_get = '''    dev_email = get_val('developer_email', 'admin@canspirit.com')
    
    return render_template('admin/settings.html', 
                           developer_email=dev_email,'''
new_get = '''    dev_email = get_val('developer_email', 'admin@canspirit.com')
    tel_freq = get_val('telemetry_frequency', 'daily')
    
    return render_template('admin/settings.html', 
                           developer_email=dev_email,
                           telemetry_frequency=tel_freq,'''
c = c.replace(old_get, new_get)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
