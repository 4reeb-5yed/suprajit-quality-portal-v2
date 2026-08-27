# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\__init__.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Change default admin username to bootstrap_admin
c = c.replace("VALUES ('admin', ?", "VALUES ('bootstrap_admin', ?")

with io.open(r'C:\Users\humza\suprajit_v2\app\__init__.py', 'w', encoding='utf-8') as f:
    f.write(c)
