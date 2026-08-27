import sqlite3
conn = sqlite3.connect('data/portal.db')
conn.execute("DELETE FROM batch_runs WHERE status = 'failed'")
conn.commit()
conn.close()
