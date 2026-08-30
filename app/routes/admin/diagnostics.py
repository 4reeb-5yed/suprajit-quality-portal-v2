import os
from datetime import datetime

from flask import current_app, flash, g, redirect, render_template, request, send_file, url_for

from app.database import GET_SETTING
from app.routes.admin import admin_bp
from app.sync_engine import SyncEngine


@admin_bp.route("/diagnostics")
def diagnostics():
    # Read the last 100 lines of the suprajit.log file
    log_lines = []
    try:
        log_path = current_app.config.get("LOG_FILE_PATH")
        if log_path and os.path.exists(log_path):
            with open(log_path, encoding="utf-8") as f:
                lines = f.readlines()
                log_lines = lines[-100:]
        else:
            log_lines = ["No log file found. System has not generated any logs yet."]
    except Exception as e:
        log_lines = [f"Error reading log file: {e}"]

    # Get last sync info
    last_run = g.db.execute("SELECT * FROM batch_runs ORDER BY run_started DESC LIMIT 1").fetchone()

    # Advanced Diagnostics Engine Stats
    db_path = current_app.config["DATABASE_PATH"]
    db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2) if os.path.exists(db_path) else 0.0

    total_reports = g.db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    unassigned_reports = g.db.execute("SELECT COUNT(*) FROM reports WHERE customer_id IS NULL").fetchone()[0]
    total_customers = g.db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    sync_time_row = g.db.execute(GET_SETTING, ("sync_time",)).fetchone()
    sync_time_str = sync_time_row["value"] if sync_time_row else "02:00"

    schema_version_row = g.db.execute("PRAGMA user_version").fetchone()
    schema_version = schema_version_row[0] if schema_version_row else 1

    audit_logs = g.db.execute("""
        SELECT a.id, a.created_at as timestamp, a.action, a.client_ip as ip_address,
               COALESCE(u.display_name, u.username, 'System') as display_name,
               COALESCE(u.username, 'System') as username,
               COALESCE(u.role, 'system') as role,
               COALESCE(r.original_filename, a.detail, 'Web Session') as target_info
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        LEFT JOIN reports r ON a.report_id = r.id
        ORDER BY a.id DESC LIMIT 100
    """).fetchall()

    return render_template(
        "admin/diagnostics.html",
        log_lines=log_lines,
        last_run=last_run,
        db_size_mb=db_size_mb,
        schema_version=schema_version,
        total_reports=total_reports,
        unassigned_reports=unassigned_reports,
        total_customers=total_customers,
        sync_time_str=sync_time_str,
        audit_logs=audit_logs,
    )


@admin_bp.route("/repair", methods=["GET", "POST"])
def repair():
    trace_log = None
    success_msg = None
    error_msg = None

    if request.method == "POST":
        action = request.form.get("action")
        db_path = current_app.config["DATABASE_PATH"]
        storage_base = current_app.config["STORAGE_FOLDER"]

        try:
            if action == "dry_run":
                engine = SyncEngine(db_path, storage_base)
                # Parse date if provided
                target = request.form.get("target_date")
                dt = datetime.strptime(target, "%Y-%m-%d").date() if target else None

                # Execute dry run
                trace_log = engine.execute_dry_run(target_date=dt)

            elif action == "purge_date":
                target = request.form.get("target_date")
                if not target:
                    error_msg = "Please provide a date to purge."
                else:
                    count = g.db.execute("SELECT COUNT(*) FROM reports WHERE report_date = ?", (target,)).fetchone()[0]
                    g.db.execute("DELETE FROM reports WHERE report_date = ?", (target,))
                    g.db.commit()
                    success_msg = f"Successfully purged {count} records for {target}."

            elif action == "force_sync":
                target = request.form.get("target_date")
                if not target:
                    error_msg = "Please provide a date to force sync."
                else:
                    dt = datetime.strptime(target, "%Y-%m-%d").date()
                    engine = SyncEngine(db_path, storage_base)

                    # Run in background to prevent hanging UI
                    import threading

                    def run_force(dt_val):
                        try:
                            engine.run_batch(target_date=dt_val)
                        except Exception as e:
                            print(f"Force sync error: {e}")

                    t = threading.Thread(target=run_force, args=(dt,))
                    t.start()
                    success_msg = f"Force Sync started in the background for {target}. Check Diagnostics in 30 seconds."

        except Exception as e:
            error_msg = str(e)

    return render_template(
        "admin/repair.html", trace_log=trace_log, success_msg=success_msg, error_msg=error_msg
    )


@admin_bp.route("/logs/download")
def download_logs():
    """Allows System Administrators to instantly download the raw system log file for observability."""
    log_path = current_app.config.get("LOG_FILE_PATH")
    if not log_path or not os.path.exists(log_path):
        flash("System log file does not exist yet.", "warning")
        return redirect(url_for("admin.dashboard"))

    return send_file(log_path, as_attachment=True, download_name="suprajit_system.log", mimetype="text/plain")
