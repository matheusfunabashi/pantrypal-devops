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
#   IMAGE_TAG           image tag to deploy first (a commit SHA, or "latest")
#
# Optional:
#   SWA_LOCATION        Static Web Apps region (default westeurope; SWA exists in a
#                       limited set of regions, so it is separate from LOCATION)
#   GHCR_OWNER          GHCR owner for the images (default matheusfunabashi)
#
# Usage:
#   az login --service-principal -u <appId> -p <secret> --tenant <tenant>
#   export SUBSCRIPTION=... RG=... LOCATION=westeurope PREFIX=sdd-3a-g3 \
#          SQL_ADMIN_USER=... SQL_ADMIN_PASSWORD=... IMAGE_TAG=latest
#   ./infra/setup.sh

set -euo pipefail

: "${SUBSCRIPTION:?set SUBSCRIPTION}"
: "${RG:?set RG}"
: "${LOCATION:?set LOCATION}"
: "${PREFIX:?set PREFIX}"
: "${SQL_ADMIN_USER:?set SQL_ADMIN_USER}"
: "${SQL_ADMIN_PASSWORD:?set SQL_ADMIN_PASSWORD}"
: "${IMAGE_TAG:?set IMAGE_TAG}"
SWA_LOCATION="${SWA_LOCATION:-westeurope}"
GHCR_OWNER="${GHCR_OWNER:-matheusfunabashi}"

# Resource names, all derived from the prefix.
LOGS="${PREFIX}-logs"
ENV="${PREFIX}-env"
SQL_SERVER="${PREFIX}-sql"
PANTRY_APP="${PREFIX}-pantry"
CATALOG_APP="${PREFIX}-catalog"
PANTRY_DB="${PREFIX}-pantry-db"
CATALOG_DB="${PREFIX}-catalog-db"
SWA="${PREFIX}-ui"
PANTRY_IMAGE="ghcr.io/${GHCR_OWNER}/pantrypal-pantry:${IMAGE_TAG}"
CATALOG_IMAGE="ghcr.io/${GHCR_OWNER}/pantrypal-catalog:${IMAGE_TAG}"

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
  local name="$1" image="$2"
  echo "==> Container App: $name"
  if ! az containerapp show -g "$RG" -n "$name" >/dev/null 2>&1; then
    # The images are public on GHCR, so no registry credentials are needed.
    # Real environment variables and the DB password secret are set by the CD
    # workflow on every deploy; here we only create the app with a first image.
    az containerapp create -g "$RG" -n "$name" --environment "$ENV" \
      --image "$image" \
      --ingress external --target-port 8000 \
      --min-replicas 0 --max-replicas 1 -o none
  fi
}
create_app "$PANTRY_APP" "$PANTRY_IMAGE"
create_app "$CATALOG_APP" "$CATALOG_IMAGE"

echo "==> Static Web App: $SWA"
if ! az staticwebapp show -g "$RG" -n "$SWA" >/dev/null 2>&1; then
  az staticwebapp create -g "$RG" -n "$SWA" -l "$SWA_LOCATION" -o none
fi

# Outputs the CD workflow and the README need.
PANTRY_URL="https://$(az containerapp show -g "$RG" -n "$PANTRY_APP" --query properties.configuration.ingress.fqdn -o tsv)"
CATALOG_URL="https://$(az containerapp show -g "$RG" -n "$CATALOG_APP" --query properties.configuration.ingress.fqdn -o tsv)"
SQL_FQDN=$(az sql server show -g "$RG" -n "$SQL_SERVER" --query fullyQualifiedDomainName -o tsv)
UI_HOST=$(az staticwebapp show -g "$RG" -n "$SWA" --query defaultHostname -o tsv)

cat <<OUT

================= PantryPal infrastructure ready =================
PANTRY_URL       $PANTRY_URL
CATALOG_URL      $CATALOG_URL
SQL_SERVER_FQDN  $SQL_FQDN
UI_ORIGIN        https://$UI_HOST

Next:
  1. Create the per-service DB users:
       export SQL_SERVER_FQDN=$SQL_FQDN
       export PANTRY_DB_APP_PASSWORD=...  CATALOG_DB_APP_PASSWORD=...
       ./infra/create-db-users.sh
  2. Set these GitHub Actions secrets and variables (values above):
       gh secret set AZURE_CREDENTIALS < sp.json
       gh secret set PANTRY_DB_APP_PASSWORD
       gh secret set CATALOG_DB_APP_PASSWORD
       gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN \\
         "\$(az staticwebapp secrets list -g $RG -n $SWA --query properties.apiKey -o tsv)"
       gh variable set AZURE_RG --body "$RG"
       gh variable set PREFIX --body "$PREFIX"
       gh variable set SQL_SERVER_FQDN --body "$SQL_FQDN"
       gh variable set PANTRY_URL --body "$PANTRY_URL"
       gh variable set CATALOG_URL --body "$CATALOG_URL"
       gh variable set UI_ORIGIN --body "https://$UI_HOST"
       gh variable set OFF_USER_AGENT --body "PantryPal/0.1 (<team-email>)"
==================================================================
OUT
