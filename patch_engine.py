with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_end = '''    except Exception as e:
        import traceback
        err = traceback.format_exc()
        app.logger.error(f"Batch failed: {err}")
        conn.execute("UPDATE batch_runs SET status='failed', end_time=CURRENT_TIMESTAMP, error_message=? WHERE id=?", (str(e), run_id))
        conn.commit()
    finally:
        conn.close()'''

new_end = '''    except Exception as e:
        import traceback
        err = traceback.format_exc()
        app.logger.error(f"Batch failed: {err}")
        conn.execute("UPDATE batch_runs SET status='failed', end_time=CURRENT_TIMESTAMP, error_message=? WHERE id=?", (str(e), run_id))
        conn.commit()
        
        # Send telemetry on failure
        try:
            from app.mail import send_heartbeat_email
            send_heartbeat_email(files_processed, files_failed, "failed", str(e))
        except:
            pass
            
    finally:
        conn.close()
        
        # Send telemetry on success
        if files_processed > 0 or files_failed > 0:
            try:
                from app.mail import send_heartbeat_email
                send_heartbeat_email(files_processed, files_failed, "success", "")
            except:
                pass'''

c = c.replace(old_end, new_end)

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
