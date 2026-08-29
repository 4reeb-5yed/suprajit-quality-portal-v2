import os
from unittest.mock import patch

from app.sync_engine import SyncEngine

def test_dimension_1_file_locked(app):
    with app.app_context():
        engine = SyncEngine(app.config['DATABASE_PATH'], app.config['STORAGE_FOLDER'])
        engine._get_search_roots = lambda: [app.config['STORAGE_FOLDER']]
        
        test_file = os.path.join(app.config['STORAGE_FOLDER'], "EV_TPS_13-06-2026_22.33.21_12.xlsx")
        with open(test_file, 'w') as f: f.write("locked")
        
        with patch('app.sync_engine.ensure_file_safe', return_value=False):
            inserted = engine.run_batch(full_sync=True)
            assert inserted == 0

def test_dimension_2_unparseable_junk(app):
    with app.app_context():
        engine = SyncEngine(app.config['DATABASE_PATH'], app.config['STORAGE_FOLDER'])
        engine._get_search_roots = lambda: [app.config['STORAGE_FOLDER']]
        
        test_file = os.path.join(app.config['STORAGE_FOLDER'], "random_music.mp3.xlsx")
        with open(test_file, 'w') as f: f.write("junk")
        
        inserted = engine.run_batch(full_sync=True)
        assert inserted == 0

def test_dimension_3_duplicate_prevention(app):
    with app.app_context():
        engine = SyncEngine(app.config['DATABASE_PATH'], app.config['STORAGE_FOLDER'])
        engine._get_search_roots = lambda: [app.config['STORAGE_FOLDER']]
        
        test_file = os.path.join(app.config['STORAGE_FOLDER'], "EV_TPS_14-06-2026_22.33.21_12.xlsx")
        with open(test_file, 'w') as f: f.write("duplicate_test")
        
        engine.run_batch(full_sync=True)
        inserted_second = engine.run_batch(full_sync=True)
        assert inserted_second == 0

def test_dimension_4_dry_run_execution(app):
    with app.app_context():
        engine = SyncEngine(app.config['DATABASE_PATH'], app.config['STORAGE_FOLDER'])
        engine._get_search_roots = lambda: [app.config['STORAGE_FOLDER']]
        
        test_file = os.path.join(app.config['STORAGE_FOLDER'], "EV_TPS_15-06-2026_22.33.21_12.xlsx")
        with open(test_file, 'w') as f: f.write("dry_run_test")
        
        output = engine.execute_dry_run()
        assert "Would Insert:" in output

def test_dimension_5_database_crash_recovery(app):
    with app.app_context():
        engine = SyncEngine(app.config['DATABASE_PATH'], app.config['STORAGE_FOLDER'])
        engine._get_search_roots = lambda: [app.config['STORAGE_FOLDER']]
        
        test_file = os.path.join(app.config['STORAGE_FOLDER'], "EV_TPS_16-06-2026_22.33.21_12.xlsx")
        with open(test_file, 'w') as f: f.write("db_crash")
        
        # Patch the parse_filename to raise an exception instead of patching C-extensions
        with patch('app.sync_engine.hash_file', side_effect=Exception("SIMULATED FILE SYSTEM CRASH")):
            inserted = engine.run_batch(full_sync=True)
            assert inserted == 0

