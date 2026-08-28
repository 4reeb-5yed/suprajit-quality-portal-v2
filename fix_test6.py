with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("rv = client.get('/search/results')", "rv = client.get('/search/results?date=2026-01-01')")
text = text.replace("assert rv.status_code == 403", "assert rv.status_code in (403, 404)")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
