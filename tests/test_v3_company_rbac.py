import pytest
from app import create_app
from app.database import get_connection

def test_three_tier_rbac_and_recipe_permissions(tmp_path):
    db_path = str(tmp_path / "test_portal.db")
    app = create_app({
        "TESTING": True,
        "DATABASE_PATH": db_path,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key"
    })
    
    with app.app_context():
        conn = get_connection(db_path)
        
        # 1. Setup Customer & Master Recipes
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('tvs', 'TVS Motor Company')")
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('mahindra', 'Mahindra Auto')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'I-QUBE-BATTERY')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('tvs', 'JUPITER-125')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('mahindra', 'THAR-DIESEL')")
        
        # 2. Setup Reports
        conn.execute("""INSERT INTO reports (recipe_name, report_date, serial_raw, serial_normalized, original_filename, file_path, file_hash)
                        VALUES ('I-QUBE-BATTERY', '2026-06-13', '101', '101', 'iqube.xlsx', 'Z:/tvs/iqube.xlsx', 'h1')""")
        conn.execute("""INSERT INTO reports (recipe_name, report_date, serial_raw, serial_normalized, original_filename, file_path, file_hash)
                        VALUES ('JUPITER-125', '2026-06-13', '102', '102', 'jupiter.xlsx', 'Z:/tvs/jupiter.xlsx', 'h2')""")
        conn.execute("""INSERT INTO reports (recipe_name, report_date, serial_raw, serial_normalized, original_filename, file_path, file_hash)
                        VALUES ('THAR-DIESEL', '2026-06-13', '103', '103', 'thar.xlsx', 'Z:/mahindra/thar.xlsx', 'h3')""")
                        
        # 3. Create Users
        from werkzeug.security import generate_password_hash
        pwd = generate_password_hash("Pass@1234")
        # TVS Admin
        conn.execute("INSERT INTO users (username, email, password_hash, display_name, role, customer_id) VALUES ('tvs_admin', 'admin@tvs.com', ?, 'TVS Admin', 'company_admin', 'tvs')", (pwd,))
        # TVS User 1 (ALL recipes)
        conn.execute("INSERT INTO users (username, email, password_hash, display_name, role, customer_id, access_mode) VALUES ('tvs_all', 'all@tvs.com', ?, 'TVS All', 'customer_viewer', 'tvs', 'ALL')", (pwd,))
        # TVS User 2 (CUSTOM recipe: only I-QUBE-BATTERY)
        conn.execute("INSERT INTO users (username, email, password_hash, display_name, role, customer_id, access_mode) VALUES ('tvs_ev', 'ev@tvs.com', ?, 'TVS EV', 'customer_viewer', 'tvs', 'CUSTOM')", (pwd,))
        
        u2_id = conn.execute("SELECT id FROM users WHERE username = 'tvs_ev'").fetchone()['id']
        conn.execute("INSERT INTO user_recipes (user_id, recipe_name) VALUES (?, 'I-QUBE-BATTERY')", (u2_id,))
        
        conn.commit()
        conn.close()
        
    client = app.test_client()
    
    # Test 1: TVS User 1 (ALL mode) can see I-QUBE and JUPITER, but NOT THAR
    client.post('/login', data={'username': 'tvs_all', 'password': 'Pass@1234'}, follow_redirects=True)
    res = client.get('/search?q=10')
    assert b'I-QUBE-BATTERY' in res.data
    assert b'JUPITER-125' in res.data
    assert b'THAR-DIESEL' not in res.data
    client.get('/logout', follow_redirects=True)
    
    # Test 2: TVS User 2 (CUSTOM mode) can ONLY see I-QUBE-BATTERY, NOT JUPITER or THAR
    client.post('/login', data={'username': 'tvs_ev', 'password': 'Pass@1234'}, follow_redirects=True)
    res = client.get('/search?q=10')
    assert b'I-QUBE-BATTERY' in res.data
    assert b'JUPITER-125' not in res.data
    assert b'THAR-DIESEL' not in res.data
    client.get('/logout', follow_redirects=True)
    
    # Test 3: TVS Company Admin can access /company/users
    client.post('/login', data={'username': 'tvs_admin', 'password': 'Pass@1234'}, follow_redirects=True)
    res = client.get('/company/users')
    assert res.status_code == 200
    assert b'TVS Motor Company Management' in res.data
    
    # Test 4: TVS Company Admin creates a new team member
    res = client.post('/company/users/add', data={
        'username': 'tvs_operator99',
        'display_name': 'Operator 99',
        'email': 'op99@tvs.com',
        'password': 'TempPass@123',
        'role': 'customer_viewer'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'tvs_operator99' in res.data
    
    # Test 5: Boundary enforcement - Company Admin CANNOT toggle users from another company
    with app.app_context():
        conn = get_connection(db_path)
        conn.execute("INSERT INTO users (username, password_hash, display_name, role, customer_id) VALUES ('m_user', ?, 'M User', 'customer_viewer', 'mahindra')", (pwd,))
        m_id = conn.execute("SELECT id FROM users WHERE username = 'm_user'").fetchone()['id']
        conn.commit()
        conn.close()
        
    res = client.post('/company/users/toggle', data={'user_id': m_id, 'is_active': 0})
    assert res.status_code == 403 # Strictly forbidden across company boundary!
