import sqlite3
conn = sqlite3.connect('data/portal.db')
conn.execute('UPDATE customers SET is_active=1')
conn.commit()
