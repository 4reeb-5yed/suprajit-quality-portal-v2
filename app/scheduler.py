import threading
import time
from datetime import datetime, timedelta
import logging
import traceback

from app.database import get_connection, GET_SETTING, SET_SETTING
from app.sync_engine import SyncEngine

logger = logging.getLogger(__name__)

def cleanup_zombies(db_path):
    try:
        conn = get_connection(db_path)
        zombie_threshold = (datetime.now() - timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE batch_runs 
            SET status = 'CRASHED_ZOMBIE', 
                error_log = error_log || '\nFATAL: Process died silently. Marked as Zombie by watchdog.' 
            WHERE status = 'running' AND run_started < ?
        """, (zombie_threshold,))
        
        if cursor.rowcount > 0:
            logger.critical(f"WATCHDOG ALERT: {cursor.rowcount} zombie batch(es) detected and killed.")
            
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to run zombie watchdog: {e}")

def run_scheduler(db_path, storage_base):
    logger.info("Internal batch scheduler started. Watchdog armed.")
    
    while True:
        try:
            cleanup_zombies(db_path)
            
            conn = get_connection(db_path)
            row = conn.execute(GET_SETTING, ('sync_time',)).fetchone()
            sync_time = row['value'] if row else '02:00'
            
            row = conn.execute(GET_SETTING, ('last_sync_date',)).fetchone()
            last_sync_date = row['value'] if row else None
            
            now = datetime.now()
            today_str = now.strftime('%Y-%m-%d')
            
            # Security Fix: Instead of exact minute match, use a 5-minute window to avoid missing the trigger
            # if the CPU pauses or the system clock jumps.
            try:
                sync_hour, sync_minute = map(int, sync_time.split(':'))
                sync_dt = now.replace(hour=sync_hour, minute=sync_minute, second=0, microsecond=0)
                
                # Check if now is within a 5-minute window AFTER the sync_time
                time_diff = now - sync_dt
                is_time_to_sync = timedelta(0) <= time_diff <= timedelta(minutes=5)
            except ValueError:
                is_time_to_sync = False
            
            if is_time_to_sync and last_sync_date != today_str:
                logger.info(f"Triggering scheduled batch sync for {sync_time} window...")
                
                conn.execute(SET_SETTING, ('last_sync_date', today_str))
                conn.commit()
                
                engine = SyncEngine(db_path, storage_base)
                has_run_before = conn.execute("SELECT COUNT(*) FROM batch_runs").fetchone()[0] > 0
                
                engine.run_batch(full_sync=not has_run_before)
                logger.info("Scheduled batch sync completed.")
            
            conn.close()
        except Exception as e:
            logger.critical(f"FATAL SYSTEM ERROR IN BACKGROUND SCHEDULER: {e}", exc_info=True)
            
        time.sleep(60)

def start_background_scheduler(app):
    db_path = app.config['DATABASE_PATH']
    storage_base = app.config['STORAGE_FOLDER']
    
    t = threading.Thread(target=run_scheduler, args=(db_path, storage_base), daemon=True)
    t.start()
