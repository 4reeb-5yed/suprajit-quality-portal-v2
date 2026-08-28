with open('app/database.py', 'r', encoding='utf-8') as f:
    text = f.read()
insert_idx = text.find('CREATE TABLE IF NOT EXISTS audit_log')
if insert_idx != -1:
    new_table = '''
            CREATE TABLE IF NOT EXISTS search_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latency_ms REAL NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            );
'''
    text = text[:insert_idx] + new_table + text[insert_idx:]
    with open('app/database.py', 'w', encoding='utf-8') as f:
        f.write(text)
