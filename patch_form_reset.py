with open('app/templates/portal/search.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_form = '''<form id="search-form" hx-get="{{ url_for('portal.search_results') }}" hx-target="#results-container" hx-trigger="submit" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">'''
new_form = '''<form id="search-form" hx-get="{{ url_for('portal.search_results') }}" hx-target="#results-container" hx-trigger="submit" hx-on::after-request="this.reset()" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">'''
c = c.replace(old_form, new_form)

with open('app/templates/portal/search.html', 'w', encoding='utf-8') as f:
    f.write(c)
