import os
import logging
from datetime import datetime, date, timedelta
import time
from typing import List

def ensure_file_safe(filepath: str) -> bool:
    """
    V1 Security Port: Bulletproof check for race conditions, file locks, and active network copies.
    """
    try:
        # 1. Windows File Lock Check
        with open(filepath, 'rb') as f:
            f.read(1)
            
        # 2. Ghost File Check
        size1 = os.path.getsize(filepath)
        if size1 == 0:
            return False
            
        # 3. Active Network Copy / Race Condition Check
        # Only penalize performance with a sleep if the file was modified in the last 60 seconds
        if time.time() - os.path.getmtime(filepath) < 60:
            time.sleep(0.5)
            if size1 != os.path.getsize(filepath):
                return False
                
        return True
    except (IOError, PermissionError, FileNotFoundError):
        # File is currently locked by another process (e.g. Excel or network driver)
        return False



from app.database import get_connection
from app.parser import parse_filename
from app.helpers import hash_file

logger = logging.getLogger(__name__)

class SyncEngine:
    def __init__(self, db_path: str, default_storage_base: str):
        self.db_path = db_path
        
    def _get_search_roots(self) -> List[str]:
        try:
            conn = get_connection(self.db_path)
            row = conn.execute("SELECT value FROM system_settings WHERE key = 'root_search_path'").fetchone()
            conn.close()
            if row and row['value']:
                return [p.strip() for p in row['value'].split(';') if p.strip()]
        except Exception as e:
            logger.error(f"Error reading root_search_path from DB: {e}")
        return []

    def scan_folder(self, folder_path: str, target_date: date) -> List[str]:
        matched_files = []
        if not os.path.exists(folder_path):
            logger.warning(f"Source folder not found: {folder_path}")
            return matched_files

        for root, _, files in os.walk(folder_path):
            for filename in files:
                if not filename.lower().endswith('.xlsx'):
                    continue
                    
                filepath = os.path.join(root, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    file_date = datetime.fromtimestamp(mtime).date()
                    if target_date is None or file_date == target_date:
                        matched_files.append(filepath)
                except OSError as e:
                    logger.error(f"Error reading file stat for {filepath}: {e}")
                
        return matched_files

    def run_batch(self, target_date: date = None, full_sync: bool = False) -> int:
        if not full_sync and target_date is None:
            target_date = date.today() - timedelta(days=1)
        elif full_sync:
            target_date = None
            
        roots = self._get_search_roots()
        total_inserted = 0
        
        for root_path in roots:
            inserted = self.process_folder(root_path, target_date)
            total_inserted += inserted
            
        return total_inserted

    def process_folder(self, source_path: str, target_date: date) -> int:
        conn = get_connection(self.db_path)
        
        cursor = conn.cursor()
        t_val = target_date.isoformat() if target_date else "ALL_HISTORICAL"
        cursor.execute("INSERT INTO batch_runs (target_date) VALUES (?)", (t_val,))
        batch_id = cursor.lastrowid
        conn.commit()

        files_to_process = self.scan_folder(source_path, target_date)
        
        scanned = len(files_to_process)
        inserted = 0
        skipped = 0
        failed = 0
        error_logs = []

        if not files_to_process:
            self._complete_batch(conn, batch_id, scanned, inserted, skipped, failed, "No files found", "completed")
            conn.close()
            return 0

        insert_values = []
        existing_hashes = {row[0] for row in conn.execute("SELECT file_hash FROM reports").fetchall()}
        
        for filepath in files_to_process:
            try:
                parsed = parse_filename(filepath)
                if not parsed:
                    failed += 1
                    error_logs.append(f"Unparseable filename: {filepath}")
                    continue
                
                file_hash = hash_file(filepath)
                if file_hash in existing_hashes:
                    skipped += 1
                    continue
                    
                file_size = os.path.getsize(filepath)
                
                insert_values.append((
                    batch_id, parsed['recipe_name'], parsed['report_date'],
                    parsed['report_time'], parsed['serial_raw'], parsed['serial_normalized'],
                    parsed['original_filename'], filepath, file_hash, file_size
                ))
                inserted += 1
                
            except Exception as e:
                failed += 1
                error_logs.append(f"Error processing {filepath}: {str(e)}")
                logger.error(f"Failed file {filepath}: {e}")

        if insert_values:
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
                return 0

        status = "completed" if failed == 0 else "completed_with_errors"
        self._complete_batch(conn, batch_id, scanned, inserted, skipped, failed, "\n".join(error_logs), status)
        
        conn.close()
        return inserted

    def _complete_batch(self, conn, batch_id, scanned, inserted, skipped, failed, error_log, status):
        conn.execute("""
            UPDATE batch_runs 
            SET run_completed = datetime('now'),
                files_scanned = ?, files_inserted = ?, files_skipped = ?, files_failed = ?,
                error_log = ?, status = ?
            WHERE id = ?
        """, (scanned, inserted, skipped, failed, error_log, status, batch_id))
        conn.commit()
