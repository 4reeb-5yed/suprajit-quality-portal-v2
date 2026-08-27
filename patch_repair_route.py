import os

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_routes = '''
@admin_bp.route('/repair', methods=['GET', 'POST'])
def repair():
    trace_log = None
    success_msg = None
    error_msg = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        db_path = current_app.config['DATABASE_PATH']
        storage_base = current_app.config['STORAGE_FOLDER']
        from app.sync_engine import SyncEngine
        
        try:
            if action == 'dry_run':
                engine = SyncEngine(db_path, storage_base)
                # Parse date if provided
                from datetime import datetime
                target = request.form.get('target_date')
                dt = datetime.strptime(target, '%Y-%m-%d').date() if target else None
                
                # Execute dry run
                result = engine.run_batch(target_date=dt, full_sync=not bool(dt), dry_run=True)
                trace_log = result.get('trace', 'No trace generated.')
                
            elif action == 'purge_date':
                target = request.form.get('target_date')
                if not target:
                    error_msg = "Please provide a date to purge."
                else:
                    count = g.db.execute("SELECT COUNT(*) FROM reports WHERE report_date = ?", (target,)).fetchone()[0]
                    g.db.execute("DELETE FROM reports WHERE report_date = ?", (target,))
                    g.db.commit()
                    success_msg = f"Successfully purged {count} records for {target}."
                    
            elif action == 'force_sync':
                target = request.form.get('target_date')
                if not target:
                    error_msg = "Please provide a date to force sync."
                else:
                    from datetime import datetime
                    dt = datetime.strptime(target, '%Y-%m-%d').date()
                    engine = SyncEngine(db_path, storage_base)
                    
                    # Run in background to prevent hanging UI
                    import threading
                    def run_force(dt_val):
                        try:
                            engine.run_batch(target_date=dt_val)
                        except Exception as e:
                            print(f"Force sync error: {e}")
                            
                    t = threading.Thread(target=run_force, args=(dt,))
                    t.start()
                    success_msg = f"Force Sync started in the background for {target}. Check Diagnostics in 30 seconds."
                    
        except Exception as e:
            error_msg = str(e)
            
    return __import__('flask').render_template('admin/repair.html', 
                             trace_log=trace_log, 
                             success_msg=success_msg, 
                             error_msg=error_msg)

@admin_bp.route('/trigger_sync', methods=['POST'])'''

c = c.replace("@admin_bp.route('/trigger_sync', methods=['POST'])", new_routes)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
