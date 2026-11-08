# Definition of Done

A backlog item is **Done** only when every point below is true. It applies to every item, in every sprint.

1. **Acceptance criteria met.** Every acceptance criterion on the story has been checked.
2. **Tests.** New or changed logic has automated tests, and all tests pass.
3. **Code quality.** Formatting and lint checks pass.
4. **Reviewed.** The change reached `main` through a pull request approved by another team member. No direct pushes to `main`.
5. **CI green.** The CI workflow passed on the pull request.
6. **Merged** into `main`.
7. **Deployed.** The CD pipeline deployed the change to Azure, and `/health` returns 200 after the deploy.
8. **No secrets.** No credentials, keys or passwords in the code, the images or the Git history.
9. **Docs updated** where the change affects them (README, `docs/decisions.md`, `docs/data-model.md`, `AI_USAGE.md`).

## Sprint 0 note
Azure deployment is not available until Sprint 1. In Sprint 0, point 7 is replaced by:
**`docker compose up --build` starts the system from a clean clone, and every `/health` returns 200.**