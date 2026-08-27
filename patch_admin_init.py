with open('app/__init__.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_code = '''        else:
            app.config['SECRET_KEY'] = secret_row['value']
            
        conn.close()'''

new_code = '''        else:
            app.config['SECRET_KEY'] = secret_row['value']
            
        # Ensure at least one admin exists for completely fresh installs
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if admin_count == 0:
            from werkzeug.security import generate_password_hash
            default_pass = generate_password_hash('admin123')
            conn.execute("INSERT INTO users (username, password_hash, display_name, role) VALUES ('admin', ?, 'Administrator', 'admin')", (default_pass,))
            conn.commit()
            
        conn.close()'''

c = c.replace(old_code, new_code)

with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(c)
