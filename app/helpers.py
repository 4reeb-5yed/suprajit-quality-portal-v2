import hashlib
import os


def hash_file(filepath: str, block_size: int = 65536) -> str:
    """Calculates the SHA-256 hash of a file for deduplication."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def is_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Prevents path traversal vulnerabilities.
    Ensures the target_path is strictly within the base_dir.
    """
    base_dir = os.path.realpath(base_dir)
    target_path = os.path.realpath(target_path)
    return target_path.startswith(base_dir + os.sep)


def locate_report_file(
    stored_path: str, expected_hash: str | None, search_roots: list[str], original_filename: str = ""
) -> str | None:
    """
    Resolves a report file path. If stored_path exists, verifies and returns it.
    If stored_path is missing (e.g. file was moved), searches configured search_roots
    for a matching file with the identical SHA-256 hash.
    """
    # 1. Direct path check
    if os.path.exists(stored_path):
        return stored_path

    # 2. Search candidate locations across search_roots
    fname = original_filename or os.path.basename(stored_path)
    for root in search_roots:
        if not root or not os.path.exists(root):
            continue
        try:
            for dirpath, _, filenames in os.walk(root):
                if fname in filenames:
                    candidate = os.path.join(dirpath, fname)
                    if expected_hash:
                        if hash_file(candidate) == expected_hash:
                            return candidate
                    else:
                        return candidate
        except Exception:
            continue

    return None


def customer_scope(user):
    if user.is_admin:
        return "1=1", []

    # Standard access: reports.customer_id must match user's customer_id, and recipe_name must be in customer_recipes
    if getattr(user, "access_mode", "ALL") == "CUSTOM":
        where = "customer_id = ? AND recipe_name IN (SELECT recipe_name FROM user_recipes WHERE user_id = ?)"
        params = [user.customer_id, int(user.id)]
    else:
        where = "customer_id = ? AND recipe_name IN (SELECT recipe_name FROM customer_recipes WHERE customer_id = ?)"
        params = [user.customer_id, user.customer_id]

    return where, params


import base64

from cryptography.fernet import Fernet
from flask import current_app


def get_cipher():
    secret = current_app.config["SECRET_KEY"]
    # Secret key is generated as token_hex(32) which is 64 hex chars (32 bytes).
    # Fernet requires a 32-byte url-safe base64 encoded key.
    key = base64.urlsafe_b64encode(bytes.fromhex(secret))
    return Fernet(key)


def encrypt_password(plaintext: str) -> str:
    if not plaintext:
        return ""
    cipher = get_cipher()
    return cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_password(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        cipher = get_cipher()
        return cipher.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception:
        # If decryption fails (e.g., legacy plaintext in dev), fail securely
        return ""
