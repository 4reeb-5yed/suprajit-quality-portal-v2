# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\setup.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('<label class="label"><span class="label-text font-bold text-gray-700">Mail Username</span></label>', 
              '<label class="label"><span class="label-text font-bold text-gray-700">Sender Email Address (Mail Username)</span></label>')

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\setup.html', 'w', encoding='utf-8') as f:
    f.write(c)

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\settings.html', 'r', encoding='utf-8') as f:
    s = f.read()

s = s.replace('<label class="label"><span class="label-text font-bold text-gray-700">Mail Username (Email Address)</span></label>', 
              '<label class="label"><span class="label-text font-bold text-gray-700">Sender Email Address</span></label>')
s = s.replace('<label class="label"><span class="label-text font-bold text-gray-700">Mail Username</span></label>', 
              '<label class="label"><span class="label-text font-bold text-gray-700">Sender Email Address (Mail Username)</span></label>')

with io.open(r'C:\Users\humza\suprajit_v2\app\templates\admin\settings.html', 'w', encoding='utf-8') as f:
    f.write(s)
