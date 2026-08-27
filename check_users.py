import sqlite3
import os

db_path = r'C:\Users\humza\suprajit_v2\data\portal.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
users = conn.execute("SELECT id, username, role FROM users").fetchall()
for u in users:
    print(f"ID: {u['id']}, Username: {u['username']}, Role: {u['role']}")
conn.close()
