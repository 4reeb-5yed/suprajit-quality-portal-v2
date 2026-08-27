with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_logic = '''        # Send telemetry on success
        if files_processed > 0 or files_failed > 0:
            try:
                from app.mail import send_heartbeat_email
                send_heartbeat_email(files_processed, files_failed, "success", "")
            except:
                pass'''

new_logic = '''        # Send telemetry on success
        if files_processed > 0 or files_failed > 0:
            try:
                from app.mail import send_heartbeat_email
                
                # Fetch frequency setting
                freq_row = conn.execute("SELECT value FROM system_settings WHERE key = 'telemetry_frequency'").fetchone()
                freq = freq_row[0] if freq_row else 'daily'
                
                send_it = False
                import datetime
                now = datetime.datetime.now()
                
                if files_failed > 0:
                    send_it = True # Always send if there are partial failures
                elif freq == 'daily':
                    send_it = True
                elif freq == 'weekly' and now.weekday() == 0:
                    send_it = True # Monday
                elif freq == 'monthly' and now.day == 1:
                    send_it = True # 1st of month
                
                if send_it:
                    send_heartbeat_email(files_processed, files_failed, "success", "")
            except Exception as e:
                app.logger.error(f"Failed to process success telemetry: {e}")'''

c = c.replace(old_logic, new_logic)

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
