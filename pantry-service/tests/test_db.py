import secrets

from app import config
from app.db import database_url


def test_database_url_uses_pymssql_and_hides_password(monkeypatch):
    # A random value with special characters. It is generated, not written in the
    # file, so secret scanners don't flag a fake password.
    password = secrets.token_urlsafe(12) + "@/:"
    monkeypatch.setattr(config, "DB_PASSWORD", password)

    url = database_url()

    assert url.drivername == "mssql+pymssql"
    assert url.password == password
    # Printing the URL (e.g. in a log or an error) must not show the password.
    assert password not in str(url)
    assert url.database == config.DB_NAME
