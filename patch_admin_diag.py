# -*- coding: utf-8 -*-
import io

with io.open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    # Get last sync info
    last_run = g.db.execute("SELECT * FROM batch_runs ORDER BY run_started DESC LIMIT 1").fetchone()
    
    return __import__('flask').render_template('admin/diagnostics.html', log_lines=log_lines, last_run=last_run)'''

replacement = '''    # Get last sync info
    last_run = g.db.execute("SELECT * FROM batch_runs ORDER BY run_started DESC LIMIT 1").fetchone()
    
    # Advanced Diagnostics Engine Stats
    import os
    from flask import current_app
    db_path = current_app.config['DATABASE_PATH']
    db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2) if os.path.exists(db_path) else 0.0
    
    total_reports = g.db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    total_customers = g.db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    
    from app.database import GET_SETTING
    sync_time_row = g.db.execute(GET_SETTING, ('sync_time',)).fetchone()
    sync_time_str = sync_time_row['value'] if sync_time_row else "02:00"
    
    return __import__('flask').render_template('admin/diagnostics.html', 
                                               log_lines=log_lines, 
                                               last_run=last_run,
                                               db_size_mb=db_size_mb,
                                               total_reports=total_reports,
                                               total_customers=total_customers,
                                               sync_time_str=sync_time_str)'''

c = c.replace(target, replacement)

with io.open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
