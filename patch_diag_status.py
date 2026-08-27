# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\diagnostics.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("{% if last_run.status == 'success' %}", "{% if last_run.status == 'success' or last_run.status == 'completed' %}")

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\diagnostics.html', 'w', encoding='utf-8') as f:
    f.write(c)
