import os
import time

from flask import Blueprint, abort, current_app, g, render_template, request, send_file
from flask_login import current_user, login_required

from app.helpers import customer_scope, is_safe_path, locate_report_file

portal_bp = Blueprint("portal", __name__)


@portal_bp.route("/")
@login_required
def index():
    return __import__("flask").redirect(__import__("flask").url_for("portal.search"))


@portal_bp.route("/search")
@login_required
def search():
    where_clause, params = customer_scope(current_user)
    if current_user.is_admin:
        query = "SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name"
        recipes = g.db.execute(query).fetchall()
    elif getattr(current_user, "access_mode", "ALL") == "CUSTOM":
        query = "SELECT DISTINCT recipe_name FROM user_recipes WHERE user_id = ? ORDER BY recipe_name"
        recipes = g.db.execute(query, [int(current_user.id)]).fetchall()
    else:
        query = "SELECT DISTINCT recipe_name FROM customer_recipes WHERE customer_id = ? ORDER BY recipe_name"
        recipes = g.db.execute(query, [current_user.customer_id]).fetchall()
    return render_template("portal/search.html", recipes=recipes)


@portal_bp.route("/search/results")
@login_required
def search_results():
    start_time = time.time()

    recipe = request.args.get("recipe", "").strip()
    date_val = request.args.get("date", "").strip()
    serial = request.args.get("serial", "").strip()

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

    if not recipe and not date_val and not serial:
        from flask import render_template_string

        return render_template_string(
            '<tr><td colspan="5" class="text-center text-gray-500 py-12"><i class="fa-solid fa-magnifying-glass text-2xl mb-3 block text-gray-300"></i>Please select a recipe, date, or enter a serial number to search for reports.</td></tr>'
        )

    query = f"""
        SELECT * FROM reports 
        WHERE {where_clause}
        ORDER BY report_date DESC, report_time DESC
        
    """

    reports = g.db.execute(query, params).fetchall()
    latency_ms = (time.time() - start_time) * 1000
    try:
        g.db.execute("INSERT INTO search_metrics (latency_ms) VALUES (?)", (latency_ms,))
        g.db.commit()
    except Exception as e:
        print("Metric error:", e)
    return render_template("partials/results_table.html", reports=reports)


@portal_bp.route("/download/<int:report_id>")
@login_required
def download_report(report_id):
    where, params = customer_scope(current_user)
    row = g.db.execute(f"SELECT * FROM reports WHERE id = ? AND {where}", [report_id] + params).fetchone()

    if not row:
        abort(404)

    target_path = row["file_path"]
    expected_hash = row["file_hash"] if "file_hash" in row.keys() else None

    # Collect search root directories
    search_roots = [current_app.config["STORAGE_FOLDER"]]
    setting_row = g.db.execute("SELECT value FROM system_settings WHERE key = 'root_search_path'").fetchone()
    if setting_row and setting_row["value"]:
        search_roots.extend([r.strip() for r in setting_row["value"].split(";") if r.strip()])
    folder_mappings = g.db.execute("SELECT folder_path FROM folder_mappings").fetchall()
    for fm in folder_mappings:
        if fm["folder_path"]:
            search_roots.append(fm["folder_path"].strip())

    # Security check: if direct path exists, verify is_safe_path
    if os.path.exists(target_path):
        is_safe = any(is_safe_path(root, target_path) for root in search_roots)
        if not is_safe:
            current_app.logger.error(f"Path Traversal Attempt Blocked: {target_path}")
            abort(403)
    else:
        # If target_path is not within authorized search roots, block as traversal
        is_safe = any(is_safe_path(root, target_path) for root in search_roots)
        if not is_safe:
            current_app.logger.error(f"Path Traversal Attempt Blocked: {target_path}")
            abort(403)

        # Resolve active file location (supports moved/relocated files across watched roots)
        resolved_path = locate_report_file(target_path, expected_hash, search_roots, row["original_filename"])
        if not resolved_path:
            abort(404)

        if resolved_path != target_path:
            try:
                g.db.execute("UPDATE reports SET file_path = ? WHERE id = ?", (resolved_path, report_id))
                g.db.commit()
                current_app.logger.info(f"Relocated file updated in DB: {row['original_filename']} -> {resolved_path}")
            except Exception as e:
                current_app.logger.warning(f"Could not update relocated path in DB: {e}")
            target_path = resolved_path

    if not os.path.exists(target_path):
        abort(404)

    # Standard Audit Log
    g.db.execute(
        "INSERT INTO audit_log (user_id, report_id, action, client_ip) VALUES (?, ?, ?, ?)",
        (current_user.id, report_id, "download", request.remote_addr),
    )
    g.db.commit()

    return send_file(target_path, as_attachment=True, download_name=row["original_filename"])


@portal_bp.route("/view-raw/<int:report_id>")
@login_required
def raw_report(report_id):
    """Streams the raw binary file for in-browser client-side Excel rendering."""
    where, params = customer_scope(current_user)
    row = g.db.execute(f"SELECT * FROM reports WHERE id = ? AND {where}", [report_id] + params).fetchone()

    if not row:
        abort(404)

    target_path = row["file_path"]
    expected_hash = row["file_hash"] if "file_hash" in row.keys() else None

    # Collect search root directories
    search_roots = [current_app.config["STORAGE_FOLDER"]]
    setting_row = g.db.execute("SELECT value FROM system_settings WHERE key = 'root_search_path'").fetchone()
    if setting_row and setting_row["value"]:
        search_roots.extend([r.strip() for r in setting_row["value"].split(";") if r.strip()])
    folder_mappings = g.db.execute("SELECT folder_path FROM folder_mappings").fetchall()
    for fm in folder_mappings:
        if fm["folder_path"]:
            search_roots.append(fm["folder_path"].strip())

    # Security check: if direct path exists, verify is_safe_path
    if os.path.exists(target_path):
        is_safe = any(is_safe_path(root, target_path) for root in search_roots)
        if not is_safe:
            abort(404)
    else:
        # If target_path is not within authorized search roots, block
        is_safe = any(is_safe_path(root, target_path) for root in search_roots)
        if not is_safe:
            abort(404)

        # Resolve active file location (supports moved/relocated files across watched roots)
        resolved_path = locate_report_file(target_path, expected_hash, search_roots, row["original_filename"])
        if not resolved_path:
            abort(404)

        if resolved_path != target_path:
            try:
                g.db.execute("UPDATE reports SET file_path = ? WHERE id = ?", (resolved_path, report_id))
                g.db.commit()
                current_app.logger.info(f"Relocated file updated in DB: {row['original_filename']} -> {resolved_path}")
            except Exception as e:
                current_app.logger.warning(f"Could not update relocated path in DB: {e}")
            target_path = resolved_path

    if not os.path.exists(target_path):
        abort(404)

    g.db.execute(
        "INSERT INTO audit_log (user_id, report_id, action, client_ip) VALUES (?, ?, ?, ?)",
        (current_user.id, report_id, "view_online", request.remote_addr),
    )
    g.db.commit()

    return send_file(
        target_path, as_attachment=False, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@portal_bp.route("/onlyoffice-viewer/<int:report_id>")
@login_required
def onlyoffice_viewer(report_id):
    """Serves the standalone ONLYOFFICE WebAssembly spreadsheet viewer page."""
    where, params = customer_scope(current_user)
    row = g.db.execute(f"SELECT * FROM reports WHERE id = ? AND {where}", [report_id] + params).fetchone()
    if not row:
        abort(404)
    return render_template("portal/onlyoffice_viewer.html", report_id=report_id, filename=row["original_filename"])


@portal_bp.route("/preview-pdf/<int:report_id>")
@login_required
def preview_pdf(report_id):
    """Generates and serves a pixel-perfect, 100% authentic PDF render of the Excel report using LibreOffice."""
    import hashlib
    import subprocess

    where, params = customer_scope(current_user)
    row = g.db.execute(f"SELECT * FROM reports WHERE id = ? AND {where}", [report_id] + params).fetchone()
    if not row:
        abort(404)

    target_path = row["file_path"]
    if not os.path.exists(target_path):
        abort(404)

    # Cache PDF by report ID and file modification time to prevent duplicate rendering
    cache_dir = os.path.join(current_app.config["DATA_FOLDER"], "pdf_cache")
    os.makedirs(cache_dir, exist_ok=True)
    mtime = os.path.getmtime(target_path)
    cache_key = hashlib.sha256(f"{report_id}_{mtime}".encode(), usedforsecurity=False).hexdigest()
    cached_pdf = os.path.join(cache_dir, f"{cache_key}.pdf")

    if not os.path.exists(cached_pdf):
        soffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
        if not os.path.exists(soffice_path):
            soffice_path = "soffice"

        cmd = [soffice_path, "--headless", "--convert-to", "pdf", target_path, "--outdir", cache_dir]
        subprocess.run(cmd, check=True, capture_output=True)

        # Move generated file to cached_pdf name
        base_name = os.path.splitext(os.path.basename(target_path))[0]
        gen_pdf = os.path.join(cache_dir, f"{base_name}.pdf")
        if os.path.exists(gen_pdf):
            if os.path.exists(cached_pdf):
                os.remove(cached_pdf)
            os.rename(gen_pdf, cached_pdf)

    if not os.path.exists(cached_pdf):
        abort(500)

    g.db.execute(
        "INSERT INTO audit_log (user_id, report_id, action, client_ip) VALUES (?, ?, ?, ?)",
        (current_user.id, report_id, "preview_pdf", request.remote_addr),
    )
    g.db.commit()

    return send_file(cached_pdf, as_attachment=False, mimetype="application/pdf")
