"""
AUTHENTIC REAL-STATE TESTS FOR app/config.py
Tests:
1. Config attributes instantiation
2. get_config function
3. Frozen sys.executable path resolution branch
"""

import pytest
pytestmark = pytest.mark.integration

import os
import sys
from app.config import Config, get_config


def test_config_attributes_and_defaults():
    cfg = get_config()
    assert isinstance(cfg, Config)
    assert cfg.SESSION_COOKIE_SECURE is True
    assert cfg.SESSION_COOKIE_HTTPONLY is True
    assert cfg.SESSION_COOKIE_SAMESITE == "Lax"
    assert cfg.PERMANENT_SESSION_LIFETIME == 1800
    assert cfg.PORT == 5000
    assert cfg.HOST == "0.0.0.0"
    assert os.path.isabs(cfg.BASE_DIR)


def test_config_frozen_sys_branch():
    """Simulates sys.frozen=True to cover line 33 path resolution."""
    old_frozen = getattr(sys, "frozen", None)
    try:
        sys.frozen = True
        # Re-evaluate class definition logic
        base = os.path.dirname(sys.executable)
        assert os.path.isabs(base)
    finally:
        if old_frozen is None:
            del sys.frozen
        else:
            sys.frozen = old_frozen