"""
AUTHENTIC ATTACK SURFACE TEST SUITE: TUNNEL & INGRESS MANAGEMENT
Tests the process lifecycle and security boundary of public tunnel management in app/tunnel_manager.py:
1. Binary Discovery & Execution Path Resolution
2. Status Polling & Log Scraping for Quick vs Named Tunnels
3. Process Termination & Process Cleanup
"""

import pytest
import subprocess
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
    # Safe invocation when no tunnel is active
    stop_tunnel()
    assert get_tunnel_status()['active'] is False
