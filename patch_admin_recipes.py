with open('app/routes/admin.py', 'r') as f:
    c = f.read()

old_str = "    return render_template('admin/customers.html', \\n                           customers=customer_list, \\n                           customer_recipes=customer_recipes,\\n                           customer_users=customer_users)"

new_str = '''    available_recipes = [r['recipe_name'] for r in g.db.execute("SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name").fetchall()]
    return render_template('admin/customers.html', 
                           customers=customer_list, 
                           customer_recipes=customer_recipes,
                           customer_users=customer_users,
                           available_recipes=available_recipes)'''

import re
c = re.sub(r'return render_template\(\'admin/customers\.html\',\s*customers=customer_list,\s*customer_recipes=customer_recipes,\s*customer_users=customer_users\)', new_str, c)

with open('app/routes/admin.py', 'w') as f:
    f.write(c)
