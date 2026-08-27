import sqlite3
conn = sqlite3.connect('data/portal.db')
try:
    conn.execute("ALTER TABLE batch_runs ADD COLUMN files_failed INTEGER DEFAULT 0")
    conn.commit()
    print("Added files_failed column!")
except Exception as e:
    print(f"Error: {e}")
conn.close()
