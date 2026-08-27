import sqlite3
db_path = r'C:\Users\humza\suprajit_v2\dist\SuprajitQualityPortal\data\portal.db'
try:
    conn = sqlite3.connect(db_path)
    res = conn.execute("SELECT value FROM system_settings WHERE key='root_search_path'").fetchone()
    print(res[0] if res else "Not found")
    conn.close()
except Exception as e:
    print(e)
