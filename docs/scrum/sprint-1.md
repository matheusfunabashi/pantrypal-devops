# Sprint 1 (11 to 18 November 2026)

Scrum Master: Sami Droubi (@Thecoolss)

## Sprint Goal

PantryPal is deployed to Azure by the pipeline, and a user can look up a product by barcode and manage it in their pantry at the public URL.

The deployment comes first. Getting the skeleton onto Azure through CI/CD is the main milestone of the project, so we don't start feature work at its expense. If the deployment gets stuck on anything other than missing Azure credentials, the others help before carrying on with features.

## Roles

| Member | Scrum role | Main work this sprint |
| --- | --- | --- |
| Gustave (@gustaveems) | Product Owner | CI, Catalog Service, product lookup UI |
| Sami Droubi (@Thecoolss) | Scrum Master | Azure setup, CD pipeline, deploying the UI |
| Matheus Funabashi (@matheusfunabashi) | Developer | Pantry Service, pantry UI, branch protection |

Everyone writes code. Matheus keeps `docker-compose.yml` and the repository settings because he is the repository admin. Sami owns `.github/workflows/cd.yml` and `infra/`, and Gustave owns `.github/workflows/ci.yml`.

## What we picked for this sprint

**Must** (the sprint fails without these):

- S1-01 CI: lint, format check, coverage gate, reusable workflow (#27, Gustave)
- S1-02 Azure resources created by a script (#28, Sami)
- S1-03 Database users on Azure SQL (Sami)
- S1-04 CD: deploy on merge to `main` (Sami)
- S1-05 Frontend on Static Web Apps (Sami)
- S1-07 Pantry database and first migration (Matheus)
- S1-08 Catalog database and first migration (Gustave)
- S1-09 Look up a product by barcode, US-01 (#3, Gustave)
- S1-10a Add a product and view the pantry, US-02 and US-03 (#4, #5, Matheus)
- S1-11 Pantry calls Catalog with a timeout (Matheus)

**Should:**

- S1-10b Update quantity and delete an item, US-04 and US-05 (#6, #7, Matheus)
- S1-12 Product lookup UI (Gustave)
- S1-13 Pantry UI (Matheus)
- S1-06 Branch protection requires CI (Matheus)
- S1-15 Sprint 1 documentation (everyone)
- S1-16 Integration test on Azure (Sami leads, everyone)

**Could:**

- S1-14 Smoke test after each deploy (Sami)
- S1-17 Bicep for the Azure resources (Sami)

US-06 (check before you buy) waits for Sprint 2. US-07 and US-08 stay optional.

If on Monday 16 November the Must items aren't all deployed, we stop the Should and Could items and finish the Must ones. Whatever isn't finished goes back to the backlog.

## Decisions we made during planning

**Database access.** Both services use SQLAlchemy 2.0.54 with the `pymssql` driver (`mssql+pymssql://`), the same setup that worked in Assignment 2. `pymssql` needs no ODBC driver in the image. We pin SQLAlchemy to 2.0.54 because 2.1.x broke tests in Assignment 2.

**Migrations.** Each service has its own Alembic migrations. The container runs `alembic upgrade head` when it starts, before the API, and retries for a while if the database isn't reachable yet. An auto-paused Azure SQL database refuses connections for up to about a minute while it resumes.

**Lint and format.** `ruff check` and `ruff format --check`, with one shared `ruff.toml`.

**Azure setup.** We start with an Azure CLI script in `infra/` that creates every resource, so nothing is set up by hand in the portal. If there is time left, we describe the same resources in Bicep.

**Images.** The pipeline pushes both images to GitHub Container Registry, tagged with the commit SHA. The packages are public, so Container Apps can pull them without a registry password.

**Configuration.** The Pantry Service finds the Catalog Service through `CATALOG_URL`. On Azure, the pipeline writes `frontend/config.js` with the two service URLs before uploading the UI. The `config.js` in the repository keeps the localhost URLs for local development.

**Open Food Facts.** The Catalog Service uses API v3, because v2 is marked as deprecated. Every request sends a User-Agent with the app name and a contact email, as Open Food Facts asks, and has a 5 second timeout. The email comes from configuration, not the code.

**Health checks.** `/health` doesn't query the database. If a migration fails, the container doesn't start, so the health check after a deploy still catches database problems. Querying the database would also wake it from auto-pause on every check.

**API contracts.** We agreed the endpoints and error responses before splitting the work, so the Pantry and Catalog work can happen in parallel:

- `GET /products/{barcode}` on Catalog returns the product (`200`), `404` if Open Food Facts doesn't know it, `422` if the barcode isn't 8 to 14 digits, and `503` if Open Food Facts is down and there is no cached copy.
- Pantry has `GET /pantry`, `GET /pantry/{id}`, `POST /pantry`, `PUT /pantry/{id}` and `DELETE /pantry/{id}`. Quantities are whole numbers from 1 to 999. Adding a barcode that is already in the pantry increases its quantity and doesn't call Catalog, so it still works when Catalog is down. Adding a new barcode returns `503` with a clear message if Catalog is down or too slow.

**Azure credentials.** We are waiting for the group's service principal and resource group. Until they arrive, Sami prepares everything that doesn't need Azure: pushing images to GitHub Container Registry, the CD workflow and the setup scripts. If the group isn't approved, or we still have no answer by the end of Friday 13 November, one of us hosts the resources on a personal Azure subscription, as the professor allowed. We keep the same resource names and limits.

## Sprint Review (18 November)

To fill in after the meeting: who was there, what we showed, which items are done and which go back to the backlog, and the Product Owner's decision on each item.

## Retrospective (18 November)

To fill in after the meeting: what went well, what didn't, and what we agree to change in Sprint 2, with a name next to each agreement.
