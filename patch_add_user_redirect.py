# -*- coding: utf-8 -*-
import io
import re

with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''          g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, role, customer_id))
          g.db.commit()
          
          # Send welcome email if email was provided'''

replacement = '''          g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, role, customer_id))
          g.db.commit()
          
          # Send welcome email if email was provided'''

target_end = '''              t = threading.Thread(target=send_email, args=(app_context, request.host_url))
              t.start()
              
      return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))'''

replacement_end = '''              t = threading.Thread(target=send_email, args=(app_context, request.host_url))
              t.start()
              
      if role == 'admin':
          return __import__('flask').redirect(__import__('flask').url_for('admin.settings'))
      return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))'''

c = c.replace(target_end, replacement_end)

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
