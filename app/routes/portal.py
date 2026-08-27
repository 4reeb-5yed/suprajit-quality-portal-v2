from flask import Blueprint, render_template, request, g, send_file, abort
from flask_login import login_required, current_user
import os

from app.helpers import customer_scope, is_safe_path
from app.config import get_config

portal_bp = Blueprint('portal', __name__)

@portal_bp.route('/')
@login_required
def index():
    return __import__('flask').redirect(__import__('flask').url_for('portal.search'))


@portal_bp.route('/search')
@login_required
def search():
    where_clause, params = customer_scope(current_user)
    # Fetch distinct recipes for the dropdown based on customer auth scope
    if current_user.is_admin:
        query = "SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name"
        recipes = g.db.execute(query).fetchall()
    else:
        query = "SELECT DISTINCT recipe_name FROM customer_recipes WHERE customer_id = ? ORDER BY recipe_name"
        recipes = g.db.execute(query, [current_user.customer_id]).fetchall()
    return render_template('portal/search.html', recipes=recipes)

@portal_bp.route('/search/results')
@login_required
def search_results():
    recipe = request.args.get('recipe', '').strip()
    date_val = request.args.get('date', '').strip()
    serial = request.args.get('serial', '').strip()
    
    where_clause, params = customer_scope(current_user)
    
    if recipe:
        where_clause += " AND recipe_name = ?"
        params.append(recipe)
        
    if date_val:
        where_clause += " AND report_date = ?"
        params.append(date_val)
        
    if serial:
        where_clause += " AND (serial_raw LIKE ? OR serial_normalized LIKE ?)"
        params.extend([f"%{serial}%", f"%{serial}%"])

    # If all fields are empty, do not show any data by default
    if not recipe and not date_val and not serial:
        from flask import render_template_string
        return render_template_string('<tr><td colspan="5" class="text-center text-gray-500 py-12"><i class="fa-solid fa-magnifying-glass text-2xl mb-3 block text-gray-300"></i>Please select a recipe, date, or enter a serial number to search for reports.</td></tr>')

    query = f"""
        SELECT * FROM reports 
        WHERE {where_clause}
        ORDER BY report_date DESC, report_time DESC
        
    """
        
    reports = g.db.execute(query, params).fetchall()
    return render_template('partials/results_table.html', reports=reports)

@portal_bp.route('/download/<int:report_id>')
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
    
    return send_file(target_path, as_attachment=True, download_name=row['original_filename'])
