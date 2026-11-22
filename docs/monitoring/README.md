# Monitoring

Saved Log Analytics queries for the personal deployment (workspace in `rg-sdd-BCSAI-g3B-personal`). The decision and the SLO are in ADR-5 in [docs/decisions.md](../decisions.md).

| Query | What it shows |
| --- | --- |
| [request-count.kql](request-count.kql) | Requests per service, per hour, last 7 days |
| [error-rate.kql](error-rate.kql) | 5xx / all requests per service, per hour, last 7 days |
| [latency.kql](latency.kql) | p50, p95 and max `duration_ms` per service, per hour, last 7 days |
| [slo.kql](slo.kql) | SLO: share of `GET /pantry` requests with status 200 within 2000 ms, last 7 days |
| [requests.kql](requests.kql) | Raw request lines from the last hour, for debugging |

All queries read the request line each service writes, for example `INFO method=GET path=/pantry status=200 duration_ms=17`, from `ContainerAppConsoleLogs_CL`.

To run one: Azure portal → the Log Analytics workspace → Logs → paste the query → Run. To save it: Save → Save as query, with the file name as the query name.

Screenshots of each result are in [screenshots/](screenshots/).
