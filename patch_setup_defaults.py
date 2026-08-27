# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\setup.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('name="mail_server" required class="input input-sm input-bordered w-full" placeholder="e.g. smtp.gmail.com"', 
              'name="mail_server" required class="input input-sm input-bordered w-full" value="smtp.gmail.com"')

c = c.replace('name="mail_port" required class="input input-sm input-bordered w-full" placeholder="e.g. 587"', 
              'name="mail_port" required class="input input-sm input-bordered w-full" value="587"')

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\setup.html', 'w', encoding='utf-8') as f:
    f.write(c)
