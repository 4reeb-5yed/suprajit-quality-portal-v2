with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = '''@admin_bp.route('/customers/delete_user', methods=['POST'])
@login_required
@admin_required
def delete_user():'''

new = '''@admin_bp.route('/customers/delete_user', methods=['POST'])
def delete_user():'''

c = c.replace(old, new)
with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
