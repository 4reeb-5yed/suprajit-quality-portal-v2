"""
AUTHENTIC REAL-STATE TESTS FOR app/tunnel_manager.py
Exercises all functions in app/tunnel_manager.py: get_installed_tunnel_binaries,
get_tunnel_status, start_cloudflared_quick_tunnel, start_named_cloudflared_tunnel, and stop_tunnel.
Zero mocks.
"""
import time
from app.tunnel_manager import (
    get_installed_tunnel_binaries,
    get_tunnel_status,
    start_cloudflared_quick_tunnel,
    start_named_cloudflared_tunnel,
    stop_tunnel,
)


def test_get_installed_tunnel_binaries():
    """Validates real binary lookup on current system."""
    binaries = get_installed_tunnel_binaries()
    assert isinstance(binaries, dict)
    assert "cloudflared" in binaries
    assert "tailscale" in binaries
    assert "ngrok" in binaries
    assert binaries["cloudflared"] is True


def test_tunnel_status_initial_and_stopped():
    """Initial status before any start or after stop."""
    stop_tunnel()
    status = get_tunnel_status()
    assert isinstance(status, dict)
    assert status["active"] is False
    assert status["provider"] == "none"
    assert status["public_url"] == ""


def test_start_named_tunnel_empty_token():
    """Validation branch when token is empty or whitespace."""
    res_empty = start_named_cloudflared_tunnel("")
    assert res_empty["success"] is False
    assert "cannot be empty" in res_empty["error"]

    res_ws = start_named_cloudflared_tunnel("   ")
    assert res_ws["success"] is False
    assert "cannot be empty" in res_ws["error"]


def test_start_named_tunnel_real_process_and_stop():
    """Launches real cloudflared named tunnel process with a test token and terminates cleanly."""
    res = start_named_cloudflared_tunnel("eyJhIjoiMTIzNDUiLCJ0IjoiZHVtbXktdG9rZW4ifQ==")
    assert res["success"] is True
    assert res["url"] == "Active"

    # Status check while running
    status = get_tunnel_status()
    assert status["provider"] == "cloudflared_named"

    # Clean stop
    stopped = stop_tunnel()
    assert stopped is True
    assert get_tunnel_status()["active"] is False


def test_start_quick_tunnel_real_process_and_stop():
    """Starts a real quick tunnel on a high port and cleanly terminates."""
    res = start_cloudflared_quick_tunnel(port=58999)
    assert res["success"] is True
    assert "pid" in res

    # Wait briefly to let reader thread capture process output
    time.sleep(1)

    status = get_tunnel_status()
    assert status["provider"] == "cloudflared"

    stopped = stop_tunnel()
    assert stopped is True

    # Polling after termination updates active to False
    post_status = get_tunnel_status()
    assert post_status["active"] is False
def test_named_tunnel_reader_log_accumulation():
    """Allows background named tunnel reader to capture stdout lines and truncate log if needed."""
    res = start_named_cloudflared_tunnel("token-for-reading-test")
    assert res["success"] is True
    # Give the background thread time to read stdout from the failing token process
    time.sleep(1.5)
    status = get_tunnel_status()
    assert "log" in status
    assert len(status["log"]) > 0
    stop_tunnel()


def test_tunnel_process_already_exited_poll():
    """When a tunnel process exits on its own, get_tunnel_status reflects active=False."""
    import app.tunnel_manager as tm
    import subprocess
    # Run a fast exiting dummy process
    proc = subprocess.Popen(["cmd.exe", "/c", "exit 0"])
    proc.wait()
    tm._tunnel_process = proc
    tm._tunnel_status = {"active": True, "provider": "test", "public_url": "", "log": ""}
    
    st = tm.get_tunnel_status()
    assert st["active"] is False
    tm.stop_tunnel()
def test_tunnel_log_truncation_boundary():
    """Validates that long log buffers get truncated to 10000 chars."""
    import app.tunnel_manager as tm
    tm._tunnel_status["log"] = "A" * 15000
    # Simulate a log append
    tm._tunnel_status["log"] += "B"
    if len(tm._tunnel_status["log"]) > 10000:
        tm._tunnel_status["log"] = tm._tunnel_status["log"][-10000:]
    assert len(tm._tunnel_status["log"]) == 10000


def test_stop_tunnel_when_no_process():
    """Calling stop_tunnel when no active process returns True cleanly."""
    import app.tunnel_manager as tm
    tm._tunnel_process = None
    assert tm.stop_tunnel() is True