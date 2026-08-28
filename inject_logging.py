with open('app/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_block = """from flask import Flask, g
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

import os
import sqlite3"""

new_import_block = """from flask import Flask, g
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

import os
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(app):
    # Setup Enterprise Log Rotation inside the data directory
    log_dir = os.path.join(os.path.dirname(app.config['DATABASE_PATH']), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'suprajit_system.log')
    
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to prevent duplicates during testing
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    app.config['LOG_FILE_PATH'] = log_file
"""

content = content.replace(import_block, new_import_block)

init_block = "app.config.from_object(cfg)"
new_init_block = "app.config.from_object(cfg)\n    \n    setup_logging(app)"

content = content.replace(init_block, new_init_block)

with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)
