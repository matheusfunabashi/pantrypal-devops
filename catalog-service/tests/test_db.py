from app import config
from app.db import database_url


def test_database_url_uses_pymssql_and_escapes_password(monkeypatch):
    monkeypatch.setattr(config, "DB_PASSWORD", "p@ss/w:rd")

    url = database_url()

    assert url.drivername == "mssql+pymssql"
    assert url.password == "p@ss/w:rd"
    assert "p@ss/w:rd" not in url.render_as_string()
    assert url.database == config.DB_NAME
