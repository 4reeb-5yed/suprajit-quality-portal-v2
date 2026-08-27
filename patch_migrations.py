with open('app/database.py', 'r') as f:
    c = f.read()

migration_code = '''

def run_migrations(conn):
    """
    Lightweight, factory-proof schema migration system.
    Relies on SQLite's PRAGMA user_version instead of external tools like Alembic.
    """
    current_version = conn.execute("PRAGMA user_version").fetchone()[0]
    
    # Baseline version initialization
    if current_version == 0:
        with conn:
            conn.execute("PRAGMA user_version = 1")
        current_version = 1

    # ==========================================
    # FUTURE MIGRATIONS GO HERE
    # ==========================================
    # Example for the future:
    # if current_version == 1:
    #     with conn:
    #         conn.execute("ALTER TABLE reports ADD COLUMN shift_number TEXT")
    #         conn.execute("PRAGMA user_version = 2")
    #     current_version = 2
    # ==========================================

def get_connection(db_path: str):
'''

c = c.replace('def get_connection(db_path: str):', migration_code)

# Now call run_migrations at the end of ensure_schema
old_end = '''            );
        """)'''

new_end = '''            );
        """)
    
    # Run auto-upgrades
    run_migrations(conn)'''

c = c.replace(old_end, new_end)

with open('app/database.py', 'w') as f:
    f.write(c)
