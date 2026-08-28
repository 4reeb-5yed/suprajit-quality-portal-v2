import pytest
def test_debug(client, app):
    with app.app_context():
        from app.database import get_connection
        conn = get_connection(app.config['DATABASE_PATH'])
        from werkzeug.security import generate_password_hash
        p_hash = generate_password_hash('admin123')
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('CUST_A', 'Company A')")
        conn.execute("INSERT OR IGNORE INTO users (username, password_hash, display_name, role, customer_id) VALUES ('cust_a', ?, 'Cust A', 'user', 'CUST_A')", (p_hash,))
        conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES ('CUST_A', 'Recipe_A')")
        conn.execute("INSERT OR IGNORE INTO reports (file_path, original_filename, recipe_name, report_date, report_time, serial_raw) VALUES ('dummy/path/a.csv', 'a.csv', 'Recipe_A', '2026-01-01', '120000', '123')")
        conn.commit()

        # Debug
        print(conn.execute("SELECT * FROM reports").fetchall())
        print(conn.execute("SELECT * FROM customer_recipes").fetchall())
        print(conn.execute("SELECT * FROM users").fetchall())

        # Test the query
        q = "SELECT * FROM reports WHERE recipe_name IN (SELECT recipe_name FROM customer_recipes WHERE customer_id = ?) AND recipe_name = ?"
        print("QUERY MATCH:", conn.execute(q, ('CUST_A', 'Recipe_A')).fetchall())
