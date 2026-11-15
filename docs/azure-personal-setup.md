# Personal Azure setup

PantryPal uses @Thecoolss's Azure for Students subscription and a dedicated
resource group. Unrelated personal-project resources must remain untouched.

## Hosting decision

The subscription policy `sys.regionrestriction` permits Switzerland North,
Germany West Central, Belgium Central, Austria East, and Norway East.
None is a supported Azure Static Web Apps region. West Europe provisioning
attempts were rejected before project resources were created.

Because the team deploys to a personal account rather than the group's institution
account, the team was asked to host the frontend on Azure Storage static website
hosting for the time being. It runs in Germany West Central and uses the built-in
HTTPS endpoint. If the group's institution account becomes available, the UI moves
to Static Web Apps there. The two backend services and their separate SQL databases
are unchanged.

The university tenant also blocks application registrations. GitHub authenticates
through OIDC and a user-assigned managed identity, with trust restricted to
`repo:matheusfunabashi/pantrypal-devops:ref:refs/heads/main`.
There is no Azure client secret. The identity has Contributor on this project's
resource group and Storage Blob Data Contributor on this project's UI account.

## Configuration

Run in WSL Bash, from the repository root:

```bash
export SUBSCRIPTION='<subscription-id>'
export RG='rg-sdd-BCSAI-g3B-personal'
export PREFIX='sdd-bcsai-g3b-personal'
export LOCATION='germanywestcentral'
export STORAGE_ACCOUNT='sddbcsaig3bui1ffa64df'
export REPO='matheusfunabashi/pantrypal-devops'
az login
az account set --subscription "$SUBSCRIPTION"
```

Resource names are lowercase for SQL server and Container App compatibility;
the existing resource group retains its capitalization. Storage names are
globally unique, contain no hyphens, and have a maximum length of 24 characters.

The existing monthly budget is 30 in the subscription's billing currency, with
email notifications to the hosting member.
It is an alert, not a spending cap. SQL storage and logs can still cost money
while application compute is idle.

## Reproduce initial provisioning

```bash
az extension add --name containerapp --upgrade
for provider in Microsoft.App Microsoft.OperationalInsights Microsoft.Sql Microsoft.Storage Microsoft.ManagedIdentity; do
  az provider register --namespace "$provider" --wait
done
az group show -n "$RG" -o table
git check-ignore .env.azure
python3 infra/generate-local-secrets.py
source .env.azure
bash infra/setup.sh
export SQL_SERVER="$PREFIX-sql"
export PANTRY_DB_NAME="$PREFIX-pantry-db"
export CATALOG_DB_NAME="$PREFIX-catalog-db"
bash infra/create-db-users.sh
bash infra/setup-github-identity.sh
```

The password generator creates `.env.azure` once, refuses to overwrite it, and
sets permissions to 600. Never print it in shared logs or commit it. Transfer its
three SQL passwords to your password manager. On subsequent runs, skip generation
and source the existing file. The SQL admin password stays local; only application
passwords are stored in GitHub Actions.

Docker must be running for database-user creation. The script temporarily allows
your public IP, uses encrypted SQL with certificate validation, and removes its
firewall rule on exit. It creates contained users owning their own database only.

Setup is resumable and skips existing resources; it does not reconcile drift.
It creates bootstrap Container Apps on port 80. The real service deployment
sets port 8000 and supplies DB credentials before migration-enabled images run.

## GitHub Actions configuration

After provisioning and identity setup, configure all secrets and variables with:

```bash
source .env.azure
export OFF_USER_AGENT='PantryPal/0.1 (<contact-email>)'
bash infra/configure-github.sh
```

This uses the existing WSL GitHub login. Feature smoke tests are initially disabled.

Store these secrets by piping values without printing them:

```bash
printf '%s' "$PANTRY_DB_APP_PASSWORD" | gh secret set PANTRY_DB_APP_PASSWORD --repo "$REPO"
printf '%s' "$CATALOG_DB_APP_PASSWORD" | gh secret set CATALOG_DB_APP_PASSWORD --repo "$REPO"
```

Set the following repository Actions variables through Settings or the API:

| Variable | Value |
| --- | --- |
| AZURE_RG | rg-sdd-BCSAI-g3B-personal |
| PREFIX | sdd-bcsai-g3b-personal |
| AZURE_SUBSCRIPTION_ID | selected subscription ID above |
| AZURE_CLIENT_ID | managed identity clientId from setup-github-identity.sh |
| AZURE_TENANT_ID | managed identity tenantId from setup-github-identity.sh |
| SQL_SERVER_FQDN | SQL server fullyQualifiedDomainName |
| PANTRY_URL | HTTPS Pantry Container App ingress hostname |
| CATALOG_URL | HTTPS Catalog Container App ingress hostname |
| UI_ORIGIN | Storage primaryEndpoints.web, without trailing slash |
| STORAGE_ACCOUNT | sddbcsaig3bui1ffa64df |
| OFF_USER_AGENT | PantryPal/0.1 (<contact-email>) |
| ENABLE_FEATURE_SMOKE_TESTS | false until both feature endpoints exist |

The older installed gh CLI lacks `gh variable`; use `gh api` instead:

```bash
set_variable() {
  local name="$1" value="$2"
  if gh api "repos/$REPO/actions/variables/$name" --silent 2>/dev/null; then
    gh api --method PATCH "repos/$REPO/actions/variables/$name" -f name="$name" -f value="$value" --silent
  else
    gh api --method POST "repos/$REPO/actions/variables" -f name="$name" -f value="$value" --silent
  fi
}
```

Allow time for Azure role assignments to propagate. GitHub deployment jobs need
`id-token: write` and `contents: read`; PR branches have no matching Azure
federated credential. No AZURE_CREDENTIALS or Static Web Apps token is needed.

## Deployment and verification

Make both GHCR packages public. Review and merge the deployment PR with Matheus's
approval and green CI. CD publishes SHA-tagged images, configures services, writes
frontend/config.js, uploads only frontend files to Storage's `$web` container
using OIDC, and checks both /health endpoints concurrently for up to five minutes.
The frontend files are public; secrets must never be placed in that directory.

Until the deployment workflow is merged, the initial bootstrap may be configured
from the same current main SHA. This verifies initial infrastructure only and
does not count as proof of automated delivery through a reviewed merge.

Open UI_ORIGIN and confirm both services show Healthy. Check CORS_ORIGINS equals
UI_ORIGIN exactly, with no trailing slash. Verify deployed image SHA tags, replicas
0–1, SQL serverless capacity and auto-pause, migration logs after database PRs land,
and request logs in the Container Apps environment's Log Analytics workspace.

Enable feature smoke tests only after /products/{barcode} and /pantry are deployed.
Record the actual deployment result, hosting choice, and identity choice in
docs/scrum/sprint-1.md and ADR-3. Add the live URL to README after verification.

## Password rotation

Rerun create-db-users.sh with new passwords, update the matching GitHub secrets,
and rerun CD from main. Updating GitHub alone does not rotate SQL users.
Coordinate rotation because existing revisions temporarily retain old credentials.

## Verified initial deployment (14 November 2026)

- UI: https://sddbcsaig3bui1ffa64df.z1.web.core.windows.net
- Both APIs run main SHA `470f615bd044d4361daea5a75dfcf4320651bb63`.
- Public UI, production config.js, both /health responses, allowed-origin CORS,
  and rejection of an unrelated browser origin were verified.
- Container Apps use 0–1 replicas. SQL uses 0.5–1 vCore, 15-minute auto-pause,
  2 GB per database, and locally redundant backups.
- Both contained database users were created; the temporary firewall rule was
  removed. Only the AllowAzureServices rule remains.
- GitHub has the two SQL application password secrets and twelve deployment
  variables. Deployment authentication uses OIDC; no Azure client secret remains.
- Log Analytics console table and columns were verified; the saved request query
  is in docs/monitoring/requests.kql. Requests from both services were confirmed
  in the workspace after deployment.
- The existing monthly budget of 30 applies to the entire subscription, including
  the unrelated project; notifications go to the hosting member.

This was an initial setup deployment, not a GitHub CD run. The local CD changes
remain uncommitted and require a reviewed PR before automated delivery is proven.
Current main provides the health-page skeleton; database migrations and product
features remain dependent on the team's feature PRs.
