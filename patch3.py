import os

with open('app/helpers.py', 'r', encoding='utf-8') as f:
    h = f.read()

h = h.replace('    from cryptography.fernet import Fernet\n', '')
if 'from cryptography.fernet import Fernet' not in h:
    h = h.replace('import base64\nfrom flask import current_app\n', 'import base64\nfrom flask import current_app\nfrom cryptography.fernet import Fernet\n')

with open('app/helpers.py', 'w', encoding='utf-8') as f:
    f.write(h)

with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
    ci = f.read()

ci = ci.replace('pip install flask flask-limiter flask-login flask-mail flask-wtf python-dotenv waitress apscheduler\n        pip install pytest pytest-flask pytest-cov', 'pip install .[dev]\n        pip install pytest pytest-flask pytest-cov')
ci = ci.replace('pip install flask flask-limiter flask-login flask-mail flask-wtf python-dotenv waitress apscheduler\n        pip install pyinstaller pytest pytest-flask', 'pip install .\n        pip install pyinstaller pytest pytest-flask')

with open('.github/workflows/ci.yml', 'w', encoding='utf-8') as f:
    f.write(ci)

with open('pyproject.toml', 'r', encoding='utf-8') as f:
    toml = f.read()

if 'pytest-cov' not in toml:
    toml = toml.replace('[project.scripts]', '[project.optional-dependencies]\ndev = ["pytest", "pytest-flask", "pytest-cov"]\n\n[project.scripts]')

with open('pyproject.toml', 'w', encoding='utf-8') as f:
    f.write(toml)
