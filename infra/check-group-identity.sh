#!/usr/bin/env bash
# Read-only. Print the client ID only after verifying main-branch federation.
set -euo pipefail
source "$(dirname "$0")/group8.env"
identity="$PREFIX-github"
subject='repo:matheusfunabashi@208869383/pantrypal-devops@1450359550:ref:refs/heads/main'
scope=(--subscription "$SUBSCRIPTION" --resource-group "$RG")
matches=$(az identity federated-credential list "${scope[@]}" --identity-name "$identity" \
  --query "length([?issuer=='https://token.actions.githubusercontent.com' && subject=='$subject' && contains(audiences, 'api://AzureADTokenExchange')])" -o tsv)
if [[ "$matches" == 0 ]]; then
  echo "No matching GitHub main-branch federation on $identity. Expected subject: $subject" >&2
  exit 1
fi
az identity show "${scope[@]}" -n "$identity" --query clientId -o tsv
