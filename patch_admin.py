with open('app/routes/admin.py', 'r') as f:
    c = f.read()
c = c.replace("folder_path = request.form.get('folder_path', '').strip()", "folder_path = request.form.get('folder_path', '').strip().strip('\"').strip(\"'\")")
with open('app/routes/admin.py', 'w') as f:
    f.write(c)
