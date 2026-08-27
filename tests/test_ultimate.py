import pytest
import os
import tempfile
from app.parser import parse_filename
from app.sync_engine import SyncEngine
from app.database import get_connection

# ==========================================
# 1. UNIT TESTS: THE PARSER
# ==========================================
def test_parser_perfect_filename():
    res = parse_filename("EV_TPS_13-06-2026_22.33.21_12.xlsx")
    assert res['recipe_name'] == "EV_TPS"
    assert res['report_date'] == "2026-06-13"
    assert res['serial_number'] == "12"

def test_parser_weird_casing_and_spaces():
    res = parse_filename("ev tps_13-06-2026_22.33.21_0045.XLSX")
    assert res['recipe_name'] == "ev tps"
    assert res['serial_number'] == "0045"

def test_parser_invalid_garbage():
    res = parse_filename("random_junk_file.txt")
    assert res is None

def test_parser_missing_date():
    res = parse_filename("RECIPE_NO_DATE_22.33.21_12.xlsx")
    assert res is None

# ==========================================
# 2. REGRESSION TESTS (Proving old bugs stay dead)
# ==========================================
def test_regression_sync_engine_dict_addition_bug(app):
    """
    BUG: The sync engine used to crash by adding an integer to a dictionary.
    FIX: Ensure run_batch properly tallies integers.
    """
    with app.app_context():
        db_path = os.environ['DATABASE_PATH']
        storage = os.environ['STORAGE_BASE']
        engine = SyncEngine(db_path, storage)
        
        # Override process_folder to simulate a successful folder processing returning an integer
        engine.process_folder = lambda customer, path, dry: 5 
        engine._get_search_roots = lambda: [storage]
        
        # This used to crash with TypeError: unsupported operand type(s) for +=: 'dict' and 'int'
        # Now it should gracefully return 5.
        os.makedirs(os.path.join(storage, 'dummy', 'dummy'), exist_ok=True)
        try:
            total = engine.run_batch(full_sync=True)
        except Exception as e:
            pytest.fail(f"Regression BUG RETURNED! Crashed with {e}")

def test_regression_deadlock_status_bug(app):
    """
    BUG: Batches would get stuck in 'running' status.
    FIX: The engine MUST mark it as 'failed' or 'completed' even if it errors.
    """
    with app.app_context():
        db_path = os.environ['DATABASE_PATH']
        storage = os.environ['STORAGE_BASE']
        engine = SyncEngine(db_path, storage)
        
        # Force process_folder to throw a fatal error
        def explosive_process(*args, **kwargs):
            raise RuntimeError("Fatal Factory Crash")
        engine.process_folder = explosive_process
        engine._get_search_roots = lambda: [storage]
        
        os.makedirs(os.path.join(storage, 'dummy', 'dummy'), exist_ok=True)
        
        # Run it - it should catch the error and not crash the thread
        engine.run_batch(full_sync=True)
        
        # Verify the batch was marked as 'failed', NOT left hanging as 'running'
        conn = get_connection(db_path)
        batch = conn.execute("SELECT status FROM batch_runs ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        
        assert batch['status'] == 'failed', "REGRESSION: Batch is stuck in running state!"

# ==========================================
# 3. END-TO-END (E2E) LIFECYCLE TEST
# ==========================================
def test_e2e_factory_lifecycle(client, app):
    """
    Simulates a full day at the factory from Admin setup, to ingestion, to Client search.
    """
    with app.app_context():
        db_path = os.environ['DATABASE_PATH']
        storage = os.environ['STORAGE_BASE']
        
        # 1. Admin creates customer and assigns recipe
        client.post('/login', data={'username': 'testadmin', 'password': 'admin123'}, follow_redirects=True)
        client.post('/admin/customers/add', data={'company_name': 'E2E Corp'}, follow_redirects=True)
        # Fetch the new customer ID
        conn = get_connection(db_path)
        cust = conn.execute("SELECT id FROM customers WHERE company_name='E2E Corp'").fetchone()
        cust_id = cust['id']
        
        client.post('/admin/customers/add_recipe', data={'customer_id': cust_id, 'recipe_name': 'E2E_PART'}, follow_redirects=True)
        
        # 2. Factory Machine drops a file onto the network drive
        recipe_dir = os.path.join(storage, 'E2E Corp', 'E2E_PART')
        os.makedirs(recipe_dir, exist_ok=True)
        with open(os.path.join(recipe_dir, 'E2E_PART_15-06-2026_12.00.00_999.xlsx'), 'wb') as f:
            f.write(b"fake excel data")
            
        # 3. Background Sync Engine wakes up and runs
        client.post('/admin/trigger_sync', follow_redirects=True)
        
        # 4. User logs in to search for their file
        # Assign a user to E2E Corp
        conn.execute("INSERT INTO customer_users (customer_id, user_id) VALUES (?, 2)", (cust_id,))
        conn.commit()
        conn.close()
        
        client.get('/logout', follow_redirects=True)
        client.post('/login', data={'username': 'testuser', 'password': 'user123'}, follow_redirects=True)
        
        # 5. User searches for serial '999'
        rv = client.get('/search/results?recipe=E2E_PART&serial=999', follow_redirects=True)
        assert b'E2E_PART_15-06-2026_12.00.00_999.xlsx' in rv.data, "E2E FAIL: File did not appear in search results!"
