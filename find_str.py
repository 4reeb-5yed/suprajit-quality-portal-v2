import re
with open('app/routes/admin.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'render_template' in line and 'customers.html' in line:
        print(f"Line {i}: {line.strip()}")
