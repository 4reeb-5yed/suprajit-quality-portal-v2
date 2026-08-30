from flask import flash, g, redirect, request, url_for

from app.database import SET_SETTING
from app.routes.admin import admin_bp
from app.tunnel_manager import (
    start_cloudflared_quick_tunnel,
    start_named_cloudflared_tunnel,
    stop_tunnel,
)


@admin_bp.route("/tunnel/action", methods=["POST"])
def tunnel_action():
    """Handles starting and stopping native Cloudflare / Tailscale tunnels."""
    action = request.form.get("action")
    token = request.form.get("tunnel_token", "")

    if action == "start_quick":
        res = start_cloudflared_quick_tunnel(port=5000)
        if res.get("success"):
            if res.get("url") and res.get("url") != "Starting...":
                g.db.execute(SET_SETTING, ("public_portal_url", res["url"]))
                g.db.commit()
            flash(f"Cloudflare Tunnel started! Public URL: {res.get('url')}", "success")
        else:
            flash(f"Could not start Cloudflare tunnel: {res.get('error')}", "error")

    elif action == "start_token":
        if not token:
            flash("Please provide a Cloudflare Tunnel Token.", "error")
        else:
            res = start_named_cloudflared_tunnel(token)
            if res.get("success"):
                flash("Cloudflare Named Tunnel started successfully.", "success")
            else:
                flash(f"Could not start Named Tunnel: {res.get('error')}", "error")

    elif action == "stop":
        stop_tunnel()
        flash("Tunnel stopped successfully.", "success")

    return redirect(url_for("admin.settings"))
