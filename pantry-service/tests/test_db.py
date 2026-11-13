from app import config
from app.db import database_url


def test_database_url_uses_pymssql_and_hides_password(monkeypatch):
    monkeypatch.setattr(config, "DB_PASSWORD", "p@ss/w:rd")

    url = database_url()

    assert url.drivername == "mssql+pymssql"
    assert url.password == "p@ss/w:rd"
    # Printing the URL (e.g. in a log or an error) must not show the password.
    assert "p@ss/w:rd" not in str(url)
    assert url.database == config.DB_NAME
