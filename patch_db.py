with open('app/database.py', 'r') as f:
    c = f.read()

# Fix CREATE TABLE customers
old_customers = '''CREATE TABLE IF NOT EXISTS customers (
                id              TEXT PRIMARY KEY,
                company_name    TEXT NOT NULL,
                is_active       INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );'''
new_customers = '''CREATE TABLE IF NOT EXISTS customers (
                id              TEXT PRIMARY KEY,
                company_name    TEXT NOT NULL,
                portal_suspended INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );'''
c = c.replace(old_customers, new_customers)

# Fix PRAGMA foreign_keys
old_conn = '''def get_db():
    conn = sqlite3.connect(
        current_app.config['DATABASE_PATH'],
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    return conn'''
new_conn = '''def get_db():
    conn = sqlite3.connect(
        current_app.config['DATABASE_PATH'],
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn'''
c = c.replace(old_conn, new_conn)

# Fix queries
c = c.replace('DEACTIVATE_CUSTOMER = "UPDATE customers SET is_active=0 WHERE id=?"', 'DELETE_CUSTOMER = "DELETE FROM customers WHERE id=?"')
c = c.replace('GET_ALL_CUSTOMERS = "SELECT * FROM customers WHERE is_active = 1 ORDER BY company_name"', 'GET_ALL_CUSTOMERS = "SELECT * FROM customers ORDER BY company_name"')

with open('app/database.py', 'w') as f:
    f.write(c)
