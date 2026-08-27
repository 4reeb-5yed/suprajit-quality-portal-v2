# -*- coding: utf-8 -*-
import io
with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''      customer_id = request.form.get('customer_id')
      username = request.form.get('username', '').strip()
      email = request.form.get('email', '').strip()
      password = request.form.get('password', '')
      display_name = request.form.get('display_name', '').strip()
      
      if not username or not password:
          flash("Username and Password are required.", "error")
          return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
          
      pwd_hash = generate_password_hash(password)
      
      try:
          g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, 'customer_viewer', customer_id))'''

replacement = '''      customer_id = request.form.get('customer_id')
      role = request.form.get('role', 'customer_viewer')
      if role == 'admin':
          customer_id = None
          
      username = request.form.get('username', '').strip()
      email = request.form.get('email', '').strip()
      password = request.form.get('password', '')
      display_name = request.form.get('display_name', '').strip()
      
      if not username or not password:
          flash("Username and Password are required.", "error")
          return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))
          
      pwd_hash = generate_password_hash(password)
      
      try:
          g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, role, customer_id))'''

c = c.replace(target, replacement)

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
