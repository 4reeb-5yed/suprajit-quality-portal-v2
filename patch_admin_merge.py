# -*- coding: utf-8 -*-
import io
import re

with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Delete the first one
pattern1 = re.compile(r"@admin_bp\.route\('/customers/delete_user', methods=\['POST'\]\)\ndef delete_user\(\):.*?return __import__\('flask'\)\.redirect\(__import__\('flask'\)\.url_for\('admin\.customers'\)\)\n", re.DOTALL)
c = pattern1.sub('', c)

# Delete the second one
pattern2 = re.compile(r"@admin_bp\.route\('/users/delete', methods=\['POST'\]\)\ndef delete_user\(\):.*?return __import__\('flask'\)\.redirect\(__import__\('flask'\)\.url_for\('admin\.customers'\)\)\n", re.DOTALL)
c = pattern2.sub('', c)

combined = '''
@admin_bp.route('/users/delete', methods=['POST'])
def delete_user():
    from flask import request, flash, g, redirect, url_for
    from flask_login import current_user
    
    user_id = request.form.get('user_id')
    
    if str(user_id) == str(current_user.id):
        flash("You cannot delete your currently active account.", "error")
        return redirect(url_for('admin.customers'))
        
    user = g.db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('admin.customers'))
        
    if user['role'] == 'admin':
        admin_count = g.db.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'").fetchone()['c']
        if admin_count <= 1:
            flash("Cannot delete the last remaining administrator account. Create a new one first.", "error")
            return redirect(url_for('admin.customers'))
            
    g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    g.db.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for('admin.customers'))
'''

c = c + combined

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
