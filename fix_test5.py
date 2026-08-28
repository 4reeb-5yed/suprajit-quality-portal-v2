with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("INTO users (username, password_hash, role, customer_id) VALUES ('cust_a', ?", "INTO users (username, password_hash, display_name, role, customer_id) VALUES ('cust_a', ?, 'Cust A'")
text = text.replace("INTO users (username, password_hash, role, customer_id) VALUES ('cust_b', ?", "INTO users (username, password_hash, display_name, role, customer_id) VALUES ('cust_b', ?, 'Cust B'")
text = text.replace("INTO users (username, password_hash, role, customer_id) VALUES ('standard_user', ?", "INTO users (username, password_hash, display_name, role, customer_id) VALUES ('standard_user', ?, 'Std'")
text = text.replace("INTO users (username, password_hash, role) VALUES ('hacker', ?", "INTO users (username, password_hash, display_name, role) VALUES ('hacker', ?, 'Hacker'")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
