with open('app/database.py', 'r') as f:
    c = f.read()

import re

old_migrations = '''    # ==========================================
    # FUTURE MIGRATIONS GO HERE
    # ==========================================
    # Example for the future:
    # if current_version == 1:
    #     with conn:
    #         conn.execute("ALTER TABLE reports ADD COLUMN shift_number TEXT")
    #         conn.execute("PRAGMA user_version = 2")
    #     current_version = 2
    # =========================================='''

new_migrations = '''    # ==========================================
    # FUTURE MIGRATIONS GO HERE
    # ==========================================
    if current_version == 1:
        with conn:
            # Add missing files_failed column to batch_runs table
            conn.execute("ALTER TABLE batch_runs ADD COLUMN files_failed INTEGER DEFAULT 0")
            conn.execute("PRAGMA user_version = 2")
        current_version = 2
    # =========================================='''

c = c.replace(old_migrations, new_migrations)

with open('app/database.py', 'w') as f:
    f.write(c)
