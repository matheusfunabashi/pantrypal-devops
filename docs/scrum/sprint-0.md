# Sprint 0 (4 to 10 November 2026)

Scrum Master: Matheus Funabashi

## Sprint Goal

By the end of Sprint 0 we want a working skeleton of PantryPal. That means a protected repo with a workflow everyone follows, the pantry and catalog services running with a health endpoint, a simple frontend page, and the whole thing starting locally with docker compose up --build. Nothing user-facing yet. The point is to have a solid base so Sprint 1 can go straight into features and deployment.

## Roles

Sami Droubi (Thecoolss) is our Product Owner this sprint, I'm the Scrum Master, and Gustave (gustaveems) is the developer. We all write code anyway, and the roles rotate next sprint.

## What we picked for this sprint

We took the setup items from the board. I handled the repo setup (#11), the Scrum docs including the Definition of Done (#13) and the Docker Compose file (#17). Sami wrote the product scope and backlog (#12) and built the static frontend (#16). Gustave built both service skeletons, pantry and catalog (#14 and #15). Sami and I share the final integration check and the review (#18). A basic CI workflow was a stretch goal, and Gustave has a PR open for it (#23).

The user stories (US-01 to US-08) stay in the backlog for Sprint 1 and 2.

## Decisions we made during planning

We went with two separate FastAPI services, each with its own SQL Server database. The pantry service handles the user's pantry items, and the catalog service looks products up on Open Food Facts and caches the results. The frontend is a static page served by nginx. Locally, pantry runs on port 8000, catalog on 8001 and the frontend on 8080. Both services have a /health endpoint that returns 200 and says which service it is, so the frontend and compose can check they're up.

All configuration comes from environment variables. The real .env file is never committed. We only keep a .env.example with the variable names and empty values, and passwords are shared between us privately. If a password ever ends up somewhere public, we change it straight away.

The services don't connect to the database as the sa admin user. A small init job runs before each service, creates its database and gives it its own login (pantry_user and catalog_user), and that login only has rights on its own database. So the services themselves never create databases.

For the Docker images we pin the exact base image version, run as a non-root user and only copy the files the app needs. Each service logs one line per request with the method, path, status and how long it took.

Every change goes through a branch and a pull request that someone else approves. Nobody pushes to main directly, and main is protected so it can't happen by accident. To avoid stepping on each other, Sami mostly works in the frontend and product docs, I work on compose, the env example, the db scripts and the Scrum docs, and Gustave works in the two service folders.

Our Definition of Done is in definition-of-done.md. Since we don't have Azure yet, "deployed" for this sprint means the stack starts from a fresh clone with docker compose and every health check returns 200.

## Sprint Review (10 November)

To fill in after the meeting: who was there, what we showed, what's done and what moves to Sprint 1.

Matheus (me), Gustave, and Sami had a meeting and made sure the progress so far matched the Definition of Done established. We tested the init jobs for pantry and catalogue alongside the databases and logs for each request.

## Retrospective (10 November)

To fill in after the meeting: what went well, what didn't, and what we agree to change (with a name next to each one).

Matheus: What really went well was making a table with divided jobs for each member that followed a chronological order so that we wouldn't be stepping on each other's work. 

Gustave: What needs to improve is the communication while working on the files, many occasions of misaligned reference names. 

Sami: We agree to communicate more during and after completing a section of the work so that less errors occur.

# Next sprint

Roles: Gustave (Product Owner), Sami (Scrum Master), Matheus (developer).

Goal for sprint 1: Build features and deploy the project
