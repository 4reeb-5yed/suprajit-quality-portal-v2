# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = 'logger.info(f"Parsed metadata -> Recipe: {parsed[\'recipe_name\']}, Serial: {parsed[\'serial_raw\']}")'
replacement = 'logger.info(f"Parsed metadata -> Recipe: {parsed[\'recipe_name\']}, Date: {parsed[\'report_date\']}, Time: {parsed[\'report_time\']}, Serial: {parsed[\'serial_raw\']}")'

c = c.replace(target, replacement)

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
