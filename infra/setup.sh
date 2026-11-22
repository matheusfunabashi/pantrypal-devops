#!/usr/bin/env bash
#
# Creates every Azure resource PantryPal needs, inside an existing resource group,
# using the group prefix. Nothing is created by hand in the portal.
#
# This script is idempotent: it checks for each resource before creating it, so a
# second run makes no changes. It never creates the resource group and never writes a secret to disk.
#
# It does NOT create the per-service database users. Run infra/create-db-users.sh
# after this, once the SQL server exists.
#
# Required environment variables (all read, none hardcoded):
#   SUBSCRIPTION        Azure subscription id
#   RG                  resource group that already exists (e.g. rg-sdd-3b-g8)
#   LOCATION            Azure region (e.g. westeurope)
#   PREFIX              resource name prefix (e.g. sdd-3b-g8)
#   SQL_ADMIN_USER      SQL server admin login for initial provisioning
#   SQL_ADMIN_PASSWORD  SQL server admin password
#
#   SWA_LOCATION        optional Static Web Apps region (defaults to LOCATION)
#
# Usage:
#   az login --tenant 5ca2bc70-353c-4d1f-b7d7-7f2b2259df68
#   export SUBSCRIPTION=... RG=rg-sdd-3b-g8 LOCATION=westeurope PREFIX=sdd-3b-g8 \
#          SQL_ADMIN_USER=... SQL_ADMIN_PASSWORD=...
#   ./infra/setup.sh

set -euo pipefail

: "${SUBSCRIPTION:?set SUBSCRIPTION}"
: "${RG:?set RG}"
: "${LOCATION:?set LOCATION}"
: "${PREFIX:?set PREFIX}"
: "${SQL_ADMIN_USER:?set SQL_ADMIN_USER}"
: "${SQL_ADMIN_PASSWORD:?set SQL_ADMIN_PASSWORD}"
SWA_LOCATION=${SWA_LOCATION:-$LOCATION}

if [[ ! "$PREFIX" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]] || (( ${#PREFIX} > 24 )); then
  echo "PREFIX must be 2–24 lowercase letters, digits or hyphens, starting with a letter and ending with a letter or digit." >&2
  exit 1
fi

# Resource names, all derived from the prefix.
LOGS="${PREFIX}-logs"
ENV="${PREFIX}-env"
SQL_SERVER="${PREFIX}-sql"
PANTRY_APP="${PREFIX}-pantry"
CATALOG_APP="${PREFIX}-catalog"
PANTRY_DB="${PREFIX}-pantry-db"
CATALOG_DB="${PREFIX}-catalog-db"

if [[ "$RG" != rg-sdd-3b-g8 || "$PREFIX" != sdd-3b-g8 ||
      "$(az account show --subscription "$SUBSCRIPTION" --query tenantId -o tsv)" != 5ca2bc70-353c-4d1f-b7d7-7f2b2259df68 ]]; then
  echo "Select the IE group 8 subscription, resource group and prefix." >&2
  exit 1
fi
# Scope every CLI call explicitly, including when another shell selects a subscription.
az() { command az "$@" --subscription "$SUBSCRIPTION"; }

# The resource group must already exist; the service principal cannot create one.
if ! az group show -n "$RG" >/dev/null 2>&1; then
  echo "Resource group '$RG' not found. It must be created for you; this script never creates it." >&2
  exit 1
fi

echo "==> Log Analytics workspace: $LOGS"
if ! az monitor log-analytics workspace show -g "$RG" -n "$LOGS" >/dev/null 2>&1; then
  az monitor log-analytics workspace create -g "$RG" -n "$LOGS" -l "$LOCATION" -o none
fi
LOG_CUSTOMER_ID=$(az monitor log-analytics workspace show -g "$RG" -n "$LOGS" --query customerId -o tsv)
LOG_KEY=$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n "$LOGS" --query primarySharedKey -o tsv)

echo "==> Container Apps environment: $ENV"
if az containerapp env show -g "$RG" -n "$ENV" -o none 2>/dev/null; then
  az resource wait -g "$RG" -n "$ENV" --resource-type Microsoft.App/managedEnvironments \
    --api-version 2024-03-01 --created
else
  az containerapp env create -g "$RG" -n "$ENV" -l "$LOCATION" \
    --logs-destination log-analytics \
    --logs-workspace-id "$LOG_CUSTOMER_ID" \
    --logs-workspace-key "$LOG_KEY" -o none
fi

echo "==> SQL server: $SQL_SERVER"
if ! az sql server show -g "$RG" -n "$SQL_SERVER" >/dev/null 2>&1; then
  az sql server create -g "$RG" -n "$SQL_SERVER" -l "$LOCATION" \
    --admin-user "$SQL_ADMIN_USER" --admin-password "$SQL_ADMIN_PASSWORD" -o none
fi

echo "==> Firewall: allow Azure services (Container Apps reach the SQL server)"
# Start=End=0.0.0.0 is Azure's special rule meaning "Azure services only",
# not a public opening. Idempotent: creating it again is a no-op.
az sql server firewall-rule create -g "$RG" -s "$SQL_SERVER" \
  -n AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 -o none

create_db() {
  local name="$1"
  echo "==> SQL database (serverless): $name"
  if ! az sql db show -g "$RG" -s "$SQL_SERVER" -n "$name" >/dev/null 2>&1; then
    az sql db create -g "$RG" -s "$SQL_SERVER" -n "$name" \
      --edition GeneralPurpose --family Gen5 --compute-model Serverless \
      --min-capacity 0.5 --capacity 1 \
      --auto-pause-delay 15 \
      --max-size 2GB \
      --backup-storage-redundancy Local -o none
  fi
}
create_db "$PANTRY_DB"
create_db "$CATALOG_DB"

create_app() {
  local name="$1"
  echo "==> Container App: $name"
  if ! az containerapp show -g "$RG" -n "$name" >/dev/null 2>&1; then
    az containerapp create -g "$RG" -n "$name" --environment "$ENV" \
      --image mcr.microsoft.com/k8se/quickstart:latest \
      --ingress external --target-port 80 \
      --cpu 0.25 --memory 0.5Gi \
      --min-replicas 0 --max-replicas 1 -o none
  fi
}
create_app "$PANTRY_APP"
create_app "$CATALOG_APP"

echo "==> Static Web App: ${PREFIX}-ui"
if ! az staticwebapp show -g "$RG" -n "$PREFIX-ui" -o none 2>/dev/null; then
  az staticwebapp create -g "$RG" -n "$PREFIX-ui" -l "$SWA_LOCATION" --sku Free -o none
fi

# Outputs the CD workflow and the README need.
PANTRY_URL="https://$(az containerapp show -g "$RG" -n "$PANTRY_APP" --query properties.configuration.ingress.fqdn -o tsv)"
CATALOG_URL="https://$(az containerapp show -g "$RG" -n "$CATALOG_APP" --query properties.configuration.ingress.fqdn -o tsv)"
SQL_FQDN=$(az sql server show -g "$RG" -n "$SQL_SERVER" --query fullyQualifiedDomainName -o tsv)
UI_ORIGIN="https://$(az staticwebapp show -g "$RG" -n "$PREFIX-ui" --query defaultHostname -o tsv)"

cat <<OUT

================= PantryPal infrastructure ready =================
PANTRY_URL       $PANTRY_URL
CATALOG_URL      $CATALOG_URL
SQL_SERVER_FQDN  $SQL_FQDN
UI_ORIGIN        $UI_ORIGIN
STATIC_WEB_APP   $PREFIX-ui

Next:
  1. Create the per-service DB users:
       export SQL_SERVER=$SQL_SERVER
       export PANTRY_DB_NAME=$PANTRY_DB CATALOG_DB_NAME=$CATALOG_DB
       export PANTRY_DB_APP_PASSWORD=...  CATALOG_DB_APP_PASSWORD=...
       ./infra/create-db-users.sh
  2. After IE provides the managed identity, verify its main-branch trust:
       bash infra/check-group-identity.sh
  3. Set GitHub application secrets and deployment variables:
       bash infra/configure-github.sh
==================================================================
OUT
