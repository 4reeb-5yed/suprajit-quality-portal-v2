import os
import pytest
from app.env_sync import get_env_path, read_env_file, write_env_key, sync_env_to_db
from app.database import get_connection, GET_SETTING

def test_env_file_two_way_sync(tmp_path, monkeypatch):
    test_env = tmp_path / ".env"
    monkeypatch.setattr("app.env_sync.get_env_path", lambda: str(test_env))

    # Write initial .env keys
    write_env_key("MAIL_SERVER", "smtp.office365.com")
    write_env_key("STORAGE_FOLDER", "C:/FactoryReports")

    data = read_env_file()
    assert data["MAIL_SERVER"] == "smtp.office365.com"
    assert data["STORAGE_FOLDER"] == "C:/FactoryReports"

    # Update an existing key
    write_env_key("MAIL_SERVER", "smtp.gmail.com")
    data_updated = read_env_file()
    assert data_updated["MAIL_SERVER"] == "smtp.gmail.com"

    # Test sync to database
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    from app.database import ensure_schema
    ensure_schema(conn)

    sync_env_to_db(conn)
    row = conn.execute(GET_SETTING, ("mail_server",)).fetchone()
    assert row["value"] == "smtp.gmail.com"
    conn.close()
