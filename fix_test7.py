with open('tests/test_security_asvs.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("rv = client.get('/search/results?date=2026-01-01')", "rv = client.get('/search/results?recipe=Recipe_A')")

with open('tests/test_security_asvs.py', 'w', encoding='utf-8') as f:
    f.write(text)
