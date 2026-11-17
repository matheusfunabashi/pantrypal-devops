from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.db import database_url

# The connection comes from the same DB_* variables the service uses.
# An explicit sqlalchemy.url in the config (set by the tests) takes precedence.
config = context.config

# Apply the logging settings from alembic.ini, so "Running upgrade" shows in the
# container logs. Existing loggers (e.g. the request logger) are left alone.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url") or database_url()
    engine = create_engine(url)
    with engine.begin() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
