"""
REAL CONCURRENCY & TRANSACTION ISOLATION CONFLICT TESTING
Simulates simultaneous threads attempting to execute write-write collisions and read-write contention.
"""

import pytest
pytestmark = pytest.mark.integration


import threading
import tempfile
import os
import time
from app.database import get_connection, ensure_schema

def test_concurrency_sqlite_wal_write_contention():
    """
    Spawns multiple threads contending for concurrent writes on the same SQLite WAL database.
    Verifies that WAL mode + timeout handles lock contention without database corruption or data loss.
    """
    fd, db_path = tempfile.mkstemp()
    conn = get_connection(db_path)
    ensure_schema(conn)
    conn.execute("CREATE TABLE IF NOT EXISTS shared_counter (id INTEGER PRIMARY KEY, count INTEGER)")
    conn.execute("INSERT INTO shared_counter (id, count) VALUES (1, 0)")
    conn.commit()
    conn.close()

    NUM_THREADS = 10
    INCREMENTS_PER_THREAD = 20
    errors = []

    def worker():
        for _ in range(INCREMENTS_PER_THREAD):
            try:
                # Open separate thread connection
                t_conn = get_connection(db_path)
                t_conn.execute("BEGIN IMMEDIATE")
                row = t_conn.execute("SELECT count FROM shared_counter WHERE id = 1").fetchone()
                val = row['count']
                time.sleep(0.001) # Force thread context switch inside transaction
                t_conn.execute("UPDATE shared_counter SET count = ? WHERE id = 1", (val + 1,))
                t_conn.commit()
                t_conn.close()
            except Exception as e:
                errors.append(str(e))

    threads = [threading.Thread(target=worker) for _ in range(NUM_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final_conn = get_connection(db_path)
    final_row = final_conn.execute("SELECT count FROM shared_counter WHERE id = 1").fetchone()
    final_count = final_row['count']
    final_conn.close()

    os.close(fd)
    try:
        os.remove(db_path)
    except OSError:
        pass

    assert len(errors) == 0, f"Encountered concurrency errors: {errors}"
    assert final_count == NUM_THREADS * INCREMENTS_PER_THREAD


def test_concurrency_batch_run_race_condition():
    """
    Simulates multiple processes attempting to start the same scheduled sync batch simultaneously.
    Verifies that only one batch run succeeds and duplicates are prevented.
    """
    fd, db_path = tempfile.mkstemp()
    conn = get_connection(db_path)
    ensure_schema(conn)
    conn.close()

    results = []
    barrier = threading.Barrier(5)

    def start_batch_worker(worker_id):
        barrier.wait() # Synchronize all 5 threads to trigger at the exact same instant
        try:
            w_conn = get_connection(db_path)
            w_conn.execute("BEGIN IMMEDIATE")
            # Check if active batch already running
            active = w_conn.execute("SELECT id FROM batch_runs WHERE status = 'running'").fetchone()
            if active:
                results.append((worker_id, "BLOCKED"))
                w_conn.rollback()
            else:
                w_conn.execute("INSERT INTO batch_runs (target_date, status) VALUES ('2026-06-13', 'running')")
                time.sleep(0.05) # Hold transaction lock open
                w_conn.commit()
                results.append((worker_id, "STARTED"))
            w_conn.close()
        except Exception as e:
            results.append((worker_id, f"ERROR: {e}"))

    threads = [threading.Thread(target=start_batch_worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    started_count = sum(1 for _, res in results if res == "STARTED")
    blocked_count = sum(1 for _, res in results if res == "BLOCKED")

    os.close(fd)
    try:
        os.remove(db_path)
    except OSError:
        pass

    assert started_count == 1, "Exactly one worker should successfully start the batch"
    assert blocked_count == 4, "Other 4 concurrent workers should have been safely blocked"
