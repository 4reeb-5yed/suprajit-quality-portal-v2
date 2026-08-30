"""
PROPERTY-BASED HYPOTHESIS TEST SUITE FOR CRYPTOGRAPHY & PATH SAFETY
Tests invariant algebraic properties of security helpers.
"""

import pytest
pytestmark = pytest.mark.unit


from hypothesis import given, strategies as st, settings, HealthCheck
from app.helpers import is_safe_path, encrypt_password, decrypt_password
import os

@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(plaintext=st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=0, max_size=2000))
def test_property_crypto_roundtrip_algebraic_identity(app, plaintext):
    """
    PROPERTY: For all arbitrary unicode strings P:
    decrypt(encrypt(P)) == P
    And for all non-empty P:
    encrypt(P) != P
    """
    with app.app_context():
        if not plaintext:
            assert encrypt_password("") == ""
            assert decrypt_password("") == ""
        else:
            cipher = encrypt_password(plaintext)
            assert cipher != plaintext
            assert isinstance(cipher, str)
            decrypted = decrypt_password(cipher)
            assert decrypted == plaintext


@settings(max_examples=150)
@given(
    base=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_\\/:", min_size=3, max_size=50),
    rel_path=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.", min_size=1, max_size=50)
)
def test_property_safe_path_valid_subpaths(base, rel_path):
    """
    PROPERTY: Any legitimately nested subpath strictly beneath base_dir must return True.
    """
    # Clean paths for Windows/POSIX realpath
    clean_base = os.path.abspath(r"C:\test_vault")
    target = os.path.join(clean_base, "subdir", rel_path)
    # If no '..' escape exists, target is safely within clean_base
    if ".." not in rel_path:
        assert is_safe_path(clean_base, target) is True


@settings(max_examples=150)
@given(
    traversal_depth=st.integers(min_value=2, max_value=10),
    payload=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_", min_size=1, max_size=20)
)
def test_property_safe_path_guaranteed_traversal_rejection(traversal_depth, payload):
    """
    PROPERTY: Any target that traverses above base_dir via '..' sequences MUST return False.
    """
    clean_base = os.path.abspath(r"C:\factory\storage")
    traversal_prefix = (".." + os.sep) * traversal_depth
    malicious_target = os.path.normpath(os.path.join(clean_base, traversal_prefix + payload))
    assert is_safe_path(clean_base, malicious_target) is False
