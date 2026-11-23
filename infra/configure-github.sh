#!/usr/bin/env bash
# Stage IE-only Actions settings. The current personal deployment uses other names.
set -euo pipefail
source "$(dirname "$0")/group8.env"
REPO=matheusfunabashi/pantrypal-devops
scope=(--subscription "$SUBSCRIPTION" --resource-group "$RG")
: "${PANTRY_DB_APP_PASSWORD:?source .env.azure.group8}" "${CATALOG_DB_APP_PASSWORD:?}"

client=$(bash "$(dirname "$0")/check-group-identity.sh")
tenant=$(az account show --subscription "$SUBSCRIPTION" --query tenantId -o tsv)
sql=$(az sql server show "${scope[@]}" -n "$SQL_SERVER" --query fullyQualifiedDomainName -o tsv)
pantry=$(az containerapp show "${scope[@]}" -n "$PREFIX-pantry" --query properties.configuration.ingress.fqdn -o tsv)
catalog=$(az containerapp show "${scope[@]}" -n "$PREFIX-catalog" --query properties.configuration.ingress.fqdn -o tsv)
ui=$(az staticwebapp show "${scope[@]}" -n "$PREFIX-ui" --query defaultHostname -o tsv)
: "${client:?}" "${tenant:?}" "${sql:?}" "${pantry:?}" "${catalog:?}" "${ui:?}"
# Check the existing Open Food Facts contact before updating any setting.
gh api "repos/$REPO/actions/variables/OFF_USER_AGENT" --silent

set_variable() {
  local name="IE_$1" value="$2"
  if gh api "repos/$REPO/actions/variables/$name" --silent 2>/dev/null; then
    gh api -X PATCH "repos/$REPO/actions/variables/$name" -f name="$name" -f value="$value" --silent
  else
    gh api -X POST "repos/$REPO/actions/variables" -f name="$name" -f value="$value" --silent
  fi
}
set_variable AZURE_CLIENT_ID "$client"
set_variable AZURE_TENANT_ID "$tenant"
set_variable AZURE_SUBSCRIPTION_ID "$SUBSCRIPTION"
set_variable AZURE_RG "$RG"
set_variable PREFIX "$PREFIX"
set_variable SQL_SERVER_FQDN "$sql"
set_variable PANTRY_URL "https://$pantry"
set_variable CATALOG_URL "https://$catalog"
set_variable UI_ORIGIN "https://$ui"
printf '%s' "$PANTRY_DB_APP_PASSWORD" | gh secret set IE_PANTRY_DB_APP_PASSWORD --repo "$REPO"
printf '%s' "$CATALOG_DB_APP_PASSWORD" | gh secret set IE_CATALOG_DB_APP_PASSWORD --repo "$REPO"
