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
#   RG                  resource group that already exists (e.g. rg-sdd-3a-g3)
#   LOCATION            Azure region (e.g. westeurope)
#   PREFIX              resource name prefix (e.g. sdd-3a-g3)
#   SQL_ADMIN_USER      SQL server admin login (used only by create-db-users.sh)
#   SQL_ADMIN_PASSWORD  SQL server admin password
#
#   STORAGE_ACCOUNT     globally unique storage account name for the static UI
#
# Usage:
#   az login        (or az login --service-principal with the group's credentials)
#   export SUBSCRIPTION=... RG=... LOCATION=germanywestcentral PREFIX=sdd-3a-g3 \
#          SQL_ADMIN_USER=... SQL_ADMIN_PASSWORD=... STORAGE_ACCOUNT=...
#   ./infra/setup.sh

set -euo pipefail

: "${SUBSCRIPTION:?set SUBSCRIPTION}"
: "${RG:?set RG}"
: "${LOCATION:?set LOCATION}"
: "${PREFIX:?set PREFIX}"
: "${SQL_ADMIN_USER:?set SQL_ADMIN_USER}"
: "${SQL_ADMIN_PASSWORD:?set SQL_ADMIN_PASSWORD}"
: "${STORAGE_ACCOUNT:?set STORAGE_ACCOUNT (3–24 lowercase letters and digits)}"

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

az account set --subscription "$SUBSCRIPTION"

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
if ! az containerapp env show -g "$RG" -n "$ENV" >/dev/null 2>&1; then
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

echo "==> Storage static website: $STORAGE_ACCOUNT"
if ! az storage account show -g "$RG" -n "$STORAGE_ACCOUNT" >/dev/null 2>&1; then
  az storage account create -g "$RG" -n "$STORAGE_ACCOUNT" -l "$LOCATION" \
    --sku Standard_LRS --kind StorageV2 --https-only true --min-tls-version TLS1_2 \
    --allow-blob-public-access false -o none
fi
export AZURE_STORAGE_KEY
AZURE_STORAGE_KEY=$(az storage account keys list -g "$RG" -n "$STORAGE_ACCOUNT" --query '[0].value' -o tsv)
az storage blob service-properties update --account-name "$STORAGE_ACCOUNT" \
  --static-website --index-document index.html -o none
unset AZURE_STORAGE_KEY

# Outputs the CD workflow and the README need.
PANTRY_URL="https://$(az containerapp show -g "$RG" -n "$PANTRY_APP" --query properties.configuration.ingress.fqdn -o tsv)"
CATALOG_URL="https://$(az containerapp show -g "$RG" -n "$CATALOG_APP" --query properties.configuration.ingress.fqdn -o tsv)"
SQL_FQDN=$(az sql server show -g "$RG" -n "$SQL_SERVER" --query fullyQualifiedDomainName -o tsv)
UI_ORIGIN=$(az storage account show -g "$RG" -n "$STORAGE_ACCOUNT" --query primaryEndpoints.web -o tsv)
UI_ORIGIN="${UI_ORIGIN%/}"

cat <<OUT

================= PantryPal infrastructure ready =================
PANTRY_URL       $PANTRY_URL
CATALOG_URL      $CATALOG_URL
SQL_SERVER_FQDN  $SQL_FQDN
UI_ORIGIN        $UI_ORIGIN
STORAGE_ACCOUNT  $STORAGE_ACCOUNT

Next:
  1. Create the per-service DB users:
       export SQL_SERVER=$SQL_SERVER
       export PANTRY_DB_NAME=$PANTRY_DB CATALOG_DB_NAME=$CATALOG_DB
       export PANTRY_DB_APP_PASSWORD=...  CATALOG_DB_APP_PASSWORD=...
       ./infra/create-db-users.sh
  2. Configure the main-only GitHub OIDC identity:
       bash infra/setup-github-identity.sh
  3. Set GitHub application secrets and deployment variables:
       export OFF_USER_AGENT='PantryPal/0.1 (<team-email>)'
       bash infra/configure-github.sh
==================================================================
OUT
