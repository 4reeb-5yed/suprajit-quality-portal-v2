with open('app/database.py', 'r') as f:
    c = f.read()

c = c.replace('FOREIGN KEY (customer_id) REFERENCES customers(id),', 'FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,')

with open('app/database.py', 'w') as f:
    f.write(c)
