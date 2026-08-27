import logging
from logging.handlers import RotatingFileHandler
from waitress import serve
from app import create_app
from app.config import get_config

import sys
import os

# Ensure the log file goes into the same directory as the executable/cwd
log_file_path = 'suprajit.log'

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
    app = create_app()
    cfg = get_config()
    
    logger.info(f"Starting Waitress production server on {cfg.HOST}:{cfg.PORT}")
    serve(app, host=cfg.HOST, port=cfg.PORT, threads=8)
