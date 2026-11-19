# Architecture decisions

## 1. Separate the pantry inventory from the product catalog
Date: 2026-11-17
Status: Decided

**Context.** The group brief requires two services with separate databases. A slow product lookup should still let someone manage groceries they already own.

**Decision.** Use two Python FastAPI services with HTTP routes, core logic, database access and external clients in separate modules. Pantry calls Catalog for a new barcode with a bounded timeout and stores a snapshot with the item.

**Alternatives considered.** A shared database would couple schema changes across services. Routing every lookup through Pantry would make Catalog depend on Pantry’s availability.

**Consequences.** Existing inventory operations use Pantry alone, and tests can substitute the external client. A new item depends on Catalog, so the API maps missing products to 404 and unavailability to 503.

## 2. Persist pantry snapshots and cache product details
Date: 2026-11-17
Status: Decided

**Context.** Open Food Facts can time out, and a serverless SQL database can take time to resume. The local stack also needs to reproduce the production schema.

**Decision.** Use SQL Server locally and one serverless Azure SQL database per service, with SQLAlchemy, pymssql and versioned Alembic migrations on startup. Catalog caches successful lookups for seven days by default and serves an existing stale row during an upstream outage.

**Alternatives considered.** Fetching fresh details for every pantry view would make the view depend on the network. Creating tables directly on startup would leave existing installations without a versioned upgrade path.

**Consequences.** Stored snapshots and cached results keep reads available but may show older product details. Bounded startup retries cover database resume, and a failed migration prevents the service from starting.

## 3. Deploy through GitHub Actions to the personal Azure resource group
Date: 2026-11-14
Status: Decided

**Context.** Sprint 1 needed a working deployment before the institutional credentials were available. The personal subscription’s allowed regions excluded Static Web Apps, and the professor authorized personal hosting.

**Decision.** Script two Consumption Container Apps scaling from zero to one, two auto-pausing SQL databases, a Storage static website and Log Analytics in Germany West Central. Gate CD on CI, publish SHA-tagged GHCR images, use OIDC with a managed identity scoped to the project, pass database passwords through Container App secrets, and check both health endpoints after deployment.

**Alternatives considered.** The group Static Web App depends on IE’s deployment identity. Azure CLI could provision the personal stack in time for Sprint 1, so the team deferred the optional Bicep version.

**Consequences.** Compute can scale down between requests, while cold starts require a five-minute health-check window and storage and logs can still incur charges. The Storage website provides the public origin used by both APIs.

On 19 November the professor advised continuing on this deployment while IE provisions its GitHub identity. [First successful automated deployment](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/43915006087) · [Deployment including update and removal](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/44541649429)

## 4. Configure the static browser UI at deployment
Date: 2026-11-19
Status: Decided

**Context.** Local development and Azure use different service addresses. Each API needs the exact browser origin for CORS.

**Decision.** Serve plain HTML, CSS and JavaScript, with CD writing both public HTTPS endpoints into frontend/config.js. Render product text with textContent and accept HTTP(S) image URLs.

**Alternatives considered.** Hard-coded URLs would require a source change for every deployment target. A frontend build tool would add a dependency to substitute two public settings.

**Consequences.** The same frontend works locally and on Azure, provided CD coordinates its URLs with backend CORS. Database credentials stay in the backend, and the server-side Pantry client uses CATALOG_URL independently of browser configuration.
