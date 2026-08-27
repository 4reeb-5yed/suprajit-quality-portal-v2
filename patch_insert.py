with open('app/database.py', 'r') as f:
    c = f.read()
c = c.replace('INSERT_CUSTOMER = "INSERT INTO customers (id, company_name, is_active) VALUES (?, ?, ?)"', 'INSERT_CUSTOMER = "INSERT INTO customers (id, company_name) VALUES (?, ?)"')
with open('app/database.py', 'w') as f:
    f.write(c)

with open('app/routes/admin.py', 'r') as f:
    c = f.read()
c = c.replace('g.db.execute(INSERT_CUSTOMER, (c_id, c_name, 1))', 'g.db.execute(INSERT_CUSTOMER, (c_id, c_name))')
with open('app/routes/admin.py', 'w') as f:
    f.write(c)
