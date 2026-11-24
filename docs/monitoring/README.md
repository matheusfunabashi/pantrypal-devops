# Monitoring

The four Sprint 2 queries are saved under the PantryPal category in both workspaces. For the live demo, open `sdd-3b-g8-logs` in `rg-sdd-3b-g8`. The Group 8 copies use the same app names as the KQL files here. The historical copies in `sdd-bcsai-g3b-personal-logs` filter on the personal apps. [ADR-5](../decisions.md)

| Query | What it shows |
| --- | --- |
| [request-count.kql](request-count.kql) | Requests per service, per hour, last 7 days |
| [error-rate.kql](error-rate.kql) | 5xx / all requests per service, per hour, last 7 days |
| [latency.kql](latency.kql) | p50, p95 and max `duration_ms` per service, per hour, last 7 days |
| [slo.kql](slo.kql) | SLO: share of `GET /pantry` requests with status 200 within 2000 ms, last 7 days |
| [requests.kql](requests.kql) | Raw request lines from the last hour, for debugging |

All queries read the request line each service writes, for example `INFO method=GET path=/pantry status=200 duration_ms=17`, from `ContainerAppConsoleLogs_CL`.

To run one: Azure portal → the Log Analytics workspace → Logs → paste the query → Run. To save it: Save → Save as query, with the file name as the query name.

On 23 November at 15:25 UTC, Group 8 recorded 82 of 82 successful `GET /pantry` requests within 2 seconds, including 60 deliberate acceptance requests. The personal workspace recorded 134 of 134. Both seven-day samples met the 95% target. The latency is measured inside the service. [Group SLO result](screenshots/ie-slo.png) · [Personal SLO result](screenshots/personal-slo.png) · [All query results](screenshots/)
