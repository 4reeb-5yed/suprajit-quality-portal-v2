import logging
from waitress import serve
from app import create_app
from app.config import get_config

import sys
import os

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
