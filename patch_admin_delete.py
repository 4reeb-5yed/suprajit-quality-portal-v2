# -*- coding: utf-8 -*-
import io
with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

target1 = '''      available_recipes = [r['recipe_name'] for r in g.db.execute("SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name").fetchall()]
      return render_template('admin/customers.html', 
                             customers=customer_list, 
                             customer_recipes=customer_recipes,
                             customer_users=customer_users,
                             available_recipes=available_recipes)'''

replacement1 = '''      admins = g.db.execute("SELECT * FROM users WHERE role = 'admin'").fetchall()
      
      available_recipes = [r['recipe_name'] for r in g.db.execute("SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name").fetchall()]
      return render_template('admin/customers.html', 
                             customers=customer_list, 
                             customer_recipes=customer_recipes,
                             customer_users=customer_users,
                             available_recipes=available_recipes,
                             system_admins=admins)'''

c = c.replace(target1, replacement1)

delete_route = '''
@admin_bp.route('/users/delete', methods=['POST'])
def delete_user():
    from flask import request, flash, g
    user_id = request.form.get('user_id')
    user = g.db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        flash("User not found.", "error")
        return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
        
    if user['role'] == 'admin':
        admin_count = g.db.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'").fetchone()['c']
        if admin_count <= 1:
            flash("Cannot delete the last remaining administrator account. Create a new one first.", "error")
            return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
            
    g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    g.db.commit()
    flash("User deleted successfully.", "success")
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
'''

c = c + delete_route

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
