# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('return {"inserted": inserted}', 'return inserted')
c = c.replace('return {"inserted": 0, "trace": ["No valid root search path configured. Skipping."]}', 'return 0')

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
