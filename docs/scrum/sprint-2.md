# Sprint 2 (19 to 24 November 2026)

Scrum Master: Gustave (@gustaveems)

## Sprint Goal

At the shop, scan a product, check its Nutri-Score, compare it with another product and see how many are already at home. At home, see what needs restocking, which meals the pantry can make, and a Nutri-Score overview of the pantry. Demonstrate the released app, a measured SLO and graceful behaviour when a dependency fails.

## Roles

| Member | Scrum role | Main work |
| --- | --- | --- |
| Matheus Funabashi (@matheusfunabashi) | Product Owner | "What can I cook?", pantry Nutri-Score overview, Catalog-down evidence, release tags |
| Gustave (@gustaveems) | Scrum Master | Already at home, compare two products, dashboard and SLO |
| Sami Droubi (@Thecoolss) | Developer | Restock list, camera scanning, Check Before You Buy, recipe ingredient matching, Group 8 cutover and delivery evidence |

During the sprint, Sami implemented Check Before You Buy, originally assigned to Gustave, and extended Matheus's recipes to recognise ingredients across brands. [Check Before You Buy](https://github.com/matheusfunabashi/pantrypal-devops/pull/78) · [Original recipes](https://github.com/matheusfunabashi/pantrypal-devops/pull/75) · [Ingredient matching](https://github.com/matheusfunabashi/pantrypal-devops/pull/77)

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

On 22 November, Group 8 verified that `sdd-3b-g8-github` has Contributor on `rg-sdd-3b-g8`. Azure recorded the identity on 21 November before the 18:00 cutoff. On 22 November the team created the main-branch federated credential and verified its configuration. On 23 November the group deployment went live at `aeb1ac5`. See the [cutover CD run](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/45186481843). [Group deployment runbook](../azure-group-setup.md)

**Independent work.** Each feature has one owner and uses only what was already on `main` or what its owner builds. New Pantry endpoints go in their own router modules, only the restock feature adds a migration (`0002`), and each frontend feature has its own file and its own section of the page.

**Definition of Done for this sprint.** An item is done when its PR is merged, CD has deployed it, and its owner has ticked every acceptance criterion in the issue with evidence: a screenshot or command output, the CI run and the deployed SHA. Every PR still needs one approval from another member. The reviewer reads the diff and checks CI is green.

**Cut line.** A feature PR that isn't merged by Sunday 22 November at 18:00 is moved to "Not done" and left out of the demo.

**Monitoring.** Request count, error rate and latency per service are saved Log Analytics queries, committed in `docs/monitoring/`. The SLO is: 95% of `GET /pantry` requests return 200 within 2000 ms over the last 7 days.

**Sample products.** Recipes and demos use six products checked on Open Food Facts: Barilla Spaghetti Nº5, Barilla Pesto alla Genovese, Polpa di pomodoro, Galbani Mozzarella, Heinz Beanz and Nutella.

**Events.** The retrospective is written on a GitHub issue by Monday 23 November at 12:00. The Sprint Review is a call on Monday 23 November at 18:00, which is also the demo rehearsal.

## Sprint Review (23 November)

Sami, Gustave and Matheus attended a short review and tested the live Group 8 site together. Matheus reported that the live camera sometimes failed to read a barcode. The team identified camera reliability as follow-up work. Scanning a clear photo and typing the barcode remain available in the deployed app. [Scanner PR](https://github.com/matheusfunabashi/pantrypal-devops/pull/76)

On 23 November, all 13 jobs passed for the first Group 8 deployment at `aeb1ac5`. Desktop checks covered lookup, pantry CRUD and restock. Sami also reported a successful physical-phone check. [Cutover CD run](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/45186481843)

| Sprint items | What shipped or was measured |
| --- | --- |
| S2-01 Check Before You Buy, S2-03 Already at home, S2-09 Compare | A lookup showed the grade and current stock without writing to the pantry. Comparing two products handled different grades, equal grades and a missing grade. Gustave recorded these checks on the personal deployment before cutover. [Lookup](https://github.com/matheusfunabashi/pantrypal-devops/issues/8#issuecomment-7103050282) · [Stock](https://github.com/matheusfunabashi/pantrypal-devops/issues/62#issuecomment-7103051957) · [Comparison](https://github.com/matheusfunabashi/pantrypal-devops/issues/69#issuecomment-7103053585) |
| S2-02 Scanning, S2-04 Restock | Camera and photo scanning shipped. Sami confirmed a clear photo decoded successfully and reported close-focus difficulties with the live camera. The restock list shows the shortfall against a saved minimum, even after the last pack is removed. [Scanner](https://github.com/matheusfunabashi/pantrypal-devops/pull/76) · [Restock](https://github.com/matheusfunabashi/pantrypal-devops/pull/60) |
| S2-05 Recipes, S2-10 Pantry overview | Recipe cards count matching packages across brands and show what is missing. The pantry overview totals packages by Nutri-Score and shows the share graded A or B. [Recipes](https://github.com/matheusfunabashi/pantrypal-devops/pull/75) · [Ingredient matching](https://github.com/matheusfunabashi/pantrypal-devops/pull/77) · [Overview](https://github.com/matheusfunabashi/pantrypal-devops/pull/80) |
| S2-06 Monitoring | The IE workspace recorded 82 of 82 qualifying pantry reads returning HTTP 200 within two seconds, meeting the 95% target. The seven-day sample included 60 deliberate acceptance requests. [Monitoring results](../monitoring/README.md) |
| S2-07a and S2-07c Partial failure | With Catalog stopped locally, listing, changing quantities and deleting still worked. Adding a new barcode returned 503 in 4.04 seconds and the UI displayed the error. Catalog recovered after restart. With Open Food Facts unreachable, a cached lookup returned 200 in 0.09 seconds and a cache miss returned 503 in 5.06 seconds. [Catalog-down issue](https://github.com/matheusfunabashi/pantrypal-devops/issues/66) · [Compose output](evidence/catalog-down.txt) · [Browser error](evidence/catalog-down.png) · [Open Food Facts exercise](https://github.com/matheusfunabashi/pantrypal-devops/issues/68#issuecomment-7082067676) |
| S2-12 Group cutover, S2-07b Delivery | CD deployed the APIs and frontend to Group 8. After the scheduled review, PR #83 merged at `5b445d7`. All 13 jobs passed again, including the smoke check on the deployed `GET /recipes` endpoint. [Cutover](https://github.com/matheusfunabashi/pantrypal-devops/pull/82) · [Delivery issue](https://github.com/matheusfunabashi/pantrypal-devops/issues/67) · [CD run](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/45292544544) · [Smoke job](https://github.com/matheusfunabashi/pantrypal-devops/actions/runs/45292544544/job/138107108254) |

**Open at the 24 November documentation check.** S2-08 documentation was in review preparation. For S2-11, `v0.2.0` pointed to `4326d05`. The final `v1.0.0` and `submission` tags were still to be published. Some shipped items also had open evidence checklists, including the camera test with a leading-zero barcode. [Documentation](https://github.com/matheusfunabashi/pantrypal-devops/issues/71) · [Release tags](https://github.com/matheusfunabashi/pantrypal-devops/issues/72) · [Camera acceptance](https://github.com/matheusfunabashi/pantrypal-devops/issues/9)

**Next sprint.** Reproduce the intermittent camera failures on phones and check whether the scanner can consistently read the same barcode on repeated attempts. US-08 also remained in the backlog as a candidate. It would let someone record an expiry date and identify groceries to use soon. [Camera issue](https://github.com/matheusfunabashi/pantrypal-devops/issues/9) · [Expiry dates](https://github.com/matheusfunabashi/pantrypal-devops/issues/10)

## Retrospective (23 November)

Proposed actions for the next sprint

- **Matheus** found that better communication reduced merge conflicts and proposed spreading the work more evenly, with one short mid-sprint check-in to adjust overloaded days. [Retrospective comment](https://github.com/matheusfunabashi/pantrypal-devops/issues/74#issuecomment-7106053557)
- **Sami** — Test scanning changes on a real phone early, using the same package at several distances to catch focus problems before the review.
- **Gustave** — Ask each owner to link their test result in the issue when their change ships, so the evidence is ready for the review.
