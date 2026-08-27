with open('app/__init__.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_db = '''    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        conn.close()'''

new_db = '''    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        
        # Security: Enforce unique cryptographically secure secret key per installation
        secret_row = conn.execute("SELECT value FROM system_settings WHERE key = 'secret_key'").fetchone()
        if not secret_row:
            import secrets
            new_secret = secrets.token_hex(32)
            conn.execute("INSERT INTO system_settings (key, value) VALUES ('secret_key', ?)", (new_secret,))
            conn.commit()
            app.config['SECRET_KEY'] = new_secret
        else:
            app.config['SECRET_KEY'] = secret_row['value']
            
        conn.close()'''
        
c = c.replace(old_db, new_db)

with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(c)
