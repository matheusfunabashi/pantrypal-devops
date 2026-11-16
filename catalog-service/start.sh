#!/bin/sh
# Apply database migrations, then start the API.
#
# Azure SQL refuses connections for about a minute while it resumes from
# auto-pause (error 40613), so the migration is retried up to 6 times,
# 10 seconds apart. If it still fails, the container exits and never serves
# traffic with a broken schema.
set -e

max_attempts=6
attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Migrations failed after $attempt attempts, giving up." >&2
    exit 1
  fi
  echo "Migrations failed (attempt $attempt of $max_attempts), retrying in 10 s." >&2
  attempt=$((attempt + 1))
  sleep 10
done

# --no-access-log: our middleware already writes one line per request.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
