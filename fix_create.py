with open('app/database.py', 'r') as f:
    c = f.read()

old_str = "files_skipped   INTEGER DEFAULT 0,"
new_str = "files_skipped   INTEGER DEFAULT 0,\n                files_failed    INTEGER DEFAULT 0,"
c = c.replace(old_str, new_str)

with open('app/database.py', 'w') as f:
    f.write(c)
