# -*- coding: utf-8 -*-
import io
import re

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Just replace "if dry_run:" with "if False:" globally.
c = c.replace("if dry_run:", "if False:")

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
