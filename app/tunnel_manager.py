import logging
import re
import shutil
import subprocess
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

# Active background tunnel process reference
_tunnel_process: subprocess.Popen | None = None
_tunnel_status: dict[str, Any] = {"active": False, "provider": "none", "public_url": "", "log": ""}


def get_installed_tunnel_binaries() -> dict[str, bool]:
    """Checks if Cloudflared, Tailscale, or Ngrok CLI binaries exist in PATH."""
    return {
        "cloudflared": shutil.which("cloudflared") is not None,
        "tailscale": shutil.which("tailscale") is not None,
        "ngrok": shutil.which("ngrok") is not None,
    }


def get_tunnel_status() -> dict[str, Any]:
    global _tunnel_process, _tunnel_status
    if _tunnel_process:
        poll = _tunnel_process.poll()
        if poll is not None:
            _tunnel_status["active"] = False
    return dict(_tunnel_status)


def start_cloudflared_quick_tunnel(port: int = 5000) -> dict[str, Any]:
    """Starts a native zero-config Cloudflare Quick Tunnel (trycloudflare.com)."""
    global _tunnel_process, _tunnel_status
    stop_tunnel()

    if not shutil.which("cloudflared"):
        return {"success": False, "error": "cloudflared executable not found in PATH."}

    cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        _tunnel_process = proc
        _tunnel_status = {
            "active": True,
            "provider": "cloudflared",
            "public_url": "Starting...",
            "log": "Starting Cloudflare Quick Tunnel...\n",
        }

        # Monitor output for trycloudflare.com URL
        def _read_output():
            global _tunnel_status
            url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            for line in proc.stdout:
                _tunnel_status["log"] += line
                if len(_tunnel_status["log"]) > 10000:
                    _tunnel_status["log"] = _tunnel_status["log"][-10000:]
                match = url_pattern.search(line)
                if match and _tunnel_status["public_url"] in ("Starting...", ""):
                    _tunnel_status["public_url"] = match.group(0)
                    logger.info(f"Cloudflare Tunnel Public URL: {_tunnel_status['public_url']}")

        t = threading.Thread(target=_read_output, daemon=True)
        t.start()

        # Wait up to 5 seconds for URL detection
        for _ in range(10):
            time.sleep(0.5)
            if _tunnel_status["public_url"] != "Starting...":
                break

        return {"success": True, "url": _tunnel_status["public_url"]}
    except Exception as e:
        logger.error(f"Failed to start Cloudflare tunnel: {e}")
        return {"success": False, "error": str(e)}


def start_named_cloudflared_tunnel(token: str) -> dict[str, Any]:
    """Starts an enterprise Cloudflare Tunnel via token."""
    global _tunnel_process, _tunnel_status
    stop_tunnel()

    if not token or not token.strip():
        return {"success": False, "error": "Cloudflare tunnel token cannot be empty."}

    if not shutil.which("cloudflared"):
        return {"success": False, "error": "cloudflared executable not found in PATH."}

    cmd = ["cloudflared", "tunnel", "run", "--token", token.strip()]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        _tunnel_process = proc
        _tunnel_status = {
            "active": True,
            "provider": "cloudflared_named",
            "public_url": "Active (Custom Cloudflare Hostname)",
            "log": "Starting Cloudflare Named Tunnel with token...\n",
        }

        def _read_output():
            global _tunnel_status
            for line in proc.stdout:
                _tunnel_status["log"] += line
                if len(_tunnel_status["log"]) > 10000:
                    _tunnel_status["log"] = _tunnel_status["log"][-10000:]

        t = threading.Thread(target=_read_output, daemon=True)
        t.start()

        return {"success": True, "url": "Active"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_tunnel() -> bool:
    global _tunnel_process, _tunnel_status
    if _tunnel_process:
        try:
            _tunnel_process.terminate()
            _tunnel_process.wait(timeout=3)
        except Exception as e:
            logger.warning(f"Error terminating tunnel process: {e}")
            try:
                _tunnel_process.kill()
            except Exception as ex:
                logger.warning(f"Error killing tunnel process: {ex}")
        _tunnel_process = None

    _tunnel_status = {"active": False, "provider": "none", "public_url": "", "log": "Tunnel stopped.\n"}
    return True
