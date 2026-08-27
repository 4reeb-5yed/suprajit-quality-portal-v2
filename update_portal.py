import sqlite3
with open('app/routes/portal.py', 'r') as f:
    content = f.read()

old_download = '''@portal_bp.route('/download/<int:report_id>')
@login_required
def download(report_id):
    where, params = customer_scope(current_user)
    row = g.db.execute(f"SELECT * FROM reports WHERE id = ? AND {where}", [report_id] + params).fetchone()
    
    if not row:
        abort(404)
        
    cfg = get_config()
    
    # Check DB for custom storage folder, fallback to config
    db_storage_row = g.db.execute("SELECT value FROM system_settings WHERE key = 'storage_folder'").fetchone()
    base_storage = db_storage_row['value'] if db_storage_row and db_storage_row['value'] else cfg.STORAGE_FOLDER
    
    target_path = os.path.join(base_storage, row['stored_path'])
    
    if not os.path.exists(target_path) or not is_safe_path(base_storage, target_path):
        abort(404)
        
    # Audit log
    g.db.execute("INSERT INTO audit_log (user_id, report_id, action, client_ip) VALUES (?, ?, ?, ?)",
                 (current_user.id, report_id, 'download', request.remote_addr))
    g.db.commit()
    
    return send_file(target_path, as_attachment=True, download_name=row['original_filename'])'''

new_download = '''@portal_bp.route('/download/<int:report_id>')
@login_required
def download(report_id):
    where, params = customer_scope(current_user)
    row = g.db.execute(f"SELECT * FROM reports WHERE id = ? AND {where}", [report_id] + params).fetchone()
    
    if not row:
        abort(404)
        
    target_path = row['file_path']
    
    if not os.path.exists(target_path):
        abort(404)
        
    # Audit log
    g.db.execute("INSERT INTO audit_log (user_id, report_id, action, client_ip) VALUES (?, ?, ?, ?)",
                 (current_user.id, report_id, 'download', request.remote_addr))
    g.db.commit()
    
    return send_file(target_path, as_attachment=True, download_name=row['original_filename'])'''

content = content.replace(old_download, new_download)

# Also update the search query so it uses correct column name for customer dropdown
old_recipe_query = '''    # Fetch distinct recipes for the dropdown
    query = f"SELECT DISTINCT recipe_name FROM reports WHERE {where_clause} ORDER BY recipe_name"
    recipes = g.db.execute(query, params).fetchall()'''

new_recipe_query = '''    # Fetch distinct recipes for the dropdown based on customer auth scope
    if current_user.is_admin:
        query = "SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name"
        recipes = g.db.execute(query).fetchall()
    else:
        query = "SELECT DISTINCT recipe_name FROM customer_recipes WHERE customer_id = ? ORDER BY recipe_name"
        recipes = g.db.execute(query, [current_user.customer_id]).fetchall()'''

content = content.replace(old_recipe_query, new_recipe_query)

with open('app/routes/portal.py', 'w') as f:
    f.write(content)
