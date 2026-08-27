with open('app/templates/admin/settings.html', 'r') as f:
    c = f.read()

c = c.replace('storage_folder', 'root_search_path')
c = c.replace('Global Storage Vault', 'Global Search Root Directories')
c = c.replace('C:\Data\Archived_Reports', 'C:\Data\Reports;Z:\Test Reports')
c = c.replace('All ingested files will be safely copied here', 'The crawler will search these directories recursively for .xlsx files. Separate multiple paths with semicolons (;)')

with open('app/templates/admin/settings.html', 'w') as f:
    f.write(c)
