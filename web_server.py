import logging
from logging.handlers import RotatingFileHandler
from waitress import serve
from app import create_app
from app.config import get_config

import sys
import os

# If frozen (PyInstaller), log next to executable
if getattr(sys, 'frozen', False):
    log_dir = os.path.dirname(sys.executable)
else:
    log_dir = os.path.dirname(os.path.abspath(__file__))
    
log_file_path = os.path.join(log_dir, 'suprajit.log')

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('waitress')

if __name__ == '__main__':
    try:
        app = create_app()
        cfg = get_config()
        
        logger.info(f"Starting Waitress production server on {cfg.HOST}:{cfg.PORT}")
        serve(app, host=cfg.HOST, port=cfg.PORT, threads=8)
    except OSError as e:
        if "10048" in str(e):
            logger.critical(f"FATAL ERROR: Port {cfg.PORT} is already in use by another application. Please close the other application or kill hanging python processes.")
        else:
            logger.critical(f"Fatal OS Error: {e}")
        input("\n[ERROR] Press Enter to exit...")
    except Exception as e:
        logger.critical(f"Fatal Application Error: {e}")
        import traceback
        traceback.print_exc()
        input("\n[ERROR] Press Enter to exit...")
