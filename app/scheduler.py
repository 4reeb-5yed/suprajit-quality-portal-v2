import threading
import time
from datetime import datetime
import logging

from app.database import get_connection, GET_SETTING, SET_SETTING
from app.sync_engine import SyncEngine

logger = logging.getLogger(__name__)

def run_scheduler(db_path, storage_base):
    """Background thread loop that checks the time every minute and triggers ingestion."""
    logger.info("Internal batch scheduler started.")
    
    while True:
        try:
            conn = get_connection(db_path)
            
            # Get configured time from database (default 02:00)
            row = conn.execute(GET_SETTING, ('sync_time',)).fetchone()
            sync_time = row['value'] if row else '02:00'
            
            # Get last run date to ensure we only run once per day
            row = conn.execute(GET_SETTING, ('last_sync_date',)).fetchone()
            last_sync_date = row['value'] if row else None
            
            now = datetime.now()
            current_time_str = now.strftime('%H:%M')
            today_str = now.strftime('%Y-%m-%d')
            
            if current_time_str == sync_time and last_sync_date != today_str:
                logger.info(f"Triggering scheduled batch sync at {sync_time}...")
                
                # Mark as run immediately to prevent race conditions within the minute
                conn.execute(SET_SETTING, ('last_sync_date', today_str))
                conn.commit()
                
                # Execute the sync engine
                engine = SyncEngine(db_path, storage_base)
                engine.run_batch()
                
                logger.info("Scheduled batch sync completed.")
            
            conn.close()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            
        # Sleep for exactly 60 seconds
        time.sleep(60)

def start_background_scheduler(app):
    """Spawns the scheduler thread securely attached to the Flask app lifecycle."""
    db_path = app.config['DATABASE_PATH']
    storage_base = app.config['STORAGE_FOLDER']
    
    # Daemon=True means this thread will automatically die when Waitress stops
    t = threading.Thread(target=run_scheduler, args=(db_path, storage_base), daemon=True)
    t.start()
