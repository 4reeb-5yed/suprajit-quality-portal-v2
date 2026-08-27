with open('app/routes/admin.py', 'r') as f:
    c = f.read()

old_delete = '''@admin_bp.route('/customers/delete', methods=['POST'])
def delete_customer():
    from app.database import DEACTIVATE_CUSTOMER
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    if customer_id:
        g.db.execute(DEACTIVATE_CUSTOMER, (customer_id,))
        g.db.execute("UPDATE users SET is_active = 0 WHERE customer_id = ?", (customer_id,))
        g.db.commit()
        flash(f"Customer '{customer_id}' has been deactivated. Their login access is revoked, but background ingestion will continue.", "success")'''

new_delete = '''@admin_bp.route('/customers/delete', methods=['POST'])
def delete_customer():
    from app.database import DELETE_CUSTOMER
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    if customer_id:
        try:
            g.db.execute(DELETE_CUSTOMER, (customer_id,))
            g.db.commit()
            flash(f"Customer '{customer_id}' has been permanently deleted.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")'''

c = c.replace(old_delete, new_delete)
with open('app/routes/admin.py', 'w') as f:
    f.write(c)
