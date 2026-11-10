# AI Usage Log

One row per meaningful AI interaction, including workflows, Dockerfiles and infrastructure code. Each member adds their own rows in the same pull request as the work. The columns follow the individual assignments, with a Member column added because the log is shared.

| Date/commit | Member | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|---|
| 2026-11-09 | @Thecoolss | ChatGPT | "Write the content of the files in the frontend folder (index, styles, app)." | Accepted | ChatGPT wrote the html, css, and simple JS for the local UI.| We have placeholder for entering the Barcode. Some headers describing each section (Pantry, Catalog) with PantryPal at the top. There is also a section that shows "Healthy" or "Unavaialable" that pings the actual docker containers to check their current status. That happens on each refresh page.|
| 2026-11-10 | @Thecoolss | Kiro | "Write README.md on the new branch." | Accepted | Kiro drafted `README.md` (product, architecture diagram, local run steps, troubleshooting, tests, planned Azure setup).| README lists the featues we planned for each sprint. It also describes the architecture containing 2 services with their own seperate databases and a static UI. Browser can call either service via HTTPS with CORS well configured. Log analytics are for writing requests, error rate, latency, etc. Docker container images are managed on Github Container Registry. |
