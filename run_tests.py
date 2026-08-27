import unittest
import os
import tempfile
import sqlite3
from werkzeug.security import generate_password_hash
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app
from app.parser import parse_filename
from app.database import ensure_schema

class SuprajitRigorousTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['DATABASE_PATH'] = self.db_path
        os.environ['SECRET_KEY'] = 'test_secret'
        os.environ['TESTING'] = 'True'
        
        self.app = create_app()
        self.app.config['DATABASE_PATH'] = self.db_path
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        conn = sqlite3.connect(self.db_path)
        ensure_schema(conn)  # Force schema creation on temp DB
        conn.execute("INSERT INTO customers (id, company_name) VALUES ('CUST_001', 'TestCo')")
        p_hash = generate_password_hash('cust123')
        conn.execute("INSERT INTO users (username, password_hash, display_name, role, customer_id, is_active) VALUES ('cust_user', ?, 'Cust User', 'customer_viewer', 'CUST_001', 1)", (p_hash,))
        self.cust_id = conn.execute("SELECT id FROM users WHERE username = 'cust_user'").fetchone()[0]
        a_hash = generate_password_hash('admin123')
        conn.execute("INSERT INTO users (username, password_hash, display_name, role, is_active) VALUES ('admin_user', ?, 'Admin', 'admin', 1)", (a_hash,))
        conn.execute("INSERT INTO reports (recipe_name, report_date, report_time, serial_raw, serial_normalized, original_filename, file_path, file_hash) VALUES ('TEST_RECIPE', '2026-08-01', '12:00:00', '001', '001', 'TEST.xlsx', 'C:\\fake.xlsx', 'hash123')")
        conn.execute("INSERT INTO customer_recipes (customer_id, recipe_name) VALUES ('CUST_001', 'TEST_RECIPE')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.app_context.pop()
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except:
            pass

    def test_parser_valid(self):
        res = parse_filename("EV_TPS_21-08-2026_14.30.00_0045.xlsx")
        self.assertEqual(res['recipe_name'], "EV_TPS")
        
    def test_parser_invalid(self):
        res = parse_filename("random_file.txt")
        self.assertIsNone(res)

    def test_login_success_admin(self):
        res = self.client.post('/login', data={'username': 'admin_user', 'password': 'admin123'}, follow_redirects=True)
        self.assertIn(b'Dashboard', res.data)

    def test_login_success_customer(self):
        res = self.client.post('/login', data={'username': 'cust_user', 'password': 'cust123'}, follow_redirects=True)
        self.assertIn(b'Search', res.data)

    def test_login_failure(self):
        res = self.client.post('/login', data={'username': 'admin_user', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b'Invalid credentials', res.data)

    def test_admin_route_protection(self):
        self.client.post('/login', data={'username': 'cust_user', 'password': 'cust123'})
        res = self.client.get('/admin/')
        self.assertEqual(res.status_code, 403)
        
    def test_unauthenticated_protection(self):
        res = self.client.get('/admin/', follow_redirects=False)
        self.assertEqual(res.status_code, 302)

    def test_search_empty_state(self):
        self.client.post('/login', data={'username': 'cust_user', 'password': 'cust123'})
        res = self.client.get('/search/results')
        self.assertIn(b'Please select a recipe', res.data)
        
    def test_search_results_security(self):
        self.client.post('/login', data={'username': 'cust_user', 'password': 'cust123'})
        res = self.client.get('/search/results?recipe=TEST_RECIPE')
        self.assertIn(b'TEST_RECIPE', res.data)

    def test_admin_delete_user(self):
        self.client.post('/login', data={'username': 'admin_user', 'password': 'admin123'})
        res = self.client.post('/admin/customers/delete_user', data={'user_id': self.cust_id}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main(verbosity=2)
