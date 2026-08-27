import sqlite3
conn = sqlite3.connect('data/portal.db')
rows = conn.execute('SELECT id, folder_path FROM source_folders').fetchall()
for r in rows:
    clean_path = r[1].strip('"').strip("'")
    conn.execute('UPDATE source_folders SET folder_path=? WHERE id=?', (clean_path, r[0]))
conn.commit()
print('Cleaned paths in database.')
