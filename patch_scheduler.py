import io
with io.open('app/scheduler.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''                # Execute the sync engine
                engine = SyncEngine(db_path, storage_base)
                engine.run_batch()'''

replacement = '''                # Execute the sync engine
                engine = SyncEngine(db_path, storage_base)
                
                # If this is the absolute first time the engine has ever run, do a full sync.
                # Otherwise, do the standard N-1 day incremental sync.
                has_run_before = conn.execute("SELECT COUNT(*) FROM batch_runs").fetchone()[0] > 0
                is_first_run = not has_run_before
                
                engine.run_batch(full_sync=is_first_run)'''

c = c.replace(target, replacement)

with io.open('app/scheduler.py', 'w', encoding='utf-8') as f:
    f.write(c)
