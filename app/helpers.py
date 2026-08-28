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
    if len(secret) == 64:
        key = base64.urlsafe_b64encode(bytes.fromhex(secret))
    else:
        import hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode('utf-8')).digest())
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
        if ciphertext.startswith("ENC:"):
            ciphertext = ciphertext[4:]
        cipher = get_cipher()
        return cipher.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except Exception:
        # If decryption fails (e.g., legacy plaintext in dev), fail securely
        return ""

def sync_env_file(updates: dict):
    """
    Two-Way Synchronization:
    Writes configuration settings safely to the .env file.
    Sensitive credentials (e.g. SMTP passwords) are stored as encrypted ciphertext
    (ENC:...) with the decryption master key isolated in data/.master_key.
    """
    env_path = current_app.config.get('ENV_PATH') or os.path.join(current_app.config['BASE_DIR'], '.env')
    
    existing_lines = []
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
        except Exception:
            existing_lines = []
            
    # Process updates: encrypt passwords if present
    processed = {}
    for k, v in updates.items():
        if v is None:
            continue
        v_str = str(v).strip()
        if k in ('MAIL_PASSWORD', 'SECRET_KEY_BACKUP') and v_str and not v_str.startswith('ENC:'):
            # Encrypt password before storing in .env
            enc_val = encrypt_password(v_str)
            processed[k] = f"ENC:{enc_val}"
        else:
            processed[k] = v_str
            
    # Update existing keys or append new ones
    updated_keys = set()
    new_lines = []
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in processed:
                new_lines.append(f"{key}={processed[key]}\n")
                updated_keys.add(key)
                continue
        new_lines.append(line)
        
    for k, v in processed.items():
        if k not in updated_keys:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')
            new_lines.append(f"{k}={v}\n")
            
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception as e:
        current_app.logger.error(f"Failed to sync .env file: {e}")


