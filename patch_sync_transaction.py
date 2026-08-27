# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        if insert_values:
            try:
                conn.execute("BEGIN TRANSACTION")
                conn.executemany("""
                    INSERT OR IGNORE INTO reports 
                    (batch_run_id, recipe_name, report_date, report_time, serial_raw, 
                     serial_normalized, original_filename, file_path, file_hash, file_size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_values)
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.critical(f"Bulk insert failed for batch {batch_id}: {e}")
                self._complete_batch(conn, batch_id, scanned, 0, skipped, failed, f"DB Error: {str(e)}", "failed")
                conn.close()
                return 0'''

replacement = '''        if insert_values:
            try:
                with conn:
                    conn.executemany("""
                        INSERT OR IGNORE INTO reports 
                        (batch_run_id, recipe_name, report_date, report_time, serial_raw, 
                         serial_normalized, original_filename, file_path, file_hash, file_size_bytes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, insert_values)
            except Exception as e:
                logger.critical(f"Bulk insert failed for batch {batch_id}: {e}")
                self._complete_batch(conn, batch_id, scanned, 0, skipped, failed, f"DB Error: {str(e)}", "failed")
                conn.close()
                return 0'''

c = c.replace(target, replacement)

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
