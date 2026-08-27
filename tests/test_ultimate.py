import pytest
import os
import tempfile
from datetime import date
from app.parser import parse_filename
from app.sync_engine import SyncEngine
from app.database import get_connection

def test_parser_perfect_filename():
    res = parse_filename("EV_TPS_13-06-2026_22.33.21_12.xlsx")
    assert res['recipe_name'] == "EV_TPS"
    assert res['report_date'] == "2026-06-13"

def test_parser_weird_casing_and_spaces():
    res = parse_filename("ev tps_13-06-2026_22.33.21_0045.XLSX")
    assert res['recipe_name'] == "ev tps"

def test_parser_invalid_garbage():
    res = parse_filename("random_junk_file.txt")
    assert res is None

def test_parser_missing_date():
    res = parse_filename("RECIPE_NO_DATE_22.33.21_12.xlsx")
    assert res is None

def test_regression_sync_engine_real_ingestion(app):
    with app.app_context():
        db_path = app.config['DATABASE_PATH']
        storage = app.config['STORAGE_FOLDER']
        engine = SyncEngine(db_path, storage)
        
        # Force the engine to only look at our temp storage
        engine._get_search_roots = lambda: [storage]
        
        # Create a real, valid file
        test_file = os.path.join(storage, "VALID_RECIPE_13-06-2026_22.33.21_001.xlsx")
        with open(test_file, 'w') as f:
            f.write("dummy content")
            
        # Run REAL full sync (no mocking of process_folder)
        total = engine.run_batch(full_sync=True)
        assert total == 1
        
        # Verify it actually went into the database
        conn = get_connection(db_path)
        count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        conn.close()
        assert count == 1
