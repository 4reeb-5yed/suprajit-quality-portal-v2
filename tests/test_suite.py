import os

from app.sync_engine import SyncEngine
from app.parser import parse_filename

# -----------------
# 1. PARSER TESTS
# -----------------
def test_parse_filename():
    assert parse_filename('EV_TPS_13-06-2026_22.33.21_12.xlsx')['recipe_name'] == 'EV_TPS'
    assert parse_filename('EV_TPS_13-06-2026_22.33.21_12 (1).xlsx')['recipe_name'] == 'EV_TPS'

# -----------------
# 2. SYNC ENGINE TESTS
# -----------------
def test_sync_engine_ingestion(app):
    with app.app_context():
        db_path = app.config['DATABASE_PATH']
        storage = app.config['STORAGE_FOLDER']
        
        recipe_dir = os.path.join(storage, 'Test Reports', 'TEST_RECIPE')
        os.makedirs(recipe_dir, exist_ok=True)
        dummy_file = os.path.join(recipe_dir, 'TEST_RECIPE_13-06-2026_22.33.21_12.xlsx')
        with open(dummy_file, 'wb') as f:
            f.write(b"dummy data")
            
        engine = SyncEngine(db_path, storage)
        engine._get_folder_customer_mapping = lambda: {storage: None}
        
        assert engine.run_batch(full_sync=True) == 1
        assert engine.run_batch(full_sync=True) == 0

# -----------------
# 3. AUTH & ROUTING TESTS
# -----------------
def test_login_redirect_and_auth(client, app):
    # Try logging in
    with client:
        rv = client.post('/login', data={'username': 'testadmin', 'password': 'Password123!'}, follow_redirects=True)
        assert rv.status_code == 200
        
        # Test direct settings access
        rv2 = client.get('/admin/settings', follow_redirects=True)
        assert rv2.status_code == 200
        assert b"System Configuration" in rv2.data or b"System Administrators" in rv2.data

def test_404_error_handler(client, app):
    rv = client.get('/favicon.ico')
    assert rv.status_code == 404



