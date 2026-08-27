import io
with io.open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        roots = self._get_search_roots()
        total_inserted = 0'''

replacement = '''        roots = self._get_search_roots()
        if not roots or roots == [''] or roots == ['C:\\\\']:
            self.logger.warning("No valid root search path configured. Skipping ingestion.")
            return {"inserted": 0, "trace": ["No valid root search path configured. Skipping."]}
            
        total_inserted = 0'''

c = c.replace(target, replacement)

with io.open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
