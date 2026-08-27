with open('app/sync_engine.py', 'r') as f:
    c = f.read()

old_scan = '''    def scan_folder(self, folder_path: str, target_date: date) -> List[str]:
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
                    if file_date == target_date:
                        matched_files.append(filepath)
                except OSError as e:
                    logger.error(f"Error reading file stat for {filepath}: {e}")
                
        return matched_files

    def run_batch(self, target_date: date = None) -> int:
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
            
        roots = self._get_search_roots()'''

new_scan = '''    def scan_folder(self, folder_path: str, target_date: date) -> List[str]:
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
            
        roots = self._get_search_roots()'''

c = c.replace(old_scan, new_scan)

# We also need to fix target_date.isoformat() if target_date is None!
old_process = '''    def process_folder(self, source_path: str, target_date: date) -> int:
        conn = get_connection(self.db_path)
        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO batch_runs (target_date) VALUES (?)", (target_date.isoformat(),))'''
new_process = '''    def process_folder(self, source_path: str, target_date: date) -> int:
        conn = get_connection(self.db_path)
        
        cursor = conn.cursor()
        t_val = target_date.isoformat() if target_date else "ALL_HISTORICAL"
        cursor.execute("INSERT INTO batch_runs (target_date) VALUES (?)", (t_val,))'''
c = c.replace(old_process, new_process)

with open('app/sync_engine.py', 'w') as f:
    f.write(c)

# Now update admin.py trigger_sync
with open('app/routes/admin.py', 'r') as f:
    c2 = f.read()
c2 = c2.replace('engine.run_batch()', 'engine.run_batch(full_sync=True)')
with open('app/routes/admin.py', 'w') as f:
    f.write(c2)
