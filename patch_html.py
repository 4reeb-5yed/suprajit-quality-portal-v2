with open('app/templates/admin/customers.html', 'r') as f:
    c = f.read()

old_modal = 'This will hide them from the portal and revoke their login access, but the ingestion engine <strong>will continue</strong> pulling and backing up their folder data in the background.'
new_modal = 'This will permanently delete the customer, their users, all mapped folders, and their historical data. The background engine will stop pulling their data.'

c = c.replace(old_modal, new_modal)
with open('app/templates/admin/customers.html', 'w') as f:
    f.write(c)
