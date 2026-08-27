with open('app/routes/admin.py', 'r') as f:
    c = f.read()

lines = c.split('\n')
for i, line in enumerate(lines):
    if 'available_recipes = ' in line and 'SELECT DISTINCT recipe_name' in line:
        lines[i] = '    ' + line.lstrip()

with open('app/routes/admin.py', 'w') as f:
    f.write('\n'.join(lines))
