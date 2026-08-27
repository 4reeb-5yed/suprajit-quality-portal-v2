with open('app/database.py', 'r') as f:
    content = f.read()

# Replace Queries
start_idx = content.find('# --- QUERY CATALOG ---')
if start_idx == -1:
    start_idx = content.find('# Customers')

queries = '''
# Customers
GET_ALL_CUSTOMERS = "SELECT * FROM customers ORDER BY company_name"
GET_CUSTOMER_BY_ID = "SELECT * FROM customers WHERE id = ?"
INSERT_CUSTOMER = "INSERT INTO customers (id, company_name) VALUES (?, ?)"
UPDATE_CUSTOMER = "UPDATE customers SET company_name=? WHERE id=?"
DELETE_CUSTOMER = "DELETE FROM customers WHERE id=?"
TOGGLE_CUSTOMER_SUSPENSION = "UPDATE customers SET portal_suspended=? WHERE id=?"

# Customer Recipes
GET_CUSTOMER_RECIPES = "SELECT recipe_name FROM customer_recipes WHERE customer_id = ?"
INSERT_CUSTOMER_RECIPE = "INSERT INTO customer_recipes (customer_id, recipe_name) VALUES (?, ?)"
DELETE_CUSTOMER_RECIPE = "DELETE FROM customer_recipes WHERE customer_id = ? AND recipe_name = ?"

# Users
GET_USER_BY_USERNAME = "SELECT * FROM users WHERE username = ?"
GET_USER_BY_EMAIL = "SELECT * FROM users WHERE email = ?"
GET_USER_BY_ID = "SELECT * FROM users WHERE id = ?"
GET_USERS_BY_CUSTOMER = "SELECT * FROM users WHERE customer_id = ?"
INSERT_USER = "INSERT INTO users (username, email, password_hash, display_name, role, customer_id) VALUES (?, ?, ?, ?, ?, ?)"
UPDATE_USER_PASSWORD = "UPDATE users SET password_hash = ? WHERE id = ?"
UPDATE_USER_LOCKOUT = "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?"
TOGGLE_USER_ACCESS = "UPDATE users SET is_active = ? WHERE id = ?"

# Reports
INSERT_REPORT = """
    INSERT OR IGNORE INTO reports 
    (batch_run_id, recipe_name, report_date, report_time, serial_raw, 
     serial_normalized, original_filename, file_path, file_hash, file_size_bytes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
GET_REPORT_BY_ID = "SELECT * FROM reports WHERE id = ?"

# System Settings
GET_SETTING = "SELECT value FROM system_settings WHERE key = ?"
SET_SETTING = "INSERT OR REPLACE INTO system_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))"
'''

content = content[:start_idx] + queries.strip()
with open('app/database.py', 'w') as f:
    f.write(content)
