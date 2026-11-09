#!/bin/bash
# Creates (or updates) the application's own SQL Server login, so the API
# never connects as the "sa" admin account.
#
# Runs once per database as a one-shot container in docker-compose.yml,
# after the database is healthy. Safe to re-run: it creates the login if it
# is missing and otherwise resets its password to the current .env value.
#
# The login gets only the "dbcreator" server role: enough for the service to
# create its own database on startup (and become that database's owner),
# without admin rights over the rest of the server.
#
# Expected environment variables:
#   DB_HOST          database container to connect to (e.g. pantry-db)
#   SA_PASSWORD      SQL Server admin password (used only by this script)
#   APP_DB_USER      login to create (e.g. pantry_user)
#   APP_DB_PASSWORD  password for that login
set -euo pipefail

: "${DB_HOST:?DB_HOST is required}"
: "${SA_PASSWORD:?SA_PASSWORD is required}"
: "${APP_DB_USER:?APP_DB_USER is required}"
: "${APP_DB_PASSWORD:?APP_DB_PASSWORD is required}"

# Login names are used as identifiers, so only allow simple names.
if [[ ! "$APP_DB_USER" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "APP_DB_USER must contain only letters, digits and underscores" >&2
  exit 1
fi

# Escape single quotes for use inside a T-SQL string literal.
app_password_sql=${APP_DB_PASSWORD//\'/\'\'}

# sqlcmd reads the admin password from this variable, so it never shows up
# in the process list or in logs.
export SQLCMDPASSWORD="$SA_PASSWORD"

/opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST" -U sa -C -b -Q "
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'$APP_DB_USER')
    CREATE LOGIN [$APP_DB_USER] WITH PASSWORD = N'$app_password_sql', CHECK_POLICY = ON;
ELSE
    ALTER LOGIN [$APP_DB_USER] WITH PASSWORD = N'$app_password_sql';

IF IS_SRVROLEMEMBER(N'dbcreator', N'$APP_DB_USER') = 0
    ALTER SERVER ROLE dbcreator ADD MEMBER [$APP_DB_USER];
"

echo "App login '$APP_DB_USER' is ready on $DB_HOST (role: dbcreator)."
