import sqlite3
conn = sqlite3.connect('data/portal.db')
conn.execute("DROP TABLE IF EXISTS reports")
conn.execute("DROP TABLE IF EXISTS reports_fts")
conn.execute("DROP TABLE IF EXISTS batch_runs")
# Ensure schema runs
from app.database import ensure_schema
ensure_schema(conn)
conn.close()
