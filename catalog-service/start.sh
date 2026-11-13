#!/bin/sh
# Apply database migrations, then start the API. If a migration fails the
# container exits, so a broken schema never serves traffic.
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
