#!/usr/bin/env bash
set -euo pipefail

if [[ "${RG:-}" == rg-sdd-3b-g8 ]]; then
  echo 'IE provisions the group identity. Use bash infra/check-group-identity.sh.' >&2
  exit 1
fi
: "${SUBSCRIPTION:?}" "${RG:?}" "${PREFIX:?}" "${LOCATION:?}" "${STORAGE_ACCOUNT:?}"
REPO="${REPO:-matheusfunabashi/pantrypal-devops}"
# Match the ID-bearing subject observed in GitHub Actions' Azure login output.
# Override OIDC_SUBJECT with the exact logged subject if the repository uses a
# different OIDC subject template. Resolve it before making any Azure changes.
if [[ -z "${OIDC_SUBJECT:-}" ]]; then
  OIDC_SUBJECT=$(gh api "repos/$REPO" --jq \
    '"repo:\(.owner.login)@\(.owner.id)/\(.name)@\(.id):ref:refs/heads/main"')
fi
: "${OIDC_SUBJECT:?GitHub OIDC subject must not be empty}"
IDENTITY_NAME="$PREFIX-github"
GROUP_SCOPE="/subscriptions/$SUBSCRIPTION/resourceGroups/$RG"
STORAGE_SCOPE="$GROUP_SCOPE/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT"
az account set --subscription "$SUBSCRIPTION"
if ! az identity show -g "$RG" -n "$IDENTITY_NAME" -o none 2>/dev/null; then
  az identity create -g "$RG" -n "$IDENTITY_NAME" -l "$LOCATION" -o none
fi
if az identity federated-credential show -g "$RG" --identity-name "$IDENTITY_NAME" \
    -n github-main -o none 2>/dev/null; then
  CREDENTIAL_ACTION=update
else
  CREDENTIAL_ACTION=create
fi
az identity federated-credential "$CREDENTIAL_ACTION" -g "$RG" --identity-name "$IDENTITY_NAME" \
  -n github-main --issuer https://token.actions.githubusercontent.com \
  --subject "$OIDC_SUBJECT" --audiences api://AzureADTokenExchange -o none
PRINCIPAL_ID=$(az identity show -g "$RG" -n "$IDENTITY_NAME" --query principalId -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role Contributor --scope "$GROUP_SCOPE" -o none
az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role 'Storage Blob Data Contributor' \
  --scope "$STORAGE_SCOPE" -o none
az identity show -g "$RG" -n "$IDENTITY_NAME" \
  --query '{AZURE_CLIENT_ID:clientId,AZURE_TENANT_ID:tenantId}' -o json
printf 'AZURE_SUBSCRIPTION_ID=%s\n' "$SUBSCRIPTION"
