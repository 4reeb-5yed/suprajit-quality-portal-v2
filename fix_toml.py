with open('pyproject.toml', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('`n', '\n')
content = content.replace('"flask-wtf>=1.3.0",\n    "cryptography>=41.0.0",', '"flask-wtf>=1.3.0",\n    "cryptography>=41.0.0",')

with open('pyproject.toml', 'w', encoding='utf-8') as f:
    f.write(content)
