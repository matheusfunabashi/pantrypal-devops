import secrets

from app import config
from app.db import database_url


def test_database_url_uses_pymssql_and_escapes_password(monkeypatch):
    # A random value with characters that must be escaped in a URL.
    password = "@/:" + secrets.token_hex(8)
    monkeypatch.setattr(config, "DB_PASSWORD", password)

    url = database_url()

    assert url.drivername == "mssql+pymssql"
    assert url.password == password
    assert password not in url.render_as_string()
    assert url.database == config.DB_NAME
