"""
Two-way environment variable and SQLite system_settings synchronization.
Ensures that settings saved in the Admin UI write to .env, and values set in .env update system_settings.
"""

import os
import re

from app.config import Config


def get_env_path() -> str:
    """Returns the absolute path to the active .env file."""
    return os.path.join(Config.BASE_DIR, ".env")


def read_env_file() -> dict[str, str]:
    """Reads key-value pairs from .env preserving non-empty, non-comment lines."""
    path = get_env_path()
    if not os.path.exists(path):
        return {}

    env_data = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_data[key.strip()] = val.strip().strip("'\"")
    return env_data


def write_env_key(key: str, value: str) -> None:
    """Safely updates or appends a key=value entry in the .env file."""
    path = get_env_path()
    lines = []
    found = False

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()

    clean_val = str(value)
    if " " in clean_val or "\n" in clean_val:
        formatted_line = f'{key}="{clean_val}"\n'
    else:
        formatted_line = f"{key}={clean_val}\n"

    new_lines = []
    for line in lines:
        if re.match(rf"^\s*{re.escape(key)}\s*=", line):
            new_lines.append(formatted_line)
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(formatted_line)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def sync_env_to_db(conn) -> None:
    """
    On application boot, syncs initial values from .env into SQLite system_settings table
    if system_settings does not already have a value configured.
    """
    from app.database import GET_SETTING, SET_SETTING

    env_map = {
        "HOST": "host",
        "PORT": "port",
        "MAIL_SERVER": "mail_server",
        "MAIL_PORT": "mail_port",
        "MAIL_USERNAME": "mail_username",
        "STORAGE_FOLDER": "root_search_path",
    }

    env_data = read_env_file()
    for env_key, db_key in env_map.items():
        if env_key in env_data and env_data[env_key]:
            existing = conn.execute(GET_SETTING, (db_key,)).fetchone()
            if not existing or not existing["value"]:
                conn.execute(SET_SETTING, (db_key, env_data[env_key]))
    conn.commit()
