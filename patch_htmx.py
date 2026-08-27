with open('app/templates/portal/search.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Fix Form trigger
old_form = '''<form id="search-form" hx-get="{{ url_for('portal.search_results') }}" hx-target="#results-container" hx-trigger="submit, change delay:200ms" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">'''
new_form = '''<form id="search-form" hx-get="{{ url_for('portal.search_results') }}" hx-target="#results-container" hx-trigger="submit" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">'''
c = c.replace(old_form, new_form)

# Fix Input trigger
old_input = '''<input type="text" name="serial" placeholder="e.g. 0012" class="input input-bordered w-full" hx-get="{{ url_for('portal.search_results') }}" hx-trigger="keyup changed delay:500ms" hx-target="#results-container" hx-include="#search-form">'''
new_input = '''<input type="text" name="serial" placeholder="e.g. 0012" class="input input-bordered w-full">'''
c = c.replace(old_input, new_input)

# Fix Tbody load state
old_tbody = '''<tbody id="results-container" hx-get="{{ url_for('portal.search_results') }}" hx-trigger="load">
                    <tr>
                        <td colspan="5" class="p-8 text-center text-gray-500">
                            <span class="loading loading-spinner text-primary"></span> Loading data...
                        </td>
                    </tr>
                </tbody>'''
new_tbody = '''<tbody id="results-container">
                    <tr>
                        <td colspan="5" class="text-center text-gray-500 py-12">
                            <i class="fa-solid fa-magnifying-glass text-2xl mb-3 block text-gray-300"></i>
                            Please select a recipe, date, or enter a serial number, then click Search.
                        </td>
                    </tr>
                </tbody>'''
c = c.replace(old_tbody, new_tbody)

with open('app/templates/portal/search.html', 'w', encoding='utf-8') as f:
    f.write(c)
