with open('app/sync_engine.py', 'r') as f:
    c = f.read()

import re

# Add the security function at the top
sec_function = '''import time
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

'''

c = c.replace('from typing import List', sec_function)

# Now inject it into the process loop
old_loop = '''            for filepath in files_to_process:
                try:
                    parsed = parse_filename(filepath)
                    if not parsed:
                        failed += 1
                        error_logs.append(f"Unparseable filename: {filepath}")
                        continue
                    
                    file_hash = hash_file(filepath)'''

new_loop = '''            for filepath in files_to_process:
                try:
                    # V1 SECURITY PORT: Enforce file locks and race condition checks
                    if not ensure_file_safe(filepath):
                        failed += 1
                        error_logs.append(f"File locked or corrupted (Race Condition): {filepath}")
                        continue

                    parsed = parse_filename(filepath)
                    if not parsed:
                        failed += 1
                        error_logs.append(f"Unparseable filename: {filepath}")
                        continue
                    
                    file_hash = hash_file(filepath)'''

c = c.replace(old_loop, new_loop)

with open('app/sync_engine.py', 'w') as f:
    f.write(c)
