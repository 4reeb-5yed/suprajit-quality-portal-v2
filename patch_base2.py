with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_link = '''<li><a href="{{ url_for('admin.diagnostics') }}"><i class="fa-solid fa-stethoscope w-5"></i> System Health</a></li>'''
new_link = '''<li><a href="{{ url_for('admin.diagnostics') }}"><i class="fa-solid fa-stethoscope w-5"></i> System Health</a></li>
<li><a href="{{ url_for('admin.repair') }}"><i class="fa-solid fa-wrench w-5"></i> Repair Tools</a></li>'''

c = c.replace(old_link, new_link)

with open('app/templates/base.html', 'w', encoding='utf-8') as f:
    f.write(c)
