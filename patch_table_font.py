with open('app/templates/partials/results_table.html', 'r', encoding='utf-8') as f:
    r = f.read()

old_tbody = '<tbody>'
new_tbody = '<tbody class="text-sm">' # Make report font smaller
r = r.replace(old_tbody, new_tbody)

with open('app/templates/partials/results_table.html', 'w', encoding='utf-8') as f:
    f.write(r)
