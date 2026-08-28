import re

with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will truncate everything from "def process_folder" down to the end of the file, and replace it with a clean, mathematically correct implementation without orphans.
pattern = r"    def process_folder\(self, source_path: str, target_date: date\) -> int:.*"
replacement = """    def process_folder(self, source_path: str, target_date: date) -> int:
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
                filename_only = os.path.basename(filepath)
                logger.info(f"Scanning file: {filename_only}")

                if not ensure_file_safe(filepath):
                    skipped += 1
                    logger.warning(f"File locked or actively copying, skipping for next batch: {filename_only}")
                    continue

                parsed = parse_filename(filepath)
                if not parsed:
                    failed += 1
                    error_logs.append(f"Unparseable filename: {filepath}")
                    logger.warning(f"Failed to parse filename metadata for: {filename_only}")
                    continue
                
                logger.info(f"Parsed metadata -> Recipe: {parsed['recipe_name']}, Date: {parsed['report_date']}, Time: {parsed['report_time']}, Serial: {parsed['serial_raw']}")
                
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
                logger.info(f"Successfully mapped {filename_only} to Recipe '{parsed['recipe_name']}'")
                
            except Exception as e:
                failed += 1
                error_logs.append(f"Error processing {filepath}: {str(e)}")
                logger.error(f"Failed file {filepath}: {e}")

        if insert_values:
            try:
                with conn:
                    conn.executemany(\"\"\"
                        INSERT OR IGNORE INTO reports 
                        (batch_run_id, recipe_name, report_date, report_time, serial_raw, 
                         serial_normalized, original_filename, file_path, file_hash, file_size_bytes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \"\"\", insert_values)
            except Exception as e:
                logger.critical(f"Bulk insert failed for batch {batch_id}: {e}")
                self._complete_batch(conn, batch_id, scanned, 0, skipped, failed, f"DB Error: {str(e)}", "failed")
                conn.close()
                return 0

        status = "completed"
        self._complete_batch(conn, batch_id, scanned, inserted, skipped, failed, "\\n".join(error_logs), status)
        
        conn.close()
        return inserted

    def _complete_batch(self, conn, batch_id, scanned, inserted, skipped, failed, error_log, status):
        conn.execute(\"\"\"
            UPDATE batch_runs 
            SET run_completed = datetime('now'),
                files_scanned = ?, files_inserted = ?, files_skipped = ?, files_failed = ?,
                error_log = ?, status = ?
            WHERE id = ?
        \"\"\", (scanned, inserted, skipped, failed, error_log, status, batch_id))
        conn.commit()

    def execute_dry_run(self, target_date: date = None) -> str:
        roots = self._get_search_roots()
        if not roots or roots == [''] or roots == ['C:\\\\']:
            return "No valid root search path configured. Please configure in Settings."
            
        trace = []
        trace.append(f"Starting DRY RUN across roots: {roots}")
        trace.append(f"Target Date: {target_date if target_date else 'ALL HISTORICAL'}\\n")
        
        conn = get_connection(self.db_path)
        existing_hashes = {row[0] for row in conn.execute("SELECT file_hash FROM reports").fetchall()}
        conn.close()
        
        total_scanned = 0
        total_insert = 0
        total_skip = 0
        total_fail = 0
        
        for root_path in roots:
            trace.append(f"-> Scanning: {root_path}")
            files = self.scan_folder(root_path, target_date)
            total_scanned += len(files)
            
            for fpath in files:
                fname = os.path.basename(fpath)
                parsed = parse_filename(fpath)
                if not parsed:
                    trace.append(f"   [FAIL] Could not parse metadata: {fname}")
                    total_fail += 1
                    continue
                    
                fhash = hash_file(fpath)
                if fhash in existing_hashes:
                    trace.append(f"   [SKIP] Already exists in DB: {fname}")
                    total_skip += 1
                else:
                    trace.append(f"   [INSERT] Valid new file: {fname} (Recipe: {parsed['recipe_name']})")
                    total_insert += 1
                    
        trace.append(f"\\n--- DRY RUN SUMMARY ---")
        trace.append(f"Scanned: {total_scanned} | Would Insert: {total_insert} | Skipped: {total_skip} | Failed Parse: {total_fail}")
        return "\\n".join(trace)
"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
