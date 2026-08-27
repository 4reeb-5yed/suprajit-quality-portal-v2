with open('app/routes/portal.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('LIMIT 100', '')

with open('app/routes/portal.py', 'w', encoding='utf-8') as f:
    f.write(c)

with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    b = f.read()

old_user = '''<div class="text-sm font-medium bg-blue-800 px-3 py-1.5 rounded flex items-center gap-2 shadow-inner">'''
new_user = '''<div class="text-lg font-bold bg-blue-800 px-4 py-2 rounded flex items-center gap-2 shadow-inner tracking-wide">'''
b = b.replace(old_user, new_user)

with open('app/templates/base.html', 'w', encoding='utf-8') as f:
    f.write(b)
