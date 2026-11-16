from functools import lru_cache

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import DeclarativeBase

from app import config


class Base(DeclarativeBase):
    pass


def database_url() -> URL:
    """Build the connection URL. URL.create escapes special characters in the password."""
    return URL.create(
        "mssql+pymssql",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
    )


@lru_cache
def get_engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True)
