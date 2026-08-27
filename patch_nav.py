with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_link = '''<a href="{{ url_for('admin.settings') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-cogs"></i> Config</a>'''
new_link = '''<a href="{{ url_for('admin.settings') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-cogs"></i> Config</a>
                            <a href="{{ url_for('admin.diagnostics') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-stethoscope"></i> Health</a>
                            <a href="{{ url_for('admin.repair') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-wrench"></i> Repair</a>'''

c = c.replace(old_link, new_link)

with open('app/templates/base.html', 'w', encoding='utf-8') as f:
    f.write(c)
