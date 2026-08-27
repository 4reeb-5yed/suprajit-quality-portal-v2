with open('app/routes/portal.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_query = '''    if serial:
        where_clause += " AND (serial_raw LIKE ? OR serial_normalized LIKE ?)"
        params.extend([f"%{serial}%", f"%{serial}%"])

    query = f"""'''

new_query = '''    if serial:
        where_clause += " AND (serial_raw LIKE ? OR serial_normalized LIKE ?)"
        params.extend([f"%{serial}%", f"%{serial}%"])

    # If all fields are empty, do not show any data by default
    if not recipe and not date_val and not serial:
        from flask import render_template_string
        return render_template_string('<tr><td colspan="5" class="text-center text-gray-500 py-12"><i class="fa-solid fa-magnifying-glass text-2xl mb-3 block text-gray-300"></i>Please select a recipe, date, or enter a serial number to search for reports.</td></tr>')

    query = f"""'''

c = c.replace(old_query, new_query)
with open('app/routes/portal.py', 'w', encoding='utf-8') as f:
    f.write(c)
