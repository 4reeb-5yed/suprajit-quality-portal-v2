with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("VALUES ('cust_a', p_hash, 'user', 'CUST_A')", "VALUES ('cust_a', ?, 'user', 'CUST_A')\", (p_hash,))")
text = text.replace("VALUES ('cust_b', p_hash, 'user', 'CUST_B')", "VALUES ('cust_b', ?, 'user', 'CUST_B')\", (p_hash,))")
text = text.replace("VALUES ('standard_user', p_hash, 'user', 'CUST_A')", "VALUES ('standard_user', ?, 'user', 'CUST_A')\", (p_hash,))")
text = text.replace("VALUES ('hacker', p_hash, 'admin')", "VALUES ('hacker', ?, 'admin')\", (p_hash,))")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
