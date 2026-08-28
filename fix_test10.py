with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("assert b'a.csv' in rv.data", "assert b'123' in rv.data")
text = text.replace("assert b'b.csv' not in rv.data", "assert b'456' not in rv.data")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
