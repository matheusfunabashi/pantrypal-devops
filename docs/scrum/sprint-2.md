# Sprint 2 (19 to 24 November 2026)

Scrum Master: Gustave (@gustaveems)

## Sprint Goal

At the shop, scan a product, check its Nutri-Score, compare it with another product and see how many are already at home. At home, see what needs restocking, which meals the pantry can make, and a Nutri-Score overview of the pantry. Demonstrate the released app, a measured SLO and graceful behaviour when a dependency fails.

## Roles

| Member | Scrum role | Main work |
| --- | --- | --- |
| Matheus Funabashi (@matheusfunabashi) | Product Owner | "What can I cook?", pantry Nutri-Score overview, Catalog-down evidence, release tags |
| Gustave (@gustaveems) | Scrum Master | Check Before You Buy, already at home, compare two products, dashboard and SLO |
| Sami Droubi (@Thecoolss) | Developer | Restock list, camera scanning, delivery evidence |

Everyone builds. Each feature has one owner, who writes its backend, UI, tests and docs.

## What we picked for this sprint

**Must:**

- S2-01 Check Before You Buy, US-06 (Gustave)
- S2-03 Already at home (Gustave)
- S2-04 Restock list (Sami)
- S2-05 What can I cook? (Matheus)
- S2-06 Dashboard and SLO (Gustave)
- S2-07a Catalog down (Matheus), S2-07b Delivery (Sami), S2-07c Open Food Facts failing (Gustave)

**Should:**

- S2-02 Camera barcode scanning, US-07 (Sami)
- S2-09 Compare two products (Gustave)
- S2-10 Pantry Nutri-Score overview (Matheus)
- S2-08 Documentation (each member for their own part)

**Could:**

- S2-11 Release tags (Matheus)
- S2-12 Move to the group's IE subscription (Sami), only if the group's GitHub identity arrives by Saturday 21 November

US-08 (expiry dates) stays in the backlog.

## Decisions we made during planning

**Azure.** We stay on the personal deployment until the group's GitHub managed identity arrives, as we were told. If it arrives by Saturday 21 November at 18:00, Sami moves the deployment to the group's resource group, where the frontend can use Static Web Apps. Otherwise we submit on the personal deployment.

**Independent work.** Each feature has one owner and uses only what was already on `main` or what its owner builds. New Pantry endpoints go in their own router modules, only the restock feature adds a migration (`0002`), and each frontend feature has its own file and its own section of the page.

**Definition of Done for this sprint.** An item is done when its PR is merged, CD has deployed it, and its owner has ticked every acceptance criterion in the issue with evidence: a screenshot or command output, the CI run and the deployed SHA. Every PR still needs one approval from another member. The reviewer reads the diff and checks CI is green.

**Cut line.** A feature PR that isn't merged by Sunday 22 November at 18:00 is moved to "Not done" and left out of the demo.

**Monitoring.** Request count, error rate and latency per service are saved Log Analytics queries, committed in `docs/monitoring/`. The SLO is: 95% of `GET /pantry` requests return 200 within 2000 ms over the last 7 days.

**Sample products.** Recipes and demos use six products checked on Open Food Facts: Barilla Spaghetti Nº5, Barilla Pesto alla Genovese, Polpa di pomodoro, Galbani Mozzarella, Heinz Beanz and Nutella.

**Events.** The retrospective is written on a GitHub issue by Monday 23 November at 12:00. The Sprint Review is a call on Monday 23 November at 18:00, which is also the demo rehearsal.

## Sprint Review (23 November)

To fill in after the call: attendees, deployed SHA, items done and not done, links to the failure and delivery evidence, and the dashboard and SLO result.

## Retrospective (23 November)

To fill in from the retrospective issue: each member's answer to what went well, what slowed them down, and their action for a next sprint.
