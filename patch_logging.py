import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(app):
    log_dir = os.path.join(os.path.dirname(app.config['DATABASE_PATH']), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'suprajit_system.log')
    
    # 5MB per file, keep 3 backups
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(file_formatter)
    
    # Also log to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Set the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Specifically attach to Werkzeug (Flask) so we capture HTTP requests too
    logging.getLogger('werkzeug').addHandler(file_handler)
    
    app.config['LOG_FILE_PATH'] = log_file
