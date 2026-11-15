# Architecture decisions

## 3. Personal Azure hosting and deployment
Date: 2026-11-14
Status: Decided

Context: Sprint 1 requires the PantryPal skeleton to run on Azure before feature expansion. The personal-account guidance in assignment 2 specifies an Azure for Students subscription, a project resource group, Storage static website hosting, and a managed identity for the pipeline. Our subscription blocks Static Web Apps regions and the guidance's suggested France Central region, while the university tenant prevents application registrations.

Decision: Use Azure CLI scripts to provision a dedicated prefixed resource group's resources in Germany West Central: two Consumption Container Apps with 0–1 replicas, one SQL logical server with two serverless databases, a Storage static website, and Log Analytics, with GitHub OIDC authentication through a user-assigned managed identity scoped to the project. CD must reuse CI before publishing public SHA-tagged GHCR images, configure per-service SQL passwords as Container App secrets, upload the static frontend, and check both health endpoints concurrently within five minutes; nginx remains local-only and feature smoke tests stay disabled until their endpoints exist.

Alternatives considered: 1. Static Web Apps in the shared institutional subscription — unavailable while deploying to the personal account, whose allowed regions do not support Static Web Apps. 2. France Central — recommended by the cloud instructions but excluded by this subscription's policy, so use the permitted Germany West Central region. 3. Bicep for provisioning — deferred until the scripted deployment works, to protect the first-deployment milestone.

Consequences: Consumption compute and SQL auto-pause reduce idle costs, but the first request may wait for a container cold start and database resume, so startup migrations need bounded connection retries and deployment checks allow five minutes; the 0–1 replica setting limits scale, and a large traffic increase would require revisiting capacity and migration coordination. Storage provides the public HTTPS UI origin used by backend CORS, only frontend files may be uploaded, persistent state stays in each service's database, and the monthly budget alert of 30 reports spending without enforcing a hard cap.
