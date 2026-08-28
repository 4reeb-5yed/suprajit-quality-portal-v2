with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("INSERT OR IGNORE INTO reports", "INSERT INTO reports")
with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
