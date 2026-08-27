with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_route = '''@admin_bp.route('/customers/delete_user', methods=['POST'])
@login_required
@admin_required
def delete_user():
    user_id = __import__('flask').request.form.get('user_id')
    
    # Ensure they aren't deleting themselves!
    if str(user_id) == str(g.user.id):
        __import__('flask').flash("You cannot delete your own admin account.", "error")
        return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
        
    g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    g.db.commit()
    __import__('flask').flash("User account permanently deleted.", "success")
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/trigger_sync', methods=['POST'])'''

c = c.replace("@admin_bp.route('/trigger_sync', methods=['POST'])", new_route)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
