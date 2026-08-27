with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_post = '''        # Email settings
        m_srv = request.form.get('mail_server')
        m_prt = request.form.get('mail_port')
        m_usr = request.form.get('mail_username')
        m_pwd = request.form.get('mail_password')'''

new_post = '''        # Email settings
        m_srv = request.form.get('mail_server')
        m_prt = request.form.get('mail_port')
        m_usr = request.form.get('mail_username')
        m_pwd = request.form.get('mail_password')
        dev_email = request.form.get('developer_email')'''
c = c.replace(old_post, new_post)

old_save = '''        if m_usr is not None: g.db.execute(SET_SETTING, ('mail_username', m_usr))
        if m_pwd is not None: g.db.execute(SET_SETTING, ('mail_password', m_pwd))'''
new_save = '''        if m_usr is not None: g.db.execute(SET_SETTING, ('mail_username', m_usr))
        if m_pwd is not None: g.db.execute(SET_SETTING, ('mail_password', m_pwd))
        if dev_email is not None: g.db.execute(SET_SETTING, ('developer_email', dev_email))'''
c = c.replace(old_save, new_save)

old_get = '''    m_srv = get_val('mail_server', 'smtp.gmail.com')
    m_prt = get_val('mail_port', '587')
    m_usr = get_val('mail_username', '')
    m_pwd = get_val('mail_password', '')
    
    return render_template('admin/settings.html', '''
new_get = '''    m_srv = get_val('mail_server', 'smtp.gmail.com')
    m_prt = get_val('mail_port', '587')
    m_usr = get_val('mail_username', '')
    m_pwd = get_val('mail_password', '')
    dev_email = get_val('developer_email', 'admin@canspirit.com')
    
    return render_template('admin/settings.html', 
                           developer_email=dev_email,'''
c = c.replace(old_get, new_get)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
