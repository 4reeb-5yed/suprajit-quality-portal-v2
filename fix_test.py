with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix FK constraint by adding customers
text = text.replace("conn.execute(\"INSERT OR IGNORE INTO users", "conn.execute(\"INSERT OR IGNORE INTO customers (id, name, code) VALUES ('CUST_A', 'A', 'A')\")\n        conn.execute(\"INSERT OR IGNORE INTO customers (id, name, code) VALUES ('CUST_B', 'B', 'B')\")\n        conn.execute(\"INSERT OR IGNORE INTO users")

# Fix missing follow_redirects which might have masked login failures
text = text.replace("client.post('/login', data={'username': 'cust_a', 'password': 'admin123'})", "client.post('/login', data={'username': 'cust_a', 'password': 'admin123'}, follow_redirects=True)")
text = text.replace("client.post('/login', data={'username': 'standard_user', 'password': 'admin123'})", "client.post('/login', data={'username': 'standard_user', 'password': 'admin123'}, follow_redirects=True)")
text = text.replace("client.post('/login', data={'username': 'hacker', 'password': 'admin123'})", "client.post('/login', data={'username': 'hacker', 'password': 'admin123'}, follow_redirects=True)")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
