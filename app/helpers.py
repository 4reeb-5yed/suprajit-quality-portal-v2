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
