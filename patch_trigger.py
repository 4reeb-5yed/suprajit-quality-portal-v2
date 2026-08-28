with open('app/database.py', 'r', encoding='utf-8') as f:
    text = f.read()

trigger_sql = '''
            CREATE TRIGGER IF NOT EXISTS search_metrics_prune AFTER INSERT ON search_metrics BEGIN
                DELETE FROM search_metrics WHERE id <= (new.id - 10000);
            END;
'''

if "search_metrics_prune" not in text:
    insert_idx = text.find("CREATE TABLE IF NOT EXISTS audit_log")
    text = text[:insert_idx] + trigger_sql + "\n" + text[insert_idx:]
    with open('app/database.py', 'w', encoding='utf-8') as f:
        f.write(text)
