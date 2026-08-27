with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix Bug 1
old_import = "from flask import Blueprint, render_template, g, abort, request"
new_import = "from flask import Blueprint, render_template, g, abort, request, current_app"
c = c.replace(old_import, new_import)

# Fix Bug 2
old_diag = "last_run = g.db.execute(\"SELECT * FROM batch_runs ORDER BY start_time DESC LIMIT 1\").fetchone()"
new_diag = "last_run = g.db.execute(\"SELECT * FROM batch_runs ORDER BY run_started DESC LIMIT 1\").fetchone()"
c = c.replace(old_diag, new_diag)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
