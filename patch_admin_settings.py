with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
in_settings = False
for line in lines:
    if line.startswith('def settings():'):
        in_settings = True
        
        new_settings = '''def settings():
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
        
        if new_time: g.db.execute(SET_SETTING, ('sync_time', new_time))
        if new_storage: g.db.execute(SET_SETTING, ('root_search_path', new_storage))
        if m_srv is not None: g.db.execute(SET_SETTING, ('mail_server', m_srv))
        if m_prt is not None: g.db.execute(SET_SETTING, ('mail_port', m_prt))
        if m_usr is not None: g.db.execute(SET_SETTING, ('mail_username', m_usr))
        if m_pwd is not None: g.db.execute(SET_SETTING, ('mail_password', m_pwd))
            
        g.db.commit()
        flash("System configuration updated.", "success")
        return __import__('flask').redirect(__import__('flask').url_for('admin.settings'))
        
    def get_val(key, default):
        row = g.db.execute(GET_SETTING, (key,)).fetchone()
        return row['value'] if row else default
        
    sync_time = get_val('sync_time', '01:00')
    root_search_path = get_val('root_search_path', 'C:\\\\')
    
    m_srv = get_val('mail_server', 'smtp.gmail.com')
    m_prt = get_val('mail_port', '587')
    m_usr = get_val('mail_username', '')
    m_pwd = get_val('mail_password', '')
    
    return render_template('admin/settings.html', 
                           sync_time=sync_time, 
                           root_search_path=root_search_path,
                           mail_server=m_srv,
                           mail_port=m_prt,
                           mail_username=m_usr,
                           mail_password=m_pwd)
'''
        out.append(new_settings)
        continue
        
    if in_settings:
        if line.startswith('@admin_bp.route') or line.startswith('def '):
            in_settings = False
        else:
            continue
            
    if not in_settings:
        out.append(line)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.writelines(out)
