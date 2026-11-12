#!/usr/bin/env bash
#
# Creates each service's own database user on Azure SQL, so the services never
# connect with the SQL admin login. Run once, from a team member's machine,
# after infra/setup.sh. CI and CD never run this, and never touch Azure SQL.
#
# Azure SQL has no server-level setup step for app logins the way a local SQL
# Server does, so each user is a CONTAINED database user created inside its own
# database. A contained user in the pantry database cannot see the catalog
# database, and the reverse.
#
# Idempotent: creates the user if missing, otherwise resets its password. This
# is also the rotation procedure if a database password leaks.
#
# It runs sqlcmd through the same mssql image used locally, so nobody needs to
# install sqlcmd. It opens a temporary firewall rule for the caller's public IP
# and removes it on exit, even if a step fails.
#
# Required environment variables:
#   RG                       resource group (e.g. rg-sdd-3a-g3)
#   SQL_SERVER               SQL server name, no suffix (e.g. sdd-3a-g3-sql)
#   SQL_ADMIN_USER           SQL admin login
#   SQL_ADMIN_PASSWORD       SQL admin password
#   PANTRY_DB_APP_PASSWORD   password for pantry_user
#   CATALOG_DB_APP_PASSWORD  password for catalog_user
#
# Optional (defaults match infra/setup.sh naming):
#   PANTRY_DB_NAME           default <SQL_SERVER without -sql>-pantry-db is not
#                            assumed; default is "pantry-db"-style from PREFIX if
#                            set, else must be given. Simplest: pass them.
#
# Usage:
#   export RG=... SQL_SERVER=sdd-3a-g3-sql SQL_ADMIN_USER=... SQL_ADMIN_PASSWORD=...
#   export PANTRY_DB_APP_PASSWORD=... CATALOG_DB_APP_PASSWORD=...
#   export PANTRY_DB_NAME=sdd-3a-g3-pantry-db CATALOG_DB_NAME=sdd-3a-g3-catalog-db
#   ./infra/create-db-users.sh

set -euo pipefail

: "${RG:?set RG}"
: "${SQL_SERVER:?set SQL_SERVER (name only, e.g. sdd-3a-g3-sql)}"
: "${SQL_ADMIN_USER:?set SQL_ADMIN_USER}"
: "${SQL_ADMIN_PASSWORD:?set SQL_ADMIN_PASSWORD}"
: "${PANTRY_DB_APP_PASSWORD:?set PANTRY_DB_APP_PASSWORD}"
: "${CATALOG_DB_APP_PASSWORD:?set CATALOG_DB_APP_PASSWORD}"
: "${PANTRY_DB_NAME:?set PANTRY_DB_NAME (e.g. <prefix>-pantry-db)}"
: "${CATALOG_DB_NAME:?set CATALOG_DB_NAME (e.g. <prefix>-catalog-db)}"

SQL_IMAGE="mcr.microsoft.com/mssql-tools"
SQL_FQDN=$(az sql server show -g "$RG" -n "$SQL_SERVER" --query fullyQualifiedDomainName -o tsv)

# Add a temporary firewall rule for this machine, and always remove it on exit.
MY_IP=$(curl -s https://api.ipify.org)
RULE="tmp-dbusers-$(date +%s)"
cleanup() {
  az sql server firewall-rule delete -g "$RG" -s "$SQL_SERVER" -n "$RULE" -o none 2>/dev/null || true
}
trap cleanup EXIT
echo "==> Temporary firewall rule $RULE for $MY_IP"
az sql server firewall-rule create -g "$RG" -s "$SQL_SERVER" \
  -n "$RULE" --start-ip-address "$MY_IP" --end-ip-address "$MY_IP" -o none

# Creates (or resets the password of) one contained user in one database.
# Fixed app usernames: pantry_user and catalog_user (validated, letters/digits/_).
create_user() {
  local db="$1" user="$2" pass="$3"
  if [[ ! "$user" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "user '$user' must be letters, digits and underscores only" >&2
    exit 1
  fi
  local pass_sql=${pass//\'/\'\'}
  echo "==> $user in database $db"
  # -C trust the server cert; Azure SQL requires encryption. Admin password and
  # SQL both arrive on the container's env / stdin, never in the process args.
  docker run --rm -i \
    -e SQLCMDPASSWORD="$SQL_ADMIN_PASSWORD" \
    "$SQL_IMAGE" /opt/mssql-tools/bin/sqlcmd \
    -S "$SQL_FQDN" -U "$SQL_ADMIN_USER" -d "$db" -C -b <<SQL
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'$user')
    CREATE USER [$user] WITH PASSWORD = N'$pass_sql';
ELSE
    ALTER USER [$user] WITH PASSWORD = N'$pass_sql';
GO
IF IS_ROLEMEMBER(N'db_owner', N'$user') = 0
    ALTER ROLE db_owner ADD MEMBER [$user];
GO
SQL
}

create_user "$PANTRY_DB_NAME" "pantry_user" "$PANTRY_DB_APP_PASSWORD"
create_user "$CATALOG_DB_NAME" "catalog_user" "$CATALOG_DB_APP_PASSWORD"

echo "Done. pantry_user owns $PANTRY_DB_NAME and catalog_user owns $CATALOG_DB_NAME, each its own database only."
