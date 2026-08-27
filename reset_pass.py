import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = r'C:\Users\humza\suprajit_v2\data\portal.db'
conn = sqlite3.connect(db_path)
new_hash = generate_password_hash('admin123')
conn.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (new_hash,))
conn.commit()
conn.close()
print("Password reset successfully!")
