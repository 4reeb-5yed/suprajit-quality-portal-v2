with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Remove the C:\ default
c = c.replace("root_search_path = get_val('root_search_path', 'C:\\\\')", "root_search_path = get_val('root_search_path', '')")

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
