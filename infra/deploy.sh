#!/usr/bin/env bash
# Use the same bootstrap shape as setup.sh. Incremental mode preserves apps already owned by CD.
set -euo pipefail
directory=$(cd "$(dirname "$0")" && pwd)
source "$directory/group8.env"
case "${1:-what-if}" in
  what-if|create) operation=${1:-what-if} ;;
  *) echo 'Usage: bash infra/deploy.sh [what-if|create]' >&2; exit 2 ;;
esac
: "${SQL_ADMIN_USER:?source .env.azure.group8}" "${SQL_ADMIN_PASSWORD:?source .env.azure.group8}"
existing=$(az resource list --subscription "$SUBSCRIPTION" -g "$RG" --resource-type Microsoft.App/containerApps --query '[].name' -o json)
workspaceId=$(az monitor log-analytics workspace list --subscription "$SUBSCRIPTION" -g "$RG" \
  --query "[?name=='$PREFIX-logs'].customerId | [0]" -o tsv)
# The admin password is in a secure ARM parameter and never appears on the command line.
params=$(mktemp)
trap 'rm -f "$params"' EXIT
python3 - "$existing" "$workspaceId" > "$params" <<'PY'
import json, os, sys
env = os.environ
present = json.loads(sys.argv[1])
prefix = env["PREFIX"]
values = {
    "prefix": prefix, "location": env["LOCATION"], "existingWorkspaceCustomerId": sys.argv[2],
    "swaLocation": env.get("SWA_LOCATION", env["LOCATION"]),
    "sqlLocation": env.get("SQL_LOCATION", env["LOCATION"]),
    "sqlAdminLogin": env["SQL_ADMIN_USER"], "sqlAdminPassword": env["SQL_ADMIN_PASSWORD"],
    "bootstrapApps": [s for s in ("pantry", "catalog") if f"{prefix}-{s}" not in present],
}
json.dump({"parameters": {k: {"value": v} for k, v in values.items()}}, sys.stdout)
PY
if [[ "$operation" == what-if ]]; then
  summary=(--no-pretty-print --query 'changes[].{resource:resourceId,change:changeType,properties:delta[].path}' -o json)
else
  summary=(--query properties.provisioningState -o tsv)
fi
az deployment group "$operation" --subscription "$SUBSCRIPTION" --resource-group "$RG" \
  --name group8-bootstrap --mode Incremental --template-file "$directory/main.bicep" \
  --parameters "@$params" "${summary[@]}"
