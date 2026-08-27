with open('app/routes/admin.py', 'r') as f:
    c = f.read()
c = c.replace('"C:\\"', '"C:\\\\"')
with open('app/routes/admin.py', 'w') as f:
    f.write(c)
