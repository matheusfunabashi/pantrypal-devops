from alembic import context
from sqlalchemy import create_engine

from app.db import database_url

# The connection comes from the same DB_* variables the service uses.
# An explicit sqlalchemy.url in the config (used by tests) takes precedence.
config = context.config


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url") or database_url()
    engine = create_engine(url)
    with engine.begin() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
