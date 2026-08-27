# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        if dry_run:
            trace_log.append(f"\n--- DRY RUN COMPLETE ---")
            trace_log.append(f"Total Scanned: {scanned}, Would Insert: {inserted}, Skipped (Dupes): {skipped}, Failed Parse: {failed}")
            conn.close()
            return {"trace": "\n".join(trace_log)}'''

replacement = '''        if False:
            pass'''

c = c.replace(target, replacement)

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
