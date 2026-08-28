with open('app/routes/portal.py', 'r', encoding='utf-8') as f:
    text = f.read()

orig = '''    # SECURITY PATCH: Actually enforce is_safe_path
    if not is_safe_path(current_app.config['STORAGE_FOLDER'], target_path):
        current_app.logger.error(f"Path Traversal Attempt Blocked: {target_path}")
        abort(403)'''

new = '''    # SECURITY PATCH: Actually enforce is_safe_path
    # Reports can be safely served from the local STORAGE_FOLDER or the designated root_search_path network share
    setting_row = g.db.execute("SELECT value FROM system_settings WHERE key = 'root_search_path'").fetchone()
    root_search_path = setting_row['value'] if setting_row else ''
    
    is_safe = is_safe_path(current_app.config['STORAGE_FOLDER'], target_path)
    if root_search_path and not is_safe:
        is_safe = is_safe_path(root_search_path, target_path)
        
    if not is_safe:
        current_app.logger.error(f"Path Traversal Attempt Blocked: {target_path}")
        abort(403)'''

text = text.replace(orig, new)
with open('app/routes/portal.py', 'w', encoding='utf-8') as f:
    f.write(text)
