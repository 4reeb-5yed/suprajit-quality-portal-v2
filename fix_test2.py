with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("INTO customers (id, name, code) VALUES ('CUST_A', 'A', 'A')", "INTO customers (id, company_name) VALUES ('CUST_A', 'Company A')")
text = text.replace("INTO customers (id, name, code) VALUES ('CUST_B', 'B', 'B')", "INTO customers (id, company_name) VALUES ('CUST_B', 'Company B')")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
