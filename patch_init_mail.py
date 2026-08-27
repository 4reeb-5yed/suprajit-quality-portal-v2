with open('app/__init__.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('from flask_mail import Mail', '')
c = c.replace('mail = Mail()', '')
c = c.replace('mail.init_app(app)', '')

with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(c)
