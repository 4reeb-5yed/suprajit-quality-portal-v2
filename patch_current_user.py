with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = '''    # Ensure they aren't deleting themselves!
    if str(user_id) == str(g.user.id):'''

new = '''    from flask_login import current_user
    # Ensure they aren't deleting themselves!
    if str(user_id) == str(current_user.id):'''

c = c.replace(old, new)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
