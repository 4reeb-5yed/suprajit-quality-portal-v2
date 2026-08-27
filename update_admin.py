import sqlite3
with open('app/routes/admin.py', 'r') as f:
    content = f.read()

# Replace folders with recipes
old_folder_routes = '''@admin_bp.route('/customers/add_folder', methods=['POST'])
def add_folder():
    from app.database import INSERT_SOURCE_FOLDER
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    folder_path = request.form.get('folder_path', '').strip().strip('"').strip("'")
    recipe_name = request.form.get('recipe_name', '').strip()
    
    if not folder_path or not recipe_name:
        flash("Folder path and Recipe prefix are required.", "error")
    else:
        try:
            g.db.execute(INSERT_SOURCE_FOLDER, (customer_id, folder_path, recipe_name))
            g.db.commit()
            flash(f"Folder mapping added for {customer_id}.", "success")
        except Exception as e:
            flash(f"Error mapping folder: {e}", "error")
            
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/toggle_folder', methods=['POST'])
def toggle_folder():
    from app.database import TOGGLE_SOURCE_FOLDER
    from flask import request, flash
    
    folder_id = request.form.get('folder_id')
    new_state = int(request.form.get('is_active', 1))
    
    if folder_id:
        g.db.execute(TOGGLE_SOURCE_FOLDER, (new_state, folder_id))
        g.db.commit()
        if new_state == 1:
            flash("Recipe ingestion RESUMED.", "success")
        else:
            flash("Recipe ingestion PAUSED.", "warning")
            
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/edit_folder', methods=['POST'])
def edit_folder():
    from app.database import UPDATE_SOURCE_FOLDER
    from flask import request, flash
    
    folder_id = request.form.get('folder_id')
    folder_path = request.form.get('folder_path', '').strip().strip('"').strip("'")
    recipe_name = request.form.get('recipe_name', '').strip()
    
    if folder_id and folder_path and recipe_name:
        try:
            g.db.execute(UPDATE_SOURCE_FOLDER, (folder_path, recipe_name, folder_id))
            g.db.commit()
            flash("Folder mapping updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating mapping: {e}", "error")
    else:
        flash("Folder path and recipe name are required.", "error")
        
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/delete_folder', methods=['POST'])
def delete_folder():
    from app.database import DELETE_SOURCE_FOLDER
    from flask import request, flash
    
    folder_id = request.form.get('folder_id')
    if folder_id:
        g.db.execute(DELETE_SOURCE_FOLDER, (folder_id,))
        g.db.commit()
        flash("Folder mapping removed successfully.", "success")
        
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))'''

new_recipe_routes = '''@admin_bp.route('/customers/add_recipe', methods=['POST'])
def add_recipe():
    from app.database import INSERT_CUSTOMER_RECIPE
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    recipe_name = request.form.get('recipe_name', '').strip()
    
    if not recipe_name:
        flash("Recipe prefix is required.", "error")
    else:
        try:
            g.db.execute(INSERT_CUSTOMER_RECIPE, (customer_id, recipe_name))
            g.db.commit()
            flash(f"Recipe access granted.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")
            
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))

@admin_bp.route('/customers/delete_recipe', methods=['POST'])
def delete_recipe():
    from app.database import DELETE_CUSTOMER_RECIPE
    from flask import request, flash
    
    customer_id = request.form.get('customer_id')
    recipe_name = request.form.get('recipe_name')
    if customer_id and recipe_name:
        g.db.execute(DELETE_CUSTOMER_RECIPE, (customer_id, recipe_name))
        g.db.commit()
        flash("Recipe access removed successfully.", "success")
        
    return __import__('flask').redirect(__import__('flask').url_for('admin.customers'))'''

content = content.replace(old_folder_routes, new_recipe_routes)

# Also update the dashboard view logic to fetch customer_recipes instead of source_folders
old_fetch = '''    # Fetch all folders and group by customer_id
    folders_raw = g.db.execute("SELECT * FROM source_folders").fetchall()
    customer_folders = {}
    for f in folders_raw:
        cid = f['customer_id']
        if cid not in customer_folders:
            customer_folders[cid] = []
        customer_folders[cid].append(f)'''

new_fetch = '''    # Fetch all recipes and group by customer_id
    recipes_raw = g.db.execute("SELECT * FROM customer_recipes").fetchall()
    customer_recipes = {}
    for r in recipes_raw:
        cid = r['customer_id']
        if cid not in customer_recipes:
            customer_recipes[cid] = []
        customer_recipes[cid].append(r)'''

content = content.replace(old_fetch, new_fetch)
content = content.replace('customer_folders=customer_folders,', 'customer_recipes=customer_recipes,')

# Now for settings: we need root_search_path
old_settings = '''@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    from app.database import SET_SETTING, GET_SETTING
    from flask import request, flash, current_app
    
    if request.method == 'POST':
        sync_time = request.form.get('sync_time', '02:00')
        storage_folder = request.form.get('storage_folder', '').strip()
        
        g.db.execute(SET_SETTING, ('sync_time', sync_time))
        g.db.execute(SET_SETTING, ('storage_folder', storage_folder))
        g.db.commit()
        
        flash("Settings updated successfully.", "success")
        
    # Get current settings
    sync_row = g.db.execute(GET_SETTING, ('sync_time',)).fetchone()
    sync_time = sync_row['value'] if sync_row else '02:00'
    
    storage_row = g.db.execute(GET_SETTING, ('storage_folder',)).fetchone()
    storage_folder = storage_row['value'] if storage_row and storage_row['value'] else current_app.config['STORAGE_FOLDER']
    
    return render_template('admin/settings.html', sync_time=sync_time, storage_folder=storage_folder)'''

new_settings = '''@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    from app.database import SET_SETTING, GET_SETTING
    from flask import request, flash, current_app
    
    if request.method == 'POST':
        sync_time = request.form.get('sync_time', '02:00')
        root_search_path = request.form.get('root_search_path', '').strip()
        
        g.db.execute(SET_SETTING, ('sync_time', sync_time))
        g.db.execute(SET_SETTING, ('root_search_path', root_search_path))
        g.db.commit()
        
        flash("Settings updated successfully.", "success")
        
    # Get current settings
    sync_row = g.db.execute(GET_SETTING, ('sync_time',)).fetchone()
    sync_time = sync_row['value'] if sync_row else '02:00'
    
    root_row = g.db.execute(GET_SETTING, ('root_search_path',)).fetchone()
    root_search_path = root_row['value'] if root_row and root_row['value'] else 'C:\\'
    
    return render_template('admin/settings.html', sync_time=sync_time, root_search_path=root_search_path)'''

content = content.replace(old_settings, new_settings)

with open('app/routes/admin.py', 'w') as f:
    f.write(content)
