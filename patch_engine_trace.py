with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_scan = '''    def scan_folder(self, folder_path: str, target_date: date) -> List[str]:
        """Deeply scans for .xlsx files matching the target modification date."""
        matched_files = []
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith('.xlsx'):
                    
                    filepath = os.path.join(root, filename)'''

new_scan = '''    def scan_folder(self, folder_path: str, target_date: date, trace_log: list = None) -> List[str]:
        """Deeply scans for .xlsx files matching the target modification date."""
        matched_files = []
        if trace_log is not None: trace_log.append(f"Scanning directory: {folder_path}")
        
        for root, dirs, files in os.walk(folder_path):
            if trace_log is not None: trace_log.append(f"  -> Checked subfolder: {root} ({len(files)} files found)")
            for filename in files:
                if filename.lower().endswith('.xlsx'):
                    
                    filepath = os.path.join(root, filename)'''
c = c.replace(old_scan, new_scan)

old_run = '''    def run_batch(self, target_date: date = None, full_sync: bool = False) -> int:
        """
        Main execution loop.
        - target_date: Explicit date to process.
        - full_sync: If True, scans all files ignoring date. 
        - Default: N-1 (Yesterday)
        """
        if not target_date and not full_sync:
            target_date = date.today() - timedelta(days=1)
            
        logger.info(f"Starting batch run for date: {target_date if target_date else 'ALL'}")
        
        roots = self._get_search_roots()'''

new_run = '''    def run_batch(self, target_date: date = None, full_sync: bool = False, dry_run: bool = False) -> dict:
        """
        Main execution loop.
        - target_date: Explicit date to process.
        - full_sync: If True, scans all files ignoring date. 
        - dry_run: If True, returns a detailed trace log without saving to DB.
        - Default: N-1 (Yesterday)
        """
        trace_log = [] if dry_run else None
        
        if not target_date and not full_sync:
            target_date = date.today() - timedelta(days=1)
            
        logger.info(f"Starting batch run for date: {target_date if target_date else 'ALL'}")
        if dry_run: trace_log.append(f"--- STARTING DRY RUN TRACE FOR DATE: {target_date if target_date else 'ALL'} ---")
        
        roots = self._get_search_roots()'''
c = c.replace(old_run, new_run)

old_mid = '''            if os.path.exists(r):
                files_to_process.extend(self.scan_folder(r, target_date if not full_sync else None))
            else:
                logger.warning(f"Root search path does not exist: {r}")'''

new_mid = '''            if os.path.exists(r):
                if dry_run: trace_log.append(f"\\n[DISCOVERY] Exploring root path: {r}")
                files_to_process.extend(self.scan_folder(r, target_date if not full_sync else None, trace_log))
            else:
                logger.warning(f"Root search path does not exist: {r}")
                if dry_run: trace_log.append(f"[WARNING] Root search path does not exist: {r}")'''
c = c.replace(old_mid, new_mid)

old_db1 = '''        # Fetch existing hashes to prevent duplicates
        conn = get_connection(self.db_path)
        existing_hashes = {row['file_hash'] for row in conn.execute("SELECT file_hash FROM reports").fetchall()}'''

new_db1 = '''        if dry_run: trace_log.append(f"\\n[MAPPING] Found {len(files_to_process)} candidate .xlsx files. Beginning mapping extraction...")
        
        # Fetch existing hashes to prevent duplicates
        conn = get_connection(self.db_path)
        existing_hashes = {row['file_hash'] for row in conn.execute("SELECT file_hash FROM reports").fetchall()}'''
c = c.replace(old_db1, new_db1)

old_loop = '''            try:
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
                    batch_id,
                    parsed['recipe_name'],
                    parsed['report_date'],
                    parsed['report_time'],
                    parsed['serial_raw'],
                    parsed['serial_normalized'],
                    parsed['original_filename'],
                    filepath,
                    file_hash,
                    file_size
                ))
                inserted += 1
            except Exception as e:'''

new_loop = '''            try:
                parsed = parse_filename(filepath)
                if not parsed:
                    failed += 1
                    error_logs.append(f"Unparseable filename: {filepath}")
                    if dry_run: trace_log.append(f"  [FAILED] {os.path.basename(filepath)} -> Regex Parser rejected format.")
                    continue
                
                file_hash = hash_file(filepath)
                if file_hash in existing_hashes:
                    skipped += 1
                    if dry_run: trace_log.append(f"  [SKIPPED] {parsed['original_filename']} -> Hash {file_hash[:8]}... already exists in DB.")
                    continue
                
                file_size = os.path.getsize(filepath)
                insert_values.append((
                    batch_id,
                    parsed['recipe_name'],
                    parsed['report_date'],
                    parsed['report_time'],
                    parsed['serial_raw'],
                    parsed['serial_normalized'],
                    parsed['original_filename'],
                    filepath,
                    file_hash,
                    file_size
                ))
                inserted += 1
                if dry_run: trace_log.append(f"  [MAPPED] {parsed['original_filename']} -> Recipe: {parsed['recipe_name']}, Date: {parsed['report_date']}, Serial: {parsed['serial_raw']}")
            except Exception as e:'''
c = c.replace(old_loop, new_loop)

old_final = '''        if insert_values:
            try:
                conn.execute("BEGIN TRANSACTION")'''

new_final = '''        if dry_run:
            trace_log.append(f"\\n--- DRY RUN COMPLETE ---")
            trace_log.append(f"Total Scanned: {scanned}, Would Insert: {inserted}, Skipped (Dupes): {skipped}, Failed Parse: {failed}")
            conn.close()
            return {"trace": "\\n".join(trace_log)}

        if insert_values:
            try:
                conn.execute("BEGIN TRANSACTION")'''
c = c.replace(old_final, new_final)

old_return_fail = '''        conn.close()
        return 0'''
new_return_fail = '''        conn.close()
        return {"inserted": 0}'''
c = c.replace(old_return_fail, new_return_fail)

old_return_succ = '''        conn.close()
        return inserted'''
new_return_succ = '''        conn.close()
        return {"inserted": inserted}'''
c = c.replace(old_return_succ, new_return_succ)

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
