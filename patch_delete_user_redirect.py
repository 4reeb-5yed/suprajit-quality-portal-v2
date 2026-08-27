# -*- coding: utf-8 -*-
import io

with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    g.db.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for('admin.customers'))'''

replacement = '''    g.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    g.db.commit()
    flash("User deleted successfully.", "success")
    if user['role'] == 'admin':
        return redirect(url_for('admin.settings'))
    return redirect(url_for('admin.customers'))'''

c = c.replace(target, replacement)

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
