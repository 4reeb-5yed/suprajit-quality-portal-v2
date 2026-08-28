with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("'scrypt:32768:8:1$1uR9x$a'", "p_hash")
text = text.replace("conn = get_connection(app.config['DATABASE_PATH'])", "conn = get_connection(app.config['DATABASE_PATH'])\n        from werkzeug.security import generate_password_hash\n        p_hash = generate_password_hash('admin123')")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
