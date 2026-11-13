from functools import lru_cache

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app import config


class Base(DeclarativeBase):
    pass


def database_url() -> URL:
    """Build the connection URL from the DB_* settings.

    URL.create escapes special characters in the password, and the URL hides the
    password when printed, so it never ends up in the logs.
    """
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
    # pool_pre_ping checks a connection before using it, so a connection dropped
    # while the Azure database was paused is replaced instead of failing a request.
    return create_engine(database_url(), pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine())
