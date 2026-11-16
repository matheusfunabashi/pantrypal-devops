#!/usr/bin/env bash
set -euo pipefail

: "${SUBSCRIPTION:?}" "${RG:?}" "${PREFIX:?}" "${LOCATION:?}" "${STORAGE_ACCOUNT:?}"
REPO="${REPO:-matheusfunabashi/pantrypal-devops}"
IDENTITY_NAME="$PREFIX-github"
GROUP_SCOPE="/subscriptions/$SUBSCRIPTION/resourceGroups/$RG"
STORAGE_SCOPE="$GROUP_SCOPE/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT"
az account set --subscription "$SUBSCRIPTION"
if ! az identity show -g "$RG" -n "$IDENTITY_NAME" -o none 2>/dev/null; then
  az identity create -g "$RG" -n "$IDENTITY_NAME" -l "$LOCATION" -o none
fi
if ! az identity federated-credential show -g "$RG" --identity-name "$IDENTITY_NAME" \
    -n github-main -o none 2>/dev/null; then
  az identity federated-credential create -g "$RG" --identity-name "$IDENTITY_NAME" \
    -n github-main --issuer https://token.actions.githubusercontent.com \
    --subject "repo:$REPO:ref:refs/heads/main" --audiences api://AzureADTokenExchange -o none
fi
PRINCIPAL_ID=$(az identity show -g "$RG" -n "$IDENTITY_NAME" --query principalId -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role Contributor --scope "$GROUP_SCOPE" -o none
az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role 'Storage Blob Data Contributor' \
  --scope "$STORAGE_SCOPE" -o none
az identity show -g "$RG" -n "$IDENTITY_NAME" \
  --query '{AZURE_CLIENT_ID:clientId,AZURE_TENANT_ID:tenantId}' -o json
printf 'AZURE_SUBSCRIPTION_ID=%s\n' "$SUBSCRIPTION"
