#!/bin/bash
# Creates the application's own SQL Server login and database, so the API
# never connects as the "sa" admin account.
#
# Runs once per database as a one-shot container in docker-compose.yml,
# after the database is healthy. Safe to re-run: it creates the database and
# login if they are missing, and otherwise resets the login's password to the
# current .env value.
#
# The login gets no server-level role. It is made db_owner of its own
# database only, which is enough for the service to run migrations there
# and nothing else on the server.
#
# Expected environment variables:
#   DB_HOST          database container to connect to (e.g. pantry-db)
#   SA_PASSWORD      SQL Server admin password (used only by this script)
#   APP_DB_NAME      database to create and own (e.g. pantry_db)
#   APP_DB_USER      login to create (e.g. pantry_user)
#   APP_DB_PASSWORD  password for that login
set -euo pipefail

: "${DB_HOST:?DB_HOST is required}"
: "${SA_PASSWORD:?SA_PASSWORD is required}"
: "${APP_DB_NAME:?APP_DB_NAME is required}"
: "${APP_DB_USER:?APP_DB_USER is required}"
: "${APP_DB_PASSWORD:?APP_DB_PASSWORD is required}"

# Login and database names are used as identifiers, so only allow simple names.
for name in "$APP_DB_USER" "$APP_DB_NAME"; do
  if [[ ! "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "'$name' must contain only letters, digits and underscores" >&2
    exit 1
  fi
done

# Escape single quotes for use inside a T-SQL string literal.
app_password_sql=${APP_DB_PASSWORD//\'/\'\'}

# sqlcmd reads the admin password from this variable, so it never shows up
# in the process list or in logs.
export SQLCMDPASSWORD="$SA_PASSWORD"

# The SQL goes in on stdin, not in -Q, so the password never appears in the
# process arguments.
/opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST" -U sa -C -b <<SQL
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'$APP_DB_USER')
    CREATE LOGIN [$APP_DB_USER] WITH PASSWORD = N'$app_password_sql', CHECK_POLICY = ON;
ELSE
    ALTER LOGIN [$APP_DB_USER] WITH PASSWORD = N'$app_password_sql';
GO

IF DB_ID(N'$APP_DB_NAME') IS NULL
    CREATE DATABASE [$APP_DB_NAME];
GO

USE [$APP_DB_NAME];
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'$APP_DB_USER')
    CREATE USER [$APP_DB_USER] FOR LOGIN [$APP_DB_USER];
IF IS_ROLEMEMBER(N'db_owner', N'$APP_DB_USER') = 0
    ALTER ROLE db_owner ADD MEMBER [$APP_DB_USER];
GO
SQL

echo "App login '$APP_DB_USER' owns database '$APP_DB_NAME' on $DB_HOST (db_owner only)."
