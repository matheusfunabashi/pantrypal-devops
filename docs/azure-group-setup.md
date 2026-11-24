# Group 8 deployment

The group deploys in IE's subscription, in `rg-sdd-3b-g8`. Use Bash from the repository root. The Azure CLI, its Container Apps extension, Python 3 and GitHub CLI are used below. The database bootstrap also uses Docker or Microsoft's native Go sqlcmd.

## Provisioning record, 19 November

| Component | Verified in the IE resource group |
| --- | --- |
| Container Apps | `sdd-3b-g8-pantry` and `sdd-3b-g8-catalog` were provisioned on Consumption, with 0–1 replicas. Both ran the bootstrap image until the first GitHub deployment. |
| Database | `sdd-3b-g8-sql` with separate Pantry and Catalog serverless databases, each 0.5–1 vCore, 2 GB, 15-minute auto-pause and local backup redundancy. Each service user authenticated and had db_owner in its database. The only remaining firewall rule was `AllowAzureServices`. |
| Frontend | Azure assigned `orange-plant-0e3501f03.5.azurestaticapps.net` to the Free tier site `sdd-3b-g8-ui`. CD uploaded the application during the cutover. |
| Logging | `sdd-3b-g8-env` uses the group Log Analytics workspace `sdd-3b-g8-logs`. |
| GitHub identity | The identity was absent at the 19 November check. See the 22 November update below. |

The final Azure Bicep `what-if` completed on 19 November. It returned six `NoChange` results (environment, workspace, SQL server, both databases and the SQL firewall rule) and four `Ignore` results (the two CD-owned apps, the already provisioned Static Web App and SQL's system master database). It listed zero creates, modifications or deletions. The two app scaling limits and the Free hosting tier were checked directly.

## Sign in and provision

```bash
source infra/group8.env
az login --tenant 5ca2bc70-353c-4d1f-b7d7-7f2b2259df68
az account set --subscription "$SUBSCRIPTION"
az group show -g "$RG" --query '{name:name,location:location}' -o table
```

For a fresh installation, create the group SQL credentials once. On a workstation with the existing installation, use the previously generated file or restore its values from the team's password manager. Keep this file private.

```bash
python3 infra/generate-local-secrets.py --group8    # fresh installation only
source .env.azure.group8
bash infra/setup.sh
bash infra/create-db-users.sh
```

The CLI creates a Log Analytics workspace, a Container Apps environment, two Consumption apps with 0–1 replicas, a SQL server with two serverless databases (0.5–1 vCore, 15-minute auto-pause), and one Free Static Web App. It skips resources already present. Each service receives a contained user in its own database. The DB script removes its temporary client-IP firewall rule on exit. To use native Go sqlcmd, set `GO_SQLCMD` to its executable before running the DB step. Both SQL paths request encryption with certificate validation. If Azure SQL reports a different client IP from the HTTP lookup, set `SQL_CLIENT_IP` to the exact address in the SQL error and rerun the DB-user step. If the network rotates through a small known egress range, set `SQL_CLIENT_IP` and `SQL_CLIENT_END_IP` to its observed bounds.

For the Bicep option, source the same variables and SQL credentials. Run `bash infra/deploy.sh what-if` to preview and `bash infra/deploy.sh create` for initial provisioning, then run the same DB-user step. The wrapper uses incremental mode and bootstraps only missing apps. Bicep creates the Static Web App once to preserve its deployment authentication and hosting configuration on subsequent runs. The template was compiled with Bicep 0.49.2. Once created, CD owns the apps' images, environment, secrets and ingress ports. Inspect the preview before applying any change to an existing group. A SQL administrator password is a secure parameter. Azure can report a change for write-only properties.

## Connect GitHub Actions

**Verified on 22 November.** Azure recorded successful writes for `sdd-3b-g8-github` on 21 November at 08:41 and 08:51 UTC. Its client ID is `48045f02-69b2-4f32-8768-650ad1222fd3`. Its principal has Contributor directly on the group resource group. The team created the federated credential `github-main` using the IE subscription and `rg-sdd-3b-g8` explicitly. The read-only preflight matched the issuer, immutable main-branch subject and audience below and returned the expected client ID. The 23 November [cutover CD run](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/45186481843) completed the GitHub token exchange and deployed both services and the frontend.

IE supplies the user-assigned managed identity `sdd-3b-g8-github` with Contributor access to this group's resource group. When configuring the repository for this environment, verify the credential and apply the group settings:

```bash
source .env.azure.group8
bash infra/check-group-identity.sh
bash infra/configure-github.sh
```

The check expects the GitHub issuer `https://token.actions.githubusercontent.com`, audience `api://AzureADTokenExchange`, and subject `repo:matheusfunabashi@208869383/pantrypal-devops@1450359550:ref:refs/heads/main`. If the identity is absent or the subject differs, check the subscription and resource-group arguments first, then inspect the credential on the named group identity. The personal identity script belongs to the historical deployment.

The configuration script reads the client ID, tenant, ingress hostnames, SQL host and UI origin from Azure. It writes separate `IE_` repository variables and two `IE_` database password secrets. The existing repository `OFF_USER_AGENT` identifies the project to Open Food Facts. GitHub retains the personal deployment settings until the group cutover has been accepted. Stage these settings before merging. The workflow runs on pushes to main, including a reviewed merge. To test just the OIDC login and group read after the workflow is on main, open **Actions → CD → Run workflow**, select **main**, and enable **Verify the IE identity and resource group access only**.

On a full run, the pipeline gates publishing on CI and the identity check, deploys both GHCR images tagged with the main commit, applies startup migrations, and supplies the Static Web App origin to both APIs' CORS configuration. The UI job generates config.js and uses the group's identity to obtain a masked Static Web Apps deployment token for that job. After both health endpoints return HTTP 200, the smoke job looks up a known barcode and reads pantry inventory, restock needs and recipe availability. It expects HTTP 200 for each request, then verifies that the public frontend's config.js points to both deployed APIs. [Smoke job after PR #83](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/45292544544/job/138107108254)

## Cutover result, 23 November

All 13 jobs passed for main commit `aeb1ac5a6678691df2f10af8c7d58020dfe7bbe4`. Both APIs received 100% of traffic on revisions using that image tag. The public frontend served the IE API addresses, and the group workspace received request logs from both services. See the [cutover CD run](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/45186481843).

Desktop Chromium verified cached lookup, errors, add, quantity changes after reload, removal and restock. The temporary item and target were cleared. Sami reported that the physical-phone check passed. The personal frontend remained available with its own API addresses.

## Verify the group cutover

Get the assigned public URL and image tags from Azure:

```bash
source infra/group8.env
az staticwebapp show --subscription "$SUBSCRIPTION" -g "$RG" -n "$PREFIX-ui" --query defaultHostname -o tsv
for service in pantry catalog; do
  az containerapp revision list --subscription "$SUBSCRIPTION" -g "$RG" -n "$PREFIX-$service" \
    --query '[?properties.active].{revision:name,weight:properties.trafficWeight,image:properties.template.containers[0].image}' -o table
done
```

Save the CD run and SHA. From the new URL on a laptop and a physical phone, check health, product lookup twice (second result cached), unknown and malformed codes, add quantity two, add again (four on the same row), increase/decrease and reload, then remove and reload. Use a barcode initially absent from the pantry so the test affects only its own item. Confirm both images match the deployed SHA and query request lines from both services in the group workspace. Record the device, time, run, SHA, results and any failed step in the integration issue. Update the README live link after verification. [Sprint integration evidence](https://github.com/matheusfunabashi/pantrypal-devops/issues/45)
