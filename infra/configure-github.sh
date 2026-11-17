#!/usr/bin/env bash
set -euo pipefail

: "${SUBSCRIPTION:?}" "${RG:?}" "${PREFIX:?}" "${STORAGE_ACCOUNT:?}"
: "${PANTRY_DB_APP_PASSWORD:?}" "${CATALOG_DB_APP_PASSWORD:?}" "${OFF_USER_AGENT:?}"
REPO="${REPO:-matheusfunabashi/pantrypal-devops}"
printf '%s' "$PANTRY_DB_APP_PASSWORD" | gh secret set PANTRY_DB_APP_PASSWORD --repo "$REPO"
printf '%s' "$CATALOG_DB_APP_PASSWORD" | gh secret set CATALOG_DB_APP_PASSWORD --repo "$REPO"

set_variable() {
  local name="$1" value="$2"
  : "${value:?GitHub variable value must not be empty}"
  if gh api "repos/$REPO/actions/variables/$name" --silent 2>/dev/null; then
    gh api --method PATCH "repos/$REPO/actions/variables/$name" -f name="$name" -f value="$value" --silent
  else
    gh api --method POST "repos/$REPO/actions/variables" -f name="$name" -f value="$value" --silent
  fi
}

SQL_FQDN=$(az sql server show -g "$RG" -n "$PREFIX-sql" --query fullyQualifiedDomainName -o tsv)
PANTRY_HOST=$(az containerapp show -g "$RG" -n "$PREFIX-pantry" --query properties.configuration.ingress.fqdn -o tsv)
CATALOG_HOST=$(az containerapp show -g "$RG" -n "$PREFIX-catalog" --query properties.configuration.ingress.fqdn -o tsv)
UI_ORIGIN=$(az storage account show -g "$RG" -n "$STORAGE_ACCOUNT" --query primaryEndpoints.web -o tsv)
CLIENT_ID=$(az identity show -g "$RG" -n "$PREFIX-github" --query clientId -o tsv)
TENANT_ID=$(az identity show -g "$RG" -n "$PREFIX-github" --query tenantId -o tsv)
set_variable AZURE_RG "$RG"
set_variable PREFIX "$PREFIX"
set_variable SQL_SERVER_FQDN "$SQL_FQDN"
set_variable PANTRY_URL "https://$PANTRY_HOST"
set_variable CATALOG_URL "https://$CATALOG_HOST"
set_variable UI_ORIGIN "${UI_ORIGIN%/}"
set_variable STORAGE_ACCOUNT "$STORAGE_ACCOUNT"
set_variable AZURE_CLIENT_ID "$CLIENT_ID"
set_variable AZURE_TENANT_ID "$TENANT_ID"
set_variable AZURE_SUBSCRIPTION_ID "$SUBSCRIPTION"
set_variable OFF_USER_AGENT "$OFF_USER_AGENT"
set_variable ENABLE_FEATURE_SMOKE_TESTS false
echo 'GitHub deployment secrets and variables configured.'
