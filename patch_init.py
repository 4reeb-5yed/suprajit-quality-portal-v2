import re

with open('app/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the duplicate csrf initialization inside the function scope that causes UnboundLocalError
content = content.replace("    from flask_wtf.csrf import CSRFProtect\n    csrf = CSRFProtect()\n    csrf.init_app(app)", "")

with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)
