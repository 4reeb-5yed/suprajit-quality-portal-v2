# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\web_server.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('waitress')'''

replacement = '''import sys
import os

# Ensure the log file goes into the same directory as the executable/cwd
log_file_path = 'suprajit.log'

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('waitress')'''

c = c.replace(target, replacement)

with io.open(r'C:\Users\humza\suprajit_v2\web_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
