with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_route = '''@admin_bp.route('/diagnostics')
def diagnostics():
    # Read the last 100 lines of the suprajit.log file
    log_lines = []
    try:
        log_path = 'suprajit.log'
        import os
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                log_lines = lines[-100:]
        else:
            log_lines = ["No log file found. System has not generated any logs yet."]
    except Exception as e:
        log_lines = [f"Error reading log file: {e}"]
        
    # Get last sync info
    last_run = g.db.execute("SELECT * FROM batch_runs ORDER BY start_time DESC LIMIT 1").fetchone()
    
    return __import__('flask').render_template('admin/diagnostics.html', log_lines=log_lines, last_run=last_run)

@admin_bp.route('/trigger_sync', methods=['POST'])'''

c = c.replace("@admin_bp.route('/trigger_sync', methods=['POST'])", new_route)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
