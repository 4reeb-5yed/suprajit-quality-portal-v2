"""
AUTHENTIC ATTACK SURFACE & LIVE CLOUDFLARE TUNNEL TEST SUITE
================================================================================
Tests the process lifecycle, binary discovery, and public URL ingress routing
in app/tunnel_manager.py:
1. Binary Discovery & Execution Path Resolution
2. Status Polling & Initial Inactive State
3. Named Tunnel Token Validation
4. Live Cloudflare Quick Tunnel Ingress Routing:
   - Starts real cloudflared quick tunnel subprocess (if cloudflared installed)
   - Obtains active public *.trycloudflare.com URL
   - Executes live HTTP GET request to public URL and verifies HTTP 200 response
   - Terminates process via stop_tunnel() and verifies genuine PID death
================================================================================
"""

import shutil
import socket
import threading
import time
import urllib.request
import psutil
import pytest
from app.tunnel_manager import (
    get_installed_tunnel_binaries,
    get_tunnel_status,
    stop_tunnel,
    start_cloudflared_quick_tunnel,
    start_named_cloudflared_tunnel
)


def test_tunnel_binary_detection():
    """
    Verifies that get_installed_tunnel_binaries correctly inspects system PATH and returns structured dict.
    """
    binaries = get_installed_tunnel_binaries()
    assert isinstance(binaries, dict)
    assert 'cloudflared' in binaries
    assert 'tailscale' in binaries
    assert isinstance(binaries['cloudflared'], bool)
    assert isinstance(binaries['tailscale'], bool)


def test_tunnel_status_initial_state():
    """
    Verifies that get_tunnel_status accurately reflects inactive state when no background process is running.
    """
    stop_tunnel()
    status = get_tunnel_status()
    assert isinstance(status, dict)
    assert status['active'] is False
    assert status['provider'] == 'none'
    assert status['public_url'] == ''


def test_tunnel_named_empty_token_rejection():
    """
    Verifies that start_named_cloudflared_tunnel gracefully fails when given empty/invalid tokens.
    """
    res = start_named_cloudflared_tunnel("")
    assert res['success'] is False
    assert "token" in res['error'].lower()


def test_tunnel_stop_lifecycle():
    """
    Verifies that stop_tunnel safely terminates any lingering processes without raising unhandled errors.
    """
    stop_tunnel()
    assert get_tunnel_status()['active'] is False


@pytest.mark.skipif(shutil.which("cloudflared") is None, reason="cloudflared binary not installed on this host")
def test_live_cloudflared_quick_tunnel_ingress_and_pid_lifecycle(app):
    """
    Starts an actual local server, binds a live cloudflared trycloudflare.com tunnel,
    requests the public URL from the internet, and verifies process termination by PID.
    """
    # 1. Spin up an actual HTTP socket server in-process on a free port
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class PingHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"SUPRAJIT_LIVE_TUNNEL_ONLINE_OK")

    httpd = HTTPServer(('127.0.0.1', 0), PingHandler)
    server_port = httpd.server_port
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    try:
        # 2. Launch real cloudflared quick tunnel targeting this local port
        res = start_cloudflared_quick_tunnel(port=server_port)
        assert res["success"] is True, f"Failed to start tunnel: {res.get('error')}"
        
        public_url = res.get("url")
        pid = res.get("pid")
        assert public_url and public_url.startswith("https://") and "trycloudflare.com" in public_url
        assert pid is not None
        assert psutil.pid_exists(pid) is True

        # 3. Query public trycloudflare.com URL over internet (with retry for global DNS propagation)
        last_error = None
        content = ""
        for attempt in range(12):
            time.sleep(2.0)
            try:
                req = urllib.request.Request(
                    public_url,
                    headers={"User-Agent": "Suprajit-CI-Tunnel-Verification-Client"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        content = response.read().decode("utf-8")
                        break
            except Exception as ex:
                last_error = ex
                continue

        assert "SUPRAJIT_LIVE_TUNNEL_ONLINE_OK" in content, f"Tunnel content verification failed: {last_error}"

        # 4. Stop tunnel and verify process PID is genuinely dead
        stop_success = stop_tunnel()
        assert stop_success is True
        time.sleep(0.5)
        assert psutil.pid_exists(pid) is False
        assert get_tunnel_status()["active"] is False

    finally:
        stop_tunnel()
        httpd.shutdown()
        httpd.server_close()