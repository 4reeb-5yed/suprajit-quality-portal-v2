import hashlib
import os

def hash_file(filepath: str, block_size: int = 65536) -> str:
    """Calculates the SHA-256 hash of a file for deduplication."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
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

def customer_scope(user):
    if user.is_admin:
        return "1=1", []
    
    # Securely scope standard users to only their allowed recipes
    where = "recipe_name IN (SELECT recipe_name FROM customer_recipes WHERE customer_id = ?)"
    params = [user.customer_id]
    return where, params

import base64
from flask import current_app

from cryptography.fernet import Fernet
def get_cipher():
    secret = current_app.config['SECRET_KEY']
    # Secret key is generated as token_hex(32) which is 64 hex chars (32 bytes).
    # Fernet requires a 32-byte url-safe base64 encoded key.
    key = base64.urlsafe_b64encode(bytes.fromhex(secret))
    return Fernet(key)

def encrypt_password(plaintext: str) -> str:
    if not plaintext:
        return ""
    cipher = get_cipher()
    return cipher.encrypt(plaintext.encode('utf-8')).decode('utf-8')

def decrypt_password(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        cipher = get_cipher()
        return cipher.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except Exception:
        # If decryption fails (e.g., legacy plaintext in dev), fail securely
        return ""

