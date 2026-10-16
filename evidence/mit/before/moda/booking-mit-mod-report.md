# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | booking-mit |
| **Date** | 2026-10-16 |
| **TD Version** | modernization-readiness-analysis (version ID unresolved — `atx custom def get -n modernization-readiness-analysis` returned "not found" in this environment) |
| **Repo Type** | application (auto-detected) |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | — |
| **Tags** | — |
| **Context** | Original MIT Python booking service, PostgreSQL database, synthetic payment HTTP provider and recovery/audit worker. Goal: a simple reproducible container-based workshop with a clear path to an operated deployment. Smallest compatible runtime preferred; no pre-existing EKS cluster or platform pipeline may be assumed. Application source under `booking_lab/`; `run.py` executes integration tests with disposable isolated Docker resources. |
| **Overall Score** | 2.02 / 4.0 |

**Classification Tier**: 🟠 **Remediation Required** — matched rule "2-11 High → Remediation Required".

**Classification Rationale**: This repository has **4 High**, **19 Medium**, and **8 Low** findings (31 findings total across 31 scored questions that fell below the passing score of 4). The matched rule is "2-11 High → Remediation Required". MOD classification is deliberately softer than the Agentic Readiness Analysis (ARA) on a single High finding: in ARA, one High is an agent-deployment gate; in MOD, one High is typically a single modernization gap and maps only to *Pilot-Ready*. This repo reaches *Remediation Required* because four independent core-question gaps (self-managed database, zero IaC, zero CI/CD, no encryption at rest) each sit at the lowest score, not because of one isolated issue.

**Repo Type Justification**: `booking_lab/` contains application source with a deployable entry point (`service.py` with `if __name__ == '__main__': main()`, serving HTTP on `0.0.0.0:8080`), a dependency manifest (`booking_lab/requirements.txt`) and a `booking_lab/Dockerfile`. A single service unit, no sibling `services/*` or `apps/*` tree, and no resource-provisioning IaC. Classified as `application`.

**Archetype Justification**: The service owns persistent relational state (PostgreSQL via `psycopg` in `booking_lab/service.py`, schema in `booking_lab/schema.sql`) and exposes write endpoints (`POST /bookings`, `DELETE /bookings/{id}`) alongside reads, with explicit entity lifecycle status fields and per-principal (`agent-a`/`agent-b`) data scoping. It calls exactly one downstream service (the payment provider), which is below the 3-downstream threshold for `orchestrator`. Classified as `stateful-crud`.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

Surface-flag rationale:
- `has_persistent_data_store=true` — `psycopg[binary]==3.3.6` in `booking_lab/requirements.txt`, connection factory `db()` in `booking_lab/service.py`, relational schema in `booking_lab/schema.sql`, and a pinned `postgres` image digest in `booking_lab/images.lock.json`.
- `has_at_rest_data_surface=true` — a named Docker volume holds the PostgreSQL data directory (`docker volume create ...-db-data`, `-v ...-db-data:/var/lib/postgresql/data` in `booking_lab/run.py`).
- `has_deployed_workload=false` — `booking_lab/Dockerfile` exists, but no deployment manifest references it: no Kubernetes manifests, no Helm chart, no Kustomize overlay, no `docker-compose.yml`, and no Terraform/CDK/CloudFormation/SAM anywhere in the repository. The only orchestration is imperative `docker run` calls inside the ephemeral test harness `booking_lab/run.py`, which creates disposable, uniquely-prefixed resources per run and is explicitly a test fixture rather than a deployment definition. Gates INF-Q9, OPS-Q5, OPS-Q7 to Not Evaluated.
- `has_api_surface=true` — HTTP endpoints defined in `Handler.dispatch` / `Handler.payments` in `booking_lab/service.py`.
- `has_multi_instance_deployment=false` — two API replicas (`api-a`, `api-b`) are started by `booking_lab/run.py` to prove cross-replica correctness, but no declarative deployment model (replica count, ASG, ECS desired count) exists in the repository.
- `has_iac_provisioning_aws_resources=false` — no `aws_*` Terraform resources, no `AWS::*` CloudFormation types, no CDK app, no SAM template. Gates SEC-Q1 and OPS-Q9 to Not Evaluated.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.60 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work | Needs Work |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.83 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Ready | Needs Work |
| **Overall** | **2.02 / 4.0** | **🟠 Needs Work** | **Remediation Required** |

### Scoring Notes

- **INF**: (Q1 2 + Q2 1 + Q3 2 + Q4 2 + Q5 3 + Q6 1 + Q7 1 + Q8 2 + Q10 1 + Q11 1) / 10 = 16/10 = **1.60**. INF-Q9 excluded — Not Evaluated (surface flag `has_deployed_workload=false`).
- **APP**: (Q1 3 + Q2 2 + Q3 3 + Q4 3 + Q5 1 + Q6 2) / 6 = 14/6 = **2.33**.
- **DATA**: (Q1 4 + Q2 3 + Q3 3 + Q4 2) / 4 = 12/4 = **3.00**.
- **SEC**: (Q2 1 + Q3 3 + Q4 1 + Q5 2 + Q6 3 + Q7 1) / 6 = 11/6 = **1.83**. SEC-Q1 excluded — Not Evaluated (surface flag `has_iac_provisioning_aws_resources=false`).
- **OPS**: (Q1 2 + Q2 1 + Q3 1 + Q4 1 + Q6 2 + Q8 1) / 6 = 8/6 = **1.33**. OPS-Q5, OPS-Q7 excluded — Not Evaluated (`has_deployed_workload=false`); OPS-Q9 excluded — Not Evaluated (`has_iac_provisioning_aws_resources=false`).
- **Overall**: (1.60 + 2.33 + 3.00 + 1.83 + 1.33) / 5 = 10.09/5 = **2.02** (each category weighted equally).

**Consistency check**: score band 1.5–2.4 → "Needs Work" ≡ count tier "Remediation Required" (4 High). Counts derived from the emitted findings array. Status: **consistent**.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC of any kind — the only environment definition is imperative `docker run`/`docker network` calls inside the test harness `booking_lab/run.py`. | Nothing about an operated environment is reproducible or reviewable. Blocks every other pathway: there is no artifact to extend for managed compute, managed database, networking, or monitoring. |
| 2 | INF-Q11: CI/CD Automation | 1 | No pipeline definition at all — no `.github/workflows/`, `buildspec.yml`, `Jenkinsfile`, or `.gitlab-ci.yml`. The high-value E2E suite in `booking_lab/run.py` is only ever run by hand. | The repository's strongest asset (17 durability/concurrency acceptance cases) provides no regression protection, and image build/publish is manual and unattributable. |
| 3 | INF-Q2: Managed Databases | 1 | PostgreSQL runs as a self-managed container on a local Docker volume with a bootstrap superuser password generated by the test harness; no managed database service, no failover. | The saga's correctness guarantees all rest on a single-instance, unreplicated, unbacked-up database. This is the single largest durability risk on the path to an operated deployment. |
| 4 | SEC-Q2: Encryption at Rest | 1 | The PostgreSQL data volume, the `pg_dump` output written to `.local/`, and the `.env` files carrying role passwords are all stored unencrypted. No KMS, no volume encryption, no envelope encryption. | Payment-adjacent records (principals, itineraries, amounts, charge states) and an immutable audit trail sit in plaintext at rest — a baseline control gap that blocks any production or compliance-scoped deployment. |
| 5 | INF-Q6: API Entry Point | 1 | `ThreadingHTTPServer` binds `0.0.0.0:8080` and is exposed directly; no API Gateway, ALB, CloudFront, or any reverse proxy. No throttling, no request-rate limiting, no TLS termination. | All transport security, rate limiting, and request validation responsibility falls on a stdlib HTTP server. An operated deployment has no place to attach throttling or WAF controls, and unauthenticated callers can exhaust the connection pool. |

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | Primary APP-Q2 = 2 (< 3) met; supporting INF-Q1 = 2 (< 3) met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 2 (< 3) is met, but the supporting condition fails: container definitions **were** found (`booking_lab/Dockerfile`, pinned base-image digests in `booking_lab/images.lock.json`). The workload is already containerized; the gap is orchestration, which Move to Cloud Native covers. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 2 (< 3) is met, but the compound condition fails: no commercial database engine is present. The only engine is open-source PostgreSQL (`booking_lab/images.lock.json`). No licensing exposure to remove. |
| 4 | Move to Managed Databases | Triggered | High | Medium | Primary INF-Q2 = 1 (< 3) met — PostgreSQL is self-managed in a container. Supporting DATA-Q3 = 3 does not fire (version is digest-pinned). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 2 (< 3) is met, but the contextual guard blocks it: no data-processing workload exists. No ETL scripts, Glue jobs, Airflow DAGs, Kinesis/MSK/Kafka infrastructure, data lake, or analytics query layer anywhere in the repository. The `outbox` → `audit_events` flow is a transactional audit trail, not an analytics pipeline. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | Primary INF-Q10 = 1 (< 3) **and** INF-Q11 = 1 (< 3) both met; supporting OPS-Q6 = 2 (< 3) strengthens the case. OPS-Q5 excluded (Not Evaluated, `has_deployed_workload=false`). |
| 7 | Move to AI | Not Triggered | — | — | Contextual guard not satisfied: no AI/agent intent is evidenced in the repository. A whole-word case-insensitive scan of `booking_lab/requirements.txt`, all source imports, all configuration, and all documentation (`booking_lab/README.md`) found none of the AI signal terms (Bedrock, LLM, generative AI, GenAI, RAG, vector database/store, embedding, chatbot, copilot, machine learning, agentic, AI agent, AI-powered, large language model). The repository's use of "agent-a"/"agent-b" is a *test principal identifier*, not an LLM agent, and generic "agent" is explicitly excluded from the signal-term list. Primary trigger conditions were therefore not evaluated. |

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current architecture state (APP-Q2 = 2).** The repository is a single-module monolith: `booking_lab/service.py` (302 lines) contains the booking API, the payment provider, and the recovery/outbox worker, selected at runtime by `sys.argv[1]` (`api` | `payments` | `worker`). All three run from one image and one codebase, so they cannot be versioned, released, or rolled back independently. Coupling is *partially* mitigated — and this is a genuine strength worth preserving: `booking_lab/schema.sql` creates four distinct database roles (`booking_app`, `payment_app`, `audit_writer`, `audit_reader`) with table-level grants that forbid cross-service access, and `booking_lab/run.py::rights()` actively proves `payment_app` cannot read `bookings` and `booking_app` cannot read `audit_events`. But all tables share the single `public` schema in a single database, and the payment "provider" is in-process code in the same file as its caller, so the boundaries exist only as privilege policy, not as deployable or schema boundaries.

**Compute model gaps (INF-Q1 = 2).** The workload is containerized (`booking_lab/Dockerfile`, non-root `USER 65532:65532`, digest-pinned base image) but there is no managed orchestration target: no ECS task definition, no EKS/Kubernetes manifest, no Lambda function, no App Runner service. Lifecycle, restart, replica count, and placement are all decided by imperative `docker run` calls in the test harness.

**Communication pattern gaps (APP-Q3 = 3, APP-Q4 = 3).** Both score at Partial, so neither acts as a strong supporting trigger. Async is already used where it matters most — the transactional outbox (`outbox` table, `emit()`, `deliver()`) decouples audit delivery from the request path, and the recovery worker (`recover()`) resumes persisted saga state after crashes. The remaining synchronous coupling is the inline `payment()` call inside the request path, which is bounded (4s HTTP timeout, 10s statement timeout) and fails closed to `503` with `retry_same_idempotency_key: true`. The gap is the absence of a client-facing operation-status resource: a caller whose request was interrupted must re-POST with the same `Idempotency-Key` rather than poll a durable operation.

**Recommended decomposition approach.** See the Decomposition Strategy section below (APP-Q2 < 3). Summary: do **not** split the booking saga — its correctness depends on `operations`, `bookings`, and `outbox` committing in one local transaction. Extract the payment provider instead (it is already an HTTP boundary with its own role, its own table, and its own bearer credential), and promote the per-role grants into per-service schemas.

**Representative AWS services.** Given the steering preference for the smallest compatible runtime and no pre-existing EKS cluster: **ECS on Fargate** (two task definitions — `api` service and `worker` service — from one image, matching the existing `argv` modes) behind **Application Load Balancer**, with **Amazon ECR** for the image, **Amazon RDS for PostgreSQL** (or Aurora PostgreSQL) for the store, and **Secrets Manager** for role credentials. API Gateway (HTTP API) is the smaller alternative to ALB if throttling is the priority. EKS is not recommended here: the workload is two processes and one database, and the steering context states no cluster may be assumed. Step Functions is *not* recommended for the saga — the saga is already durable in the database and moving it would weaken the single-transaction invariant.

**Recommended patterns.**
- **Strangler Fig** — extract the payment provider first; the booking service already talks to it over HTTP via `PAYMENT_URL`, so extraction is a deployment change, not a code rewrite. [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- **Anti-corruption Layer** — the `payment()` function already normalizes provider responses (`402` → `DECLINED`, transport errors → retryable `RuntimeError`); formalize it as the ACL when the provider becomes a real third party. [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- **Saga** — already implemented correctly and durably (`advance()` with persisted `NEW → CHARGED → CONFIRMED` / `COMPENSATING → COMPENSATED` states, compensating refunds, and re-read-before-refund on ambiguous commit). Preserve it as-is. [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)
- **Event Sourcing** — the `outbox` → `audit_events` flow with UUID deduplication is already an event-log foundation; formalize it if additional consumers appear. [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html)
- **Hexagonal Architecture** — extract `db()`, `payment()`, and the HTTP handler into explicit ports so the service can be tested and deployed against RDS and a real provider without touching saga logic.

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current database topology (INF-Q2 = 1).** A single self-managed PostgreSQL container, image digest-pinned in `booking_lab/images.lock.json`, started by `booking_lab/run.py` with a generated superuser password on a local named Docker volume. There is no replica, no automatic failover, no automated backup schedule, no retention policy, and no PITR. The bootstrap owner is correctly separated from every runtime role (`booking_lab/schema.sql`), which is good practice that carries over to a managed service unchanged.

**Engine version and EOL status (DATA-Q3 = 3).** The engine is pinned immutably by image digest, which is stronger than a floating tag, but the pin obscures the human-readable major version — `booking_lab/run.py` has to query `SHOW server_version;` at runtime to record it as evidence. No documented engine-update or EOL-tracking procedure exists.

**Data access patterns (DATA-Q2 = 3).** All database access funnels through the single `db(name='DATABASE_URL')` factory in `booking_lab/service.py`, with the audit sink reached via the separate `AUDIT_DATABASE_URL`. Connection-string-driven access means repointing to a managed endpoint is a configuration change, not a code change — this materially lowers migration effort.

**Migration considerations specific to this service.** Three PostgreSQL-specific mechanisms must be preserved and verified on the target engine, because the service's correctness guarantees depend on them:
1. `pg_advisory_lock` (session-scoped, spanning external payment calls) and `pg_advisory_xact_lock` in the provider — supported on RDS/Aurora PostgreSQL. Note that session advisory locks interact with connection pooling: a transaction-pooling proxy (including RDS Proxy in some modes) can break the session-lock guarantee. Validate with the existing `eight_concurrent_requests_two_api_replicas_one_charge` case before cutover.
2. `FOR UPDATE SKIP LOCKED` in `deliver()` for outbox draining — supported.
3. `jsonb`, `clock_timestamp()`, and the `CHECK` constraint state machine — supported.

**Recommended managed targets.** **Amazon RDS for PostgreSQL** Multi-AZ is the smallest compatible target and preserves every construct above; **Aurora PostgreSQL** if read scaling or faster failover is wanted later. DynamoDB is explicitly **not** appropriate — the saga depends on multi-table single-transaction commits (`operations` + `bookings` + `outbox`) and on advisory locks, neither of which has a DynamoDB equivalent without redesigning the durability model the test suite exists to prove.

**Immediate actions.** (1) Define the database in IaC with `multi_az = true`, `backup_retention_period` ≥ 7, `storage_encrypted = true` and a customer-managed KMS key — this closes INF-Q2, INF-Q8, INF-Q9 and SEC-Q2 in one change. (2) Move the four role passwords into Secrets Manager with rotation. (3) Keep `booking_lab/run.py`'s `pg_dump`/restore row-hash verification as the migration validation harness — it is already a working data-fidelity check.

**Migration tooling.** AWS DMS for the data move (homogeneous PostgreSQL → PostgreSQL); AWS SCT is not needed — there is no engine conversion.

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC coverage (INF-Q10 = 1).** Zero. Searches for `*.tf`, `*.tfvars`, `cdk.json`, CloudFormation templates, `Chart.yaml`, `kustomization.yaml`, and `docker-compose*.yml` across the repository returned nothing. Every environment concern — networks, volumes, container lifecycle, port binding, resource limits, role creation — is expressed imperatively in `booking_lab/run.py` as `subprocess` calls to the Docker CLI. This is deliberate and appropriate for a disposable test fixture, but it means there is no declarative artifact describing an operated environment, and none of the surfaces this service demonstrably depends on (compute, networking, data store, secrets, monitoring) is covered.

**Current CI/CD state (INF-Q11 = 1).** No pipeline definition exists. The repository's most valuable asset is the acceptance suite in `booking_lab/run.py` — 17 cases covering authentication rejection (issuer/audience/expiry/nbf/signature/scope), cross-replica idempotent replay, identity isolation, 8-way concurrency against two replicas yielding exactly one charge, real insert-failure compensation, refund-provider outage with durable `COMPENSATING` state, process crash after external commit reconciling without double charge, crash after refund without second refund, provider outage retaining intent, declined payment, cancel/refund idempotency, audit-delivery failure with durable outbox drain, redelivery deduplication, runtime-role privilege containment, fail-closed behaviour during database outage, and a real `pg_dump`/restore with per-table row-hash comparison. None of it runs automatically.

**Deployment strategy (OPS-Q5).** Not Evaluated — `has_deployed_workload=false`. There is no deployed workload in this repository to assess a rollout strategy against. This must be established as part of the IaC work, not retrofitted.

**Testing gaps (OPS-Q6 = 2).** Coverage is exceptional; execution is entirely manual. The suite also requires a Docker daemon and ~35s waits per condition, so it needs a runner with Docker available (GitHub Actions `ubuntu-latest`, or CodeBuild with privileged mode).

**Recommended toolchain and sequencing.** Smallest-first, consistent with the steering preference:
1. **CI first** — add a workflow that runs `python3 booking_lab/run.py e2e --output .local/db-e2e.json` on every pull request, uploads the evidence JSON as an artifact, and fails the build on a non-zero exit. This converts the existing suite into a regression gate at near-zero cost and is the single highest-leverage change in the repository.
2. **Add security steps to the same pipeline** — `pip-audit` on `booking_lab/requirements.txt`, a container scan of the built image (Amazon ECR enhanced scanning or Trivy), and a dependency-update bot (`.github/dependabot.yml`) so digest pins get refreshed rather than frozen. Closes SEC-Q7 and lifts SEC-Q6.
3. **Then IaC** — one Terraform or CDK stack covering VPC with private subnets, ECS Fargate services for the `api` and `worker` modes, ALB or API Gateway, RDS PostgreSQL Multi-AZ with encryption and backup retention, Secrets Manager entries, CloudWatch log groups, latency/error alarms, and consistent cost/ownership tags. This single stack closes or lifts INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, SEC-Q1, SEC-Q2, SEC-Q5, OPS-Q2, OPS-Q4 and OPS-Q9.
4. **Then deployment safety** — ECS rolling deployment with circuit breaker and automatic rollback as the minimum; CodeDeploy blue/green for the API service once the ALB exists.

**Representative AWS services.** CodeBuild / CodePipeline or GitHub Actions with OIDC into an IAM role, Amazon ECR (with scan-on-push), CloudFormation or CDK, CodeDeploy, CloudWatch. The existing `images.lock.json` + `--output` evidence pattern is already pipeline-shaped and should be kept.

---

## Decomposition Strategy

APP-Q2 scored 2, so this section applies.

### Approach Options

| Approach | Applicability to booking-mit | Level of Effort | Verdict |
|----------|------------------------------|-----------------|---------|
| **Strengthen as Modular Monolith** | High. The booking saga is one bounded context whose correctness depends on `operations`, `bookings` and `outbox` committing inside a single local transaction (`advance()`, `transition()`, `result()` in `booking_lab/service.py`). Splitting those tables across services would convert a local ACID commit into a distributed transaction and weaken exactly the guarantees the E2E suite exists to prove. The real work is promoting the existing per-role grants into per-service schemas and separating the three `argv` modes into their own modules. | **Low** — module separation plus a schema-per-service migration. No new distributed-systems problems introduced. | ✅ **Recommended as the primary track.** |
| **Strangler Fig (Parallel Track)** | Medium–High, but only for the payment provider. It is already an HTTP boundary (`PAYMENT_URL`, bearer token, `/charge` and `/refund`), already has its own database role (`payment_app`) and its own table (`charges`), and `booking_lab/run.py::rights()` already proves it cannot reach `bookings`. Extracting it to its own repository/image/database is a bounded, low-risk change — and necessary anyway, because in any operated deployment the provider is a third party, not in-process code. | **Low–Medium** for the provider alone; High if applied to the booking saga (not recommended). | ✅ **Recommended, scoped to the payment provider only.** |
| **Conditional / Adaptive** | Already partially satisfied — the workload is containerized. The adaptive step here is "deploy the existing image to Fargate as two task definitions (`api`, `worker`) and extract only the payment provider", deferring any further split until a driver appears. | **Low** — reuses the existing Dockerfile unchanged. | ✅ **Recommended as the sequencing strategy.** |
| **Big-Bang Rewrite** | Not applicable. The implementation is 350 lines of working, invariant-verified code with a 17-case acceptance suite. A rewrite would discard a tested durability model for no architectural gain. | Very High | ⚠️ **Recommended against.** |

**Recommendation**: strengthen as a modular monolith (booking API + worker as one service, two deployment modes), extract the payment provider via Strangler Fig, and keep the saga transactional and local. Decomposition drivers here are weak — one team, one small service, no independent-scaling pressure — so a microservices split would add operational cost without benefit.

### Pattern Recommendations

| Pattern | Application here | AWS Prescriptive Guidance |
|---------|------------------|---------------------------|
| **Anti-corruption Layer** | Formalize `payment()` as the ACL between the booking saga and the real provider: it already maps HTTP 402 to `DECLINED` and all transport faults to a retryable error, and deliberately never marks a refund complete on an ambiguous timeout. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga** | Already implemented and durable. Preserve the invariant that `COMPENSATING`/`CANCELLING` states persist before the external refund call, and that refunds are retried rather than assumed. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | The transactional `outbox` with UUID-deduplicated delivery into `audit_events` (append-only, `audit_writer` has `INSERT` but no `UPDATE`/`DELETE`) is already an event-log foundation. Formalize when a second consumer appears; consider EventBridge or SQS as the delivery target instead of a direct second-database insert. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Split `booking_lab/service.py` into `api/` (HTTP adapter), `saga/` (pure state machine), `payments/` (provider port), `audit/` (outbox port) and `store/` (persistence adapter). This is the concrete form of the modular-monolith recommendation and makes the saga unit-testable without Docker. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Observed | Effect on effort |
|--------|----------|------------------|
| Module boundaries | Single 302-line file, three runtime modes selected by `argv`; no package structure, but no circular dependencies and very small surface. | **Lowers** — small enough to restructure safely. |
| Data coupling | One database, one `public` schema, but strict per-role table grants with no cross-service table access and no cross-module joins (proven by `rights()`). | **Lowers** — boundaries already exist as policy; promoting them to schemas is mechanical. |
| Stored procedures | One `plpgsql` function and one trigger, both existing solely for test fault injection; PostgreSQL-specific advisory locks are load-bearing in the concurrency design. | **Raises slightly** — advisory-lock semantics must be re-verified against any pooling proxy. |
| Communication patterns | Async already present for audit delivery and crash recovery; one bounded synchronous provider call remains. | **Lowers** — no async retrofit needed. |
| CI/CD maturity | None. No pipeline to extend. | **Raises** — pipeline must be built before extraction can be validated continuously. |
| Test coverage | 17 integration cases covering concurrency, crash recovery, compensation, privilege containment and dump/restore fidelity. | **Strongly lowers** — extraction can be validated empirically at every step. |

**Calibrated estimate**: **Low–Medium** for the recommended track (modular-monolith restructure + payment-provider extraction + Fargate deployment), gated on building the CI pipeline first so each step is validated by the existing suite.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P1 · Effort Medium · Phase 1 |
| **Finding** | The workload is containerized but runs on no managed compute platform. `booking_lab/Dockerfile` builds a single image (digest-pinned `python` base, `WORKDIR /app`, non-root `USER 65532:65532`, `CMD ["python","service.py","api"]`) that serves all three runtime modes. No `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_apprunner_*` or `aws_instance` resources exist, and no Kubernetes manifest, Helm chart or ECS task definition exists. The only compute lifecycle management is imperative: `booking_lab/run.py` issues `docker run -d --name ... --network ...` for the `db`, `payments`, `api-a`, `api-b` and `worker` containers. |
| **Gap** | Containerization is complete; managed orchestration is entirely absent. There is no declarative definition of how many replicas run, how they restart, where they are placed, or how they are health-checked by a scheduler — the service's own `/health/live` and `/health/ready` endpoints exist but nothing consumes them outside the test harness. |
| **Recommendation** | Define two ECS Fargate services from the existing image — one with `command: ["python","service.py","api"]` and one with `["python","service.py","worker"]` — wired to the existing `/health/ready` endpoint as the container health check. This reuses `booking_lab/Dockerfile` unchanged. EKS is not recommended: the steering context states no cluster may be assumed, and two processes plus one database do not justify cluster operations. Lambda is not recommended for the `api` mode because the saga relies on session-scoped `pg_advisory_lock` held across the external payment call. |
| **Evidence** | `booking_lab/Dockerfile`; `booking_lab/run.py` (`Lab.start`, `Lab.setup` docker invocations); absence of `*.tf`, `cdk.json`, CloudFormation templates, `Chart.yaml`, `k8s/`, `manifests/` anywhere in the repository |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **High** · Priority P1 · Effort Medium · Phase 1 |
| **Finding** | The sole datastore is a self-managed PostgreSQL container. `booking_lab/images.lock.json` pins `postgres@sha256:721873c3...`; `booking_lab/run.py` starts it with `docker run -d --name {prefix}-db --network {prefix} --env-file ... -v {prefix}-db-data:/var/lib/postgresql/data`, passing a generated `POSTGRES_PASSWORD`. No managed database resource of any kind (`aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, `aws_elasticache_*`) is defined. There is one instance, no replica, and no failover mechanism. The audit sink is the *same* instance reached through a different role (`AUDIT_DATABASE_URL` with the `audit_writer` role), so the audit trail shares the single point of failure with the operational data it audits. |
| **Gap** | Every durability guarantee the service is built to provide — the persisted saga state machine, the transactional outbox, the append-only audit trail — depends on a single unmanaged, unreplicated PostgreSQL process with no automated patching, no failover, and no managed backup. |
| **Recommendation** | Migrate to Amazon RDS for PostgreSQL (or Aurora PostgreSQL) with `multi_az = true`, `storage_encrypted = true` against a customer-managed KMS key, and `backup_retention_period` ≥ 7 days. Validate `pg_advisory_lock`, `pg_advisory_xact_lock` and `FOR UPDATE SKIP LOCKED` behaviour on the target before cutover — all three are supported, but session-scoped advisory locks are incompatible with transaction-level connection pooling, so re-run the `eight_concurrent_requests_two_api_replicas_one_charge` case against the managed endpoint through whatever proxy is in front of it. Place the audit sink in a separate database or account so the audit trail does not share a failure domain with the data it records. |
| **Evidence** | `booking_lab/images.lock.json`; `booking_lab/run.py` (`Lab.setup` database container creation, `Lab.start` `DATABASE_URL`/`AUDIT_DATABASE_URL` construction); `booking_lab/service.py` (`db()`, `deliver()`); `booking_lab/schema.sql` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P2 · Effort Medium · Phase 2 |
| **Finding** | *Archetype-calibrated (`stateful-crud`).* The multi-step booking workflow is implemented as a hand-rolled but genuinely structured state machine in application code. `booking_lab/schema.sql` constrains `operations.status` to `('NEW','CHARGED','CONFIRMED','COMPENSATING','COMPENSATED','DECLINED','CANCELLING','CANCELLED')` via a `CHECK`, and `booking_lab/service.py::advance()` is a resumable transition function driven entirely from persisted state, with `transition()` and `result()` committing each state change together with its outbox event. No dedicated orchestration service (`aws_sfn_*`, Temporal, Camunda, MWAA) is used. |
| **Gap** | Retry policy, backoff, timeout escalation and workflow visibility are all implicit in the code path and the worker's fixed 0.25s poll loop. There is no execution history, no per-step timeout, and no operator-visible view of in-flight or stuck operations beyond querying `operations` directly. |
| **Recommendation** | Keep the saga in application code — it is durable, idempotent and correct, and moving it to Step Functions would break the single-transaction commit of `operations` + `bookings` + `outbox` that the compensation tests verify. Instead close the visibility gap: emit a CloudWatch metric and alarm on the count of operations in `('NEW','CHARGED','COMPENSATING','CANCELLING')` older than a threshold (the query already exists in `booking_lab/run.py` as the `pending_operations` invariant), and add a bounded attempt counter with backoff so a permanently failing operation surfaces instead of looping silently. |
| **Recommendation note (archetype)** | For a `stateful-crud` service the `stateful-crud` rubric column applies, which expects dedicated orchestration for business-critical multi-step operations at Score 4. The score of 2 reflects "simple state machines in code with some structure, but no dedicated service" — the structure (persisted, constrained, resumable states) is real, which is why this is a 2 and not a 1. Had this service been classified `orchestrator`, the same evidence of a hand-coded coordination path across a downstream provider would have been flagged as an archetype anti-pattern; as a `stateful-crud` owning its own state, an in-process durable saga is a defensible design and the recommendation is explicitly *not* to adopt an orchestration service. |
| **Evidence** | `booking_lab/service.py` (`advance()`, `transition()`, `result()`, `recover()`, `main()` worker loop); `booking_lab/schema.sql` (`operations.status` CHECK constraint) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P2 · Effort Medium · Phase 2 |
| **Finding** | *Archetype-calibrated (`stateful-crud`).* Asynchronous delivery exists and is well built, but it is self-managed on PostgreSQL rather than on a managed messaging service. `booking_lab/schema.sql` defines an `outbox` table; `booking_lab/service.py::emit()` inserts the event in the same transaction as the state change, and `deliver()` drains it with `SELECT ... FOR UPDATE SKIP LOCKED LIMIT 100`, inserting into `audit_events` with `ON CONFLICT(id) DO NOTHING` for at-least-once-with-dedup semantics. No `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*`, `aws_kinesis_*`, `aws_msk_*` or `aws_mq_*` resource exists, and no messaging SDK is present in `booking_lab/requirements.txt` (the sole dependency is `psycopg[binary]==3.3.6`). |
| **Gap** | The broker is the application's own database table, so message durability, throughput and backlog visibility are all coupled to the single PostgreSQL instance, and fan-out to any additional consumer requires new application code. The 0.25s fixed-interval poll in `main()` is the only delivery trigger — there is no backpressure signal and no dead-letter destination for an event that can never be delivered. |
| **Recommendation** | Keep the transactional outbox — it is the correct pattern for atomically coupling a state change to an event, and removing it would reintroduce the dual-write problem. Change only the *delivery target*: have `deliver()` publish to EventBridge or SQS instead of inserting directly into a second database, and attach a dead-letter queue. Add an alarm on `SELECT count(*) FROM outbox WHERE delivered_at IS NULL` (the query already exists as the `undelivered_audit_events` invariant in `booking_lab/run.py`). |
| **Recommendation note (archetype)** | Under the `stateful-crud` column, Score 4 requires managed messaging for cross-service state changes; Score 2 is "self-managed messaging for cross-service flows", which is exactly what a database-backed outbox is. Note the archetype materially changed this score: for a `stateless-utility` or `data-gateway`, synchronous-only operation would have scored 4 as the correct design, and a self-managed broker would have been penalised as unnecessary overhead. Here the cross-service audit flow genuinely crosses a service boundary (`booking_app` → `audit_writer`), so managed messaging is the right target state. |
| **Evidence** | `booking_lab/schema.sql` (`outbox`, `audit_events`); `booking_lab/service.py` (`emit()`, `deliver()`, worker loop in `main()`); `booking_lab/requirements.txt` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P1 · Effort Medium · Phase 2 |
| **Finding** | The repository owns a real network surface — Docker networks created by `booking_lab/run.py` — and segments it deliberately. Two networks are created: `docker network create --internal {prefix}` (no external egress) carrying the database, the payment provider and the worker, and `{prefix}-front` carrying only the API replicas, which are then attached to both. Host exposure is restricted to loopback with an ephemeral port: `-p 127.0.0.1:{port}:8080`, never `0.0.0.0`. Containers additionally run with `--read-only --cap-drop=ALL --security-opt=no-new-privileges`, a `noexec,nosuid` tmpfs for `/tmp`, and memory/CPU/PID limits when the host supports cgroups. No `0.0.0.0/0` ingress and no default-network database exposure exists anywhere. |
| **Gap** | The segmentation is defined only inside an ephemeral test fixture, so none of it carries into an operated deployment: there is no VPC, no private-subnet placement, no security group, no VPC endpoint or PrivateLink, and no TLS anywhere (`DATABASE_URL` uses plain `postgresql://` with no `sslmode`, and the payment call uses plain `http://`). Database credentials and bearer tokens cross the container network in cleartext. |
| **Recommendation** | Port the demonstrated tiering into a VPC definition: API tasks in private subnets behind a load balancer, worker and database with no inbound path from the internet, security groups scoped to the single required port per hop, VPC endpoints for ECR/Secrets Manager/CloudWatch so no NAT egress is needed. Enforce `sslmode=verify-full` on both `DATABASE_URL` and `AUDIT_DATABASE_URL`, and TLS on `PAYMENT_URL`, before any non-local deployment. |
| **Evidence** | `booking_lab/run.py` (`Lab.setup` network creation, `Lab.start` options and port binding, `DATABASE_URL`/`PAYMENT_URL` construction); `booking_lab/service.py` (`db()` connection options, `payment()`) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Medium · Phase 2 |
| **Finding** | The service is exposed directly with no gateway or load balancer. `booking_lab/service.py::main()` starts `ThreadingHTTPServer(('0.0.0.0',8080), Handler)` — a Python stdlib server — and `booking_lab/run.py` publishes it straight to a host port. No `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_appsync_*`, `aws_lb_*` or CloudFront resource exists, and there is no reverse proxy in the image. |
| **Gap** | There is no throttling or rate limiting of any kind, no TLS termination, no request-size or connection-rate control at the edge (only an in-handler 8192-byte body cap and an 8-second socket timeout), no WAF, and no single control point for authentication. `ThreadingHTTPServer` spawns a thread per connection with no bound, so connection-rate abuse translates directly into thread and database-connection exhaustion. |
| **Recommendation** | Place API Gateway (HTTP API) or an Application Load Balancer in front of the service: ALB if TLS termination and health-checked target groups are the priority, API Gateway if per-client throttling and request validation matter more. Either way, terminate TLS at the edge, set a request-rate limit, and keep the existing `/health/ready` endpoint as the target-group health check. Retain the in-handler validation — it is good defence in depth — but stop relying on it as the only control. |
| **Evidence** | `booking_lab/service.py` (`main()` `ThreadingHTTPServer`, `Handler.body()` size cap, `Handler.dispatch` socket timeout); `booking_lab/run.py` (`Lab.start` port publishing); absence of any gateway/load-balancer IaC |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | No auto-scaling mechanism exists. Capacity is fixed and imperative: `booking_lab/run.py` starts exactly two API replicas and one worker, with hard-coded `--memory 256m --cpus 1 --pids-limit 128` per application container and `512m` for the database. No `aws_autoscaling_*` or `aws_appautoscaling_*` resource, no scaling policy, no min/max capacity, no Lambda concurrency setting, and no database capacity scaling is defined anywhere. |
| **Gap** | Neither compute nor data capacity can respond to load. The two API replicas exist to prove cross-replica correctness, not to provide elasticity, and the single worker is a fixed-throughput component: its 0.25s loop with `LIMIT 100` caps outbox drain and saga recovery throughput regardless of backlog. |
| **Recommendation** | After the ECS definition exists, attach Application Auto Scaling target tracking to the API service on ALB request-count-per-target (not CPU — the workload is I/O-bound on the database and the payment provider, so CPU is a poor load signal). Scale the worker on a custom CloudWatch metric derived from `SELECT count(*) FROM outbox WHERE delivered_at IS NULL` and the pending-operations count, which are the true backlog signals. On RDS, enable storage autoscaling and size the connection ceiling against the chosen task maximum — note that each request opens a fresh connection via `db()`, so connection count scales linearly with concurrency and will become the binding constraint before CPU does. |
| **Evidence** | `booking_lab/run.py` (`Lab.setup` `resource_options`, fixed `api-a`/`api-b`/`worker` container set); `booking_lab/service.py` (`db()` per-request connection, worker `time.sleep(0.25)` loop with `LIMIT 100`) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P2 · Effort Low · Phase 1 |
| **Finding** | Restore capability is genuinely *tested* but backup is not *configured*. `booking_lab/run.py::dump_restore()` performs a real `pg_dump` of the live database, restores it into a separate `restore_check` database, and asserts equality of row counts and of per-table MD5 row hashes for `operations`, `bookings`, `charges`, `outbox`, `audit_events` and `faults`, recording the hashes and the dump SHA-256 as evidence. The data volume is also proven to survive container restart (`database_outage_fail_closed_and_volume_survives_restart`). However there is no scheduled backup, no retention period, no PITR, no `aws_backup_plan`, no snapshot lifecycle and no cross-region copy — the dump exists only as a one-shot artifact in `.local/`. |
| **Gap** | A restore procedure is verified; a backup *policy* does not exist. There is nothing to restore *from* after a volume loss, and no defined RPO or RTO. The dump is also written unencrypted to local disk (see SEC-Q2). |
| **Recommendation** | On the managed database, set `backup_retention_period` (7–35 days), enable PITR, and enable automated snapshots with a KMS key; add an AWS Backup plan with a cross-region copy rule for the audit data. Keep `dump_restore()` as the fidelity check and promote it into the CI pipeline so restore validation runs on every change rather than only when the suite is invoked by hand. Record the resulting RPO/RTO alongside it. |
| **Evidence** | `booking_lab/run.py` (`dump_restore()`, `restart()`, `Lab.setup` `docker volume create`); absence of any backup-plan or retention configuration in the repository |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (surface-flag) |
| **Finding** | Gate: `has_deployed_workload` is `false`. `booking_lab/Dockerfile` exists but no deployment manifest references it — no Kubernetes/Helm/Kustomize manifest, no `docker-compose.yml`, and no Terraform/CDK/CloudFormation/SAM defining compute. The only container lifecycle management is imperative `docker run` inside the ephemeral test fixture `booking_lab/run.py`. This system therefore has no deployed workload against which to evaluate multi-AZ placement or fault isolation. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A — multi-AZ placement must be decided as part of the IaC work tracked under INF-Q10 and the managed-database migration under INF-Q2, and should be re-evaluated once a deployment definition exists in the repository. |
| **Evidence** | `booking_lab/Dockerfile`; `booking_lab/run.py`; absence of `*.tf`, `cdk.json`, CloudFormation templates, `Chart.yaml`, `kustomization.yaml`, `docker-compose*.yml`, `k8s/`, `manifests/` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **High** · Priority P1 · Effort Medium · Phase 1 |
| **Finding** | There is no infrastructure as code. Searches across the repository for `*.tf`, `*.tfvars`, `cdk.json`, CloudFormation templates (`template.yaml`/`template.json`/`*.cfn.*`), `Chart.yaml`, `values.yaml`, `kustomization.yaml`, `docker-compose*.yml`, Ansible playbooks and ArgoCD/Flux resources returned nothing. The repository contains exactly eleven files, of which the only environment definition is `booking_lab/run.py` — imperative Python `subprocess` calls to the Docker CLI that create per-run networks, a volume, database roles and five containers under a random prefix, and are explicitly designed to be disposable. Every infrastructure category this service demonstrably depends on is uncovered: compute, networking, the persistent data store, secrets, and monitoring. |
| **Gap** | No operated environment is reproducible, reviewable, diffable or recoverable from the repository. This is the structural blocker beneath most other findings — there is no artifact in which to express multi-AZ placement, encryption keys, backup retention, scaling policies, alarms or tags. |
| **Recommendation** | Author a single Terraform or CDK stack as the first infrastructure deliverable, covering: VPC with public/private subnets across two AZs; ECS Fargate cluster with `api` and `worker` services from the existing image; ALB or API Gateway; RDS PostgreSQL Multi-AZ with `storage_encrypted` and `backup_retention_period`; Secrets Manager entries for the four database roles, the JWT key and the payment token; CloudWatch log groups with retention; latency and error-rate alarms; and provider-level `default_tags`. Keep `booking_lab/run.py` exactly as it is — it is a correct and valuable disposable test fixture, and it should not be conflated with or replaced by the deployment definition. |
| **Evidence** | `booking_lab/run.py`; repository file inventory (`booking_lab/{README.md,auth.py,.dockerignore,Dockerfile,requirements.txt,run.py,service.py,images.lock.json,schema.sql}`, `.gitignore`, `LICENSE`) confirming no IaC files exist |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **High** · Priority P1 · Effort Low · Phase 1 |
| **Finding** | No CI/CD exists. There is no `.github/` directory, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`, no `appspec.yml` and no CodePipeline definition. The image build (`docker build -t {prefix}-app`) happens inside `booking_lab/run.py` as part of the test run and is never published to a registry. The documented workflow in `booking_lab/README.md` is a single manual command: `python3 booking_lab/run.py e2e --output .local/db-e2e.json`. |
| **Gap** | Nothing is automated: no build, no test execution, no image publish, no deploy, no rollback. The repository's 17-case durability acceptance suite — which verifies exactly the properties most likely to regress under refactoring — never runs unless a human remembers to run it. |
| **Recommendation** | Add a pull-request workflow that (a) builds the image, (b) runs `python3 booking_lab/run.py e2e --output .local/db-e2e.json` on a runner with a Docker daemon, (c) fails the build on non-zero exit, and (d) uploads the evidence JSON as a build artifact. This is the single highest-leverage change available in this repository and is a small amount of work because the suite is already self-contained, self-isolating (unique resource prefix per run) and already emits machine-readable evidence. Then extend the same pipeline with the security steps described under SEC-Q7, image publish to ECR, and a deploy stage once IaC exists. |
| **Evidence** | `booking_lab/README.md`; `booking_lab/run.py` (`main()` CLI, `Lab.setup` `docker build`); absence of `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `appspec.yml` |

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | Python, documented as requiring 3.11+ (`booking_lab/README.md`), running on a digest-pinned official `python` image (`booking_lab/images.lock.json`, `booking_lab/Dockerfile`). Python has first-class AWS SDK coverage and a deep cloud-native ecosystem, so the language axis is modern. The framework axis lags: there is no web framework at all — the HTTP layer is `http.server.BaseHTTPRequestHandler`/`ThreadingHTTPServer` from the standard library, and JWT handling is hand-rolled on `hmac`/`base64` in `booking_lab/auth.py` rather than using a vetted library. The single third-party dependency is `psycopg[binary]==3.3.6`, which is the current major line. No AWS SDK (`boto3`) is present. |
| **Gap** | The stdlib HTTP server provides no routing, no middleware, no request validation framework, no structured logging integration, no OpenAPI generation, and no connection limiting — all of which are reimplemented by hand in `Handler.dispatch` (regex path matching, manual method dispatch, manual content-type and size checks). Hand-rolled JWT verification, while carefully written here, carries ongoing maintenance and cryptographic-review burden. |
| **Recommendation** | Keep Python. Replace the stdlib HTTP layer with a maintained ASGI framework (FastAPI or Starlette) behind an ASGI server, which brings routing, validation, structured error handling, OpenAPI generation (closing APP-Q5) and bounded concurrency, and preserves the existing handler logic almost verbatim. Replace the hand-rolled verifier in `booking_lab/auth.py` with a maintained JWT library once asymmetric keys or an external IdP are introduced (see SEC-Q4). Add `boto3` only where managed services are actually adopted. |
| **Evidence** | `booking_lab/README.md`; `booking_lab/requirements.txt`; `booking_lab/Dockerfile`; `booking_lab/images.lock.json`; `booking_lab/service.py` (`Handler`, `main()`); `booking_lab/auth.py` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P1 · Effort Medium · Phase 2 |
| **Finding** | A single deployable unit containing three logical services. `booking_lab/service.py` holds the booking API, the synthetic payment provider (`Handler.payments`) and the recovery/outbox worker, selected at runtime by `sys.argv[1]` (`api` | `payments` | `worker`) from one image. All tables live in the single `public` schema of a single database. Data isolation is nevertheless enforced — and tested — at the privilege layer: `booking_lab/schema.sql` revokes all default public access, creates four roles (`booking_app`, `payment_app`, `audit_writer`, `audit_reader`) with table-level and even column-level grants, and `booking_lab/run.py::rights()` asserts that `payment_app` cannot read `bookings`, `booking_app` cannot read `audit_events` or create tables, and no runtime role can `UPDATE` or `DELETE` audit rows. Cross-service communication is over HTTP (`PAYMENT_URL`), not shared tables, and there are no cross-module joins. |
| **Gap** | The boundaries exist as privilege policy rather than as deployable or schema boundaries, which is what holds this at Score 2 rather than 3: all services share one `public` schema in one database, and the payment provider — which in any operated deployment is an external third party — is in-process code in the same file as its own caller. The three modes cannot be versioned, released, scaled or rolled back independently, and there is no package structure within the 302-line module. |
| **Recommendation** | Promote the existing role grants into per-service schemas (`booking`, `payments`, `audit`) so isolation is structural rather than policy-only, and split `booking_lab/service.py` into packages along the lines the grants already describe. Extract the payment provider into its own repository, image and database — it is already an HTTP boundary with its own credential and its own table, so this is a bounded change. Do **not** split the booking saga itself: `operations`, `bookings` and `outbox` must commit in one local transaction for the compensation and crash-recovery guarantees to hold. See the Decomposition Strategy section for the full approach. |
| **Evidence** | `booking_lab/service.py` (`main()` mode dispatch, `Handler.payments`, `recover()`, `deliver()`); `booking_lab/schema.sql` (`REVOKE`/`GRANT` block); `booking_lab/run.py` (`rights()`, `Lab.start` role-per-mode wiring); `booking_lab/Dockerfile` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P2 · Effort Medium · Phase 2 |
| **Finding** | *Archetype-calibrated (`stateful-crud`).* A genuine mix. Async is used for the flows that cross a service boundary and for failure recovery: the transactional outbox decouples audit delivery (`emit()` in-transaction, `deliver()` out-of-band), and the worker's `recover()` resumes any operation persisted in `('NEW','CHARGED','COMPENSATING','CANCELLING')` without a client present. The remaining synchronous dependency is the inline `payment()` HTTP call in the request path, which is deliberately bounded (4-second HTTP timeout, 3-second connect timeout, 10-second statement timeout, 8-second lock timeout) and fails closed: on any transport fault the handler returns `503` with `{'error':'temporarily_unavailable','retry_same_idempotency_key':True}` while the durable intent remains in the database for the worker to complete. `booking_lab/run.py::provider_outage()` proves the provider can be stopped mid-flight and the operation still reaches `CONFIRMED` once the provider returns. |
| **Gap** | Cross-service state propagation to the audit sink goes through a direct second-database insert rather than a managed event bus, so adding a consumer requires code change. The payment call remains in the client-facing path, so provider latency is client-visible even though correctness is preserved. |
| **Recommendation** | Publish outbox events to EventBridge or SQS instead of inserting directly into the audit database, which decouples the audit consumer entirely. Optionally make the payment step fully async by returning `202` with an operation URI on first POST and letting the worker drive the charge — but note this is a deliberate API-contract trade-off, not a defect: the current design's synchronous-with-durable-fallback behaviour gives callers an immediate `201` in the normal case and is a reasonable choice for a booking API. |
| **Recommendation note (archetype)** | The `stateful-crud` column was applied. Score 4 would require 50%+ async for cross-service state propagation or async availability for all long-running operations; Score 3 is "mix of async and sync with async for key workflows", which matches precisely. The archetype mattered: for a `stateless-utility` this question would have been recorded as Not Evaluated (sync is correct by design), and for an `orchestrator` the inline synchronous provider call in a coordination path would have been treated far more harshly as an anti-pattern. As a `stateful-crud` that owns its data and calls exactly one downstream provider, the observed mix is close to appropriate. |
| **Evidence** | `booking_lab/service.py` (`emit()`, `deliver()`, `recover()`, `payment()`, `db()` timeouts, `Handler.dispatch` 503 path); `booking_lab/run.py` (`provider_outage()`, `pending()`, `audit_outage()`) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P2 · Effort Medium · Phase 3 |
| **Finding** | *Archetype-calibrated (`stateful-crud`).* No operation can run unbounded: `db()` sets `connect_timeout=3`, `statement_timeout=10000` and `lock_timeout=8000`; `payment()` uses a 4-second HTTP timeout; `Handler.dispatch` sets an 8-second socket timeout. Any operation that cannot complete inside those bounds is persisted in an intermediate state and completed asynchronously by the worker — `booking_lab/run.py::pending()` demonstrates a refund-provider outage leaving the operation durably `COMPENSATING` and the worker driving it to `COMPENSATED` after the fault clears, and `crash()`/`refund_crash()` demonstrate recovery after the API process exits mid-saga. |
| **Gap** | There is no client-facing status resource for an in-flight operation. A caller that receives `503` must re-POST with the same `Idempotency-Key` to learn the outcome; there is no `GET /operations/{id}` returning the persisted `operations.status`, and no callback or webhook. The worker's recovery is also unprioritised and unbounded in attempts — `recover()` takes the first 100 pending operations by `id` with a fixed 0.25s loop and no backoff or attempt ceiling, so a permanently failing operation retries forever and silently (`print('recovery_pending')`). |
| **Recommendation** | Expose a read-only operation-status endpoint backed by `operations.status`/`response_code`/`response_body`, which the data model already supports with no schema change, and document the `503` + `retry_same_idempotency_key` contract alongside it. Add an attempt counter and exponential backoff to `recover()`, with a terminal state and an alarm for operations that exceed the ceiling, so stuck work surfaces to an operator instead of looping. |
| **Recommendation note (archetype)** | The `stateful-crud` column was applied, where Score 4 requires all operations over 30 seconds to be async jobs with status polling or callbacks. No operation here can reach 30 seconds, and durable async completion already exists — but client-visible status polling does not, which places this at Score 3 rather than 4. Under a `stateless-utility` archetype this question would have been recorded Not Evaluated (no long-running operations by design); as a `stateful-crud` owning a multi-step money-adjacent saga, the absence of a status surface is a real, if moderate, gap. |
| **Evidence** | `booking_lab/service.py` (`db()` timeout options, `payment()` timeout, `Handler.dispatch` socket timeout and 503 response, `recover()`, `main()` worker loop); `booking_lab/run.py` (`pending()`, `crash()`, `refund_crash()`) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | There is no API versioning. Routes are matched as unversioned literals and a single regex in `booking_lab/service.py::Handler.dispatch`: `/bookings`, `/bookings/[a-f0-9]{64}`, `/health/live`, `/health/ready`, plus `/charge` and `/refund` on the provider. No `/v1/` path segment, no `Accept-Version` or other version header is read, and no version query parameter is accepted. The only version marker anywhere is the cosmetic `server_version = 'BookingLab/1'` response header. No OpenAPI/Swagger/AsyncAPI/GraphQL specification exists in the repository, and no changelog file. |
| **Gap** | Any change to request validation or response shape breaks every consumer simultaneously, with no negotiation path and no deprecation window. This is a sharper risk than usual here because the request contract is strict and exact — `Handler.dispatch` rejects any payload whose key set is not exactly `{'itinerary','amount'}` and whose itinerary does not match `[A-Z]{3}-[A-Z]{3}` — so even an additive field change is a breaking change for existing callers, and the `Idempotency-Key` fingerprint (a SHA-256 over the canonicalised payload) means a payload-shape change also invalidates replay equivalence for in-flight keys. |
| **Recommendation** | Introduce a version segment (`/v1/bookings`) before any external consumer exists, keeping the current paths as aliases if needed. Publish an OpenAPI document describing the exact request contract, the error codes (`400 invalid_request`, `401 unauthorized`, `403 forbidden`, `402 payment_declined`, `404 booking_not_found`, `405 method_not_allowed`, `409 idempotency_payload_mismatch` / `booking_failed_payment_refunded`, `503 temporarily_unavailable`), the `Idempotency-Key` and `X-Correlation-ID` headers, and the replay semantics — all of which are currently discoverable only by reading `Handler.dispatch`. Adopting an ASGI framework (APP-Q1) makes the specification generated rather than hand-maintained. |
| **Evidence** | `booking_lab/service.py` (`Handler.server_version`, `Handler.dispatch` route matching and payload validation, `create()` fingerprint computation); absence of `openapi.*`, `swagger.*`, `*.graphql` or changelog files in the repository |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | Endpoints are supplied as environment variables with no dynamic discovery. `booking_lab/service.py` reads `os.environ['PAYMENT_URL']` in `payment()` and `os.environ['DATABASE_URL']`/`os.environ['AUDIT_DATABASE_URL']` in `db()`. `booking_lab/run.py::Lab.start` materialises those values into a per-container `.env` file, resolving the provider as `http://{prefix}-payments:8080` — Docker's built-in container-name DNS on the internal network. No AWS Cloud Map / ECS Service Discovery, Consul, Istio, or API catalog is used, and no client-side resolution, health-aware endpoint selection, or retry-across-instances logic exists. |
| **Gap** | The provider is a single fixed address: `payment()` has no instance-level failover, so if that one endpoint is unreachable every charge attempt fails (correctly, into the retryable `503` path) until the address becomes healthy again. Endpoints are fixed at container start, so relocating a dependency requires a restart. |
| **Recommendation** | Keep configuration-driven endpoints — this is the right level of indirection for a service with one dependency — but resolve them through a discovery-backed name rather than a hard-coded host. On ECS, register the payment service in AWS Cloud Map and point `PAYMENT_URL` at the service-discovery DNS name, so instance health and replacement are handled below the application; use the RDS endpoint name (not an instance address) for `DATABASE_URL`. Add bounded retry with jitter inside `payment()` for idempotent charge/refund calls, which the provider's advisory-lock-guarded idempotency already makes safe. |
| **Evidence** | `booking_lab/service.py` (`db()`, `payment()` environment reads); `booking_lab/run.py` (`Lab.start` `PAYMENT_URL`/`DATABASE_URL`/`AUDIT_DATABASE_URL` construction, `Lab.env`) |

### Data Platform Modernization (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 — Mature |
| **Finding** | The service has no unstructured or document data surface, and its storage choice is correct for the data it actually holds. Every persisted value is structured relational data defined in `booking_lab/schema.sql` — `text`, `integer`, `uuid`, `timestamptz` columns under explicit `CHECK` constraints — with the only semi-structured values being the two `jsonb` columns `operations.payload` and `operations.response_body`, which store a validated two-field request body (`{'itinerary','amount'}`) and the canonical API response. Both are written through `psycopg.types.json.Jsonb` and queried as values, not parsed as documents. There are no file uploads, no binary blobs, no PDF/image handling, no document-parsing libraries (`booking_lab/requirements.txt` contains only `psycopg[binary]==3.3.6`), and no filesystem writes other than the test harness's evidence and log files under `.local/` (gitignored). No S3 bucket or object-storage dependency exists, and none is needed. |
| **Gap** | N/A — there is no unstructured-data surface to modernise. Scoring this question as a gap would be a false positive: the absence of S3 reflects the absence of unstructured data, not a storage anti-pattern. |
| **Recommendation** | N/A — no action. Retain `jsonb` for the request payload and response snapshot; it is the correct choice given the payload is both validated on ingress and fingerprinted for idempotency. Should document attachments (itinerary PDFs, receipts) ever be added, store them in S3 with server-side encryption and keep only the object key in PostgreSQL rather than widening the `jsonb` columns. |
| **Evidence** | `booking_lab/schema.sql`; `booking_lab/service.py` (`Jsonb` usage in `create()`, `result()`, `advance()`); `booking_lab/requirements.txt`; `.gitignore` (`.local/`) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P2 · Effort Low · Phase 3 |
| **Finding** | Data access is centralised at the connection layer and confined to a single module. Every connection in the codebase is created by one factory, `booking_lab/service.py::db(name='DATABASE_URL')`, which uniformly applies `autocommit=True`, `row_factory=dict_row`, `connect_timeout=3`, `statement_timeout=10000` and `lock_timeout=8000` — so no code path can accidentally open an unbounded or inconsistently configured connection, and the audit sink is reached through the same factory with a different variable name (`db('AUDIT_DATABASE_URL')`). `psycopg` is imported in exactly one file. All queries are parameterised (`%s` placeholders) with no string interpolation of user input. |
| **Gap** | There is no repository or DAO abstraction above the connection factory: SQL statements are written inline in the business functions (`create()`, `cancel()`, `advance()`, `transition()`, `result()`, `recover()`, `deliver()`) and in the HTTP handler itself (`Handler.dispatch` executes `SELECT id,itinerary,amount,status FROM bookings ...` and the readiness probe runs its own `SELECT`), and `Handler.payments` embeds the provider's `charges` queries directly. Table knowledge is therefore spread across the module, and the saga state machine cannot be unit-tested without a live database. |
| **Recommendation** | Extract a thin persistence module exposing intention-named operations (`load_operation`, `insert_operation`, `set_status`, `append_outbox`, `list_bookings_for_principal`, `claim_undelivered`) and keep the saga functions free of SQL. This is low-effort given the small statement count, makes the state machine unit-testable without Docker, and creates the single place to add instrumentation when distributed tracing is introduced (OPS-Q1). Preserve the existing `db()` timeout defaults and parameterisation discipline unchanged — both are strengths. |
| **Evidence** | `booking_lab/service.py` (`db()`, inline SQL in `create()`, `cancel()`, `advance()`, `transition()`, `result()`, `recover()`, `deliver()`, `Handler.dispatch`, `Handler.payments`); `booking_lab/requirements.txt` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P1 · Effort Low · Phase 2 |
| **Finding** | The engine is pinned, immutably, but opaquely. `booking_lab/images.lock.json` fixes `postgres@sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea` and `booking_lab/run.py` consumes it directly (`PG_IMAGE`), pulls it, and records `RepoDigests` into the evidence file — a stronger guarantee than a floating tag, since the exact binary is reproducible. The harness also captures `SHOW server_version;` and `SHOW synchronous_commit;` at runtime as evidence. No `aws_rds_*` engine version parameter exists because no managed database exists. |
| **Gap** | The digest does not disclose the PostgreSQL major version to a reader of the repository — it has to be discovered by running the suite and reading the emitted evidence — so EOL status cannot be assessed from the repository alone and is effectively untracked. There is no documented engine-update procedure covering downtime windows, rollback or risk acknowledgement, and digest pinning without an update mechanism means security patches to the base image are never picked up (see SEC-Q6). |
| **Recommendation** | Record the human-readable major version alongside the digest in `booking_lab/images.lock.json` (e.g. a `postgres_version` field) so EOL can be assessed by inspection, and document a short update procedure: how the digest is refreshed, how the suite validates the new engine, and what the rollback is. On the managed database, pin `engine_version` explicitly in IaC, enable only minor-version auto-upgrade, and track the PostgreSQL community EOL date for the chosen major against the RDS deprecation calendar. |
| **Evidence** | `booking_lab/images.lock.json`; `booking_lab/run.py` (`IMAGES`/`PG_IMAGE`, `Lab.setup` image pull and `base_images` evidence, `postgres_version`/`synchronous_commit` evidence capture) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P1 · Effort Medium · Phase 3 |
| **Finding** | Business logic lives in the application layer, but the schema and the concurrency design are meaningfully coupled to PostgreSQL. `booking_lab/schema.sql` contains one `CREATE FUNCTION fail_booking_insert() ... LANGUAGE plpgsql` and one `CREATE TRIGGER test_booking_insert BEFORE INSERT ON bookings` — present solely so the test administrator can inject a real insert failure (there is deliberately no HTTP fault endpoint), and gated on a row in the `faults` table. Beyond those, the engine-specific constructs are load-bearing rather than cosmetic: `pg_advisory_lock` (session-scoped, deliberately held across local commits *and* the external payment call, per the comment in `locked()`), `pg_advisory_xact_lock(17, ...)` in the provider on a separate lock namespace, `FOR UPDATE SKIP LOCKED` for outbox draining, `ON CONFLICT ... DO NOTHING` for audit deduplication, `jsonb`, `clock_timestamp()`, and column-level `GRANT SELECT(id)`. |
| **Gap** | No business logic needs extraction — correctly, the saga is in Python — but the correctness model is portable only to PostgreSQL. Advisory locks in particular are the mechanism that makes "eight concurrent requests across two replicas produce exactly one charge" true, and they are also the construct most at risk from infrastructure changes: a transaction-level connection pooler in front of the database silently breaks session-scoped advisory locks without any error. The `plpgsql` trigger also means production and test schemas differ unless the trigger is explicitly excluded. |
| **Recommendation** | Keep PostgreSQL — do not treat this as a reason to change engines. Instead (1) document the advisory-lock dependency as an explicit architectural constraint, including its incompatibility with transaction-mode pooling, and add it as a pre-cutover check for RDS Proxy or PgBouncer; (2) separate the fault-injection function and trigger into a `schema.test.sql` applied only by the harness, so the deployed schema contains no test artefacts; (3) retain `SKIP LOCKED` and `ON CONFLICT` — both are standard-adjacent and supported across RDS/Aurora PostgreSQL. |
| **Evidence** | `booking_lab/schema.sql` (`fail_booking_insert()`, `test_booking_insert` trigger, `faults` table, column-level grant); `booking_lab/service.py` (`locked()`, `Handler.payments` `pg_advisory_xact_lock`, `deliver()` `FOR UPDATE SKIP LOCKED` and `ON CONFLICT DO NOTHING`); `booking_lab/run.py` (`fault()`, `concurrent()`) |

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (surface-flag) |
| **Finding** | Gate: `has_iac_provisioning_aws_resources` is `false`. Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organisation, not per-application. This repository contains no AWS-provisioning IaC at all — no `aws_cloudtrail`, no `aws_config_*`, no `aws_guardduty_*`, no Organization SCPs, and equally no application-level AWS resources — so there is no account-level scope here against which to evaluate CloudTrail. SEC-Q1 does not apply; CloudTrail evaluation belongs in a foundation/account-level infrastructure repository. |
| **Gap** | N/A |
| **Recommendation** | N/A for this repository. Worth recording separately, however: the service does implement a strong *application-level* audit trail that is independent of CloudTrail — `audit_events` is append-only by privilege design (`audit_writer` holds `INSERT` plus `SELECT(id)` only, `audit_reader` holds `SELECT`, and no runtime role can `UPDATE` or `DELETE`), events carry `principal` and `correlation_id` attribution, and `booking_lab/run.py::rights()` proves no runtime role can rewrite history. That property should be preserved when the trail moves to a managed store. |
| **Evidence** | `booking_lab/schema.sql` (`audit_events`, `audit_writer`/`audit_reader` grants); `booking_lab/run.py` (`rights()`); absence of `*.tf`, `cdk.json`, CloudFormation templates and any `aws_*`/`AWS::*` resource in the repository |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **High** · Priority P1 · Effort Low · Phase 1 |
| **Finding** | No encryption at rest is configured on any data surface. The PostgreSQL data directory lives on a plain Docker volume (`docker volume create {prefix}-db-data`, mounted at `/var/lib/postgresql/data`) with no volume-level or filesystem-level encryption and no `aws_kms_key` or `kms_key_id` anywhere in the repository. The `pg_dump` output produced by `dump_restore()` is written in cleartext to `{work}/workshop.sql`, and the per-container `.env` files written by `Lab.env` contain the four database role passwords, the symmetric `JWT_KEY` and the `PAYMENT_TOKEN` in cleartext on disk. Filesystem permissions are the only control applied: the work directory is created `mode=0o700` and both the dump and the `.env` files are `chmod(0o600)`. |
| **Gap** | Payment-adjacent records — principals, itineraries, amounts, charge states, refund counts — and the immutable audit trail all sit unencrypted at rest, as do live credentials and the JWT signing key. Permissions-only protection does not survive volume snapshot, host compromise, disk disposal, or backup copy, and provides no key rotation or access audit trail. |
| **Recommendation** | On the managed database set `storage_encrypted = true` with a customer-managed KMS key and ensure automated snapshots inherit it. Move the four role passwords, `JWT_KEY` and `PAYMENT_TOKEN` into Secrets Manager (see SEC-Q5) so they are never materialised to disk; inject them at task start rather than via `--env-file`. Encrypt any dump artifact before it leaves the host, and write it to an S3 bucket with SSE-KMS and a lifecycle policy rather than to local disk. Document a key rotation policy. The existing `0700`/`0600` discipline is good hygiene and should be kept as defence in depth, not as the control. |
| **Evidence** | `booking_lab/run.py` (`Lab.__init__` work-directory creation, `Lab.env` password/JWT/token materialisation, `Lab.setup` `docker volume create` and `-v ...:/var/lib/postgresql/data`, `dump_restore()` dump write); `.gitignore`; absence of any KMS or `storage_encrypted` configuration in the repository |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P2 · Effort Medium · Phase 2 |
| **Finding** | Per-request token authentication is enforced on every business endpoint, and enforced carefully. `booking_lab/service.py::Handler.dispatch` extracts the `Authorization: Bearer` value and calls `auth.verify(token, os.environ['JWT_KEY'], required)` where `required` is `bookings:read` for `GET` and `bookings:write` otherwise. `booking_lab/auth.py::verify` validates the HMAC-SHA256 signature with `hmac.compare_digest`, rejects any header other than exactly `{'alg':'HS256','typ':'JWT'}` (closing algorithm-confusion and `alg:none`), and checks `iss`, `aud`, `exp`, `nbf`, `iat` and a `sub` pattern before scope evaluation, returning `403` for insufficient scope versus `401` for invalid tokens. Token length is capped at 4096 bytes. The service refuses to start if `JWT_KEY` is shorter than 32 characters. The payment provider independently requires its own bearer token compared with `hmac.compare_digest`. `booking_lab/run.py::auth()` proves rejection of missing, expired, wrong-audience, wrong-issuer, not-yet-valid, wrong-key and insufficient-scope tokens, and asserts no charge was created in any rejected case. Authorisation is also data-scoped: `cancel()` and the list/read paths filter by `principal`, and `booking_lab/run.py::isolation()` proves `agent-b` cannot read or cancel `agent-a`'s booking. |
| **Gap** | Score 4 requires intentionally public endpoints to be fronted by a gateway with throttling and request validation; `/health/live` and `/health/ready` are unauthenticated and there is no gateway at all (INF-Q6 = 1), so there is no throttling, no per-client rate limit, and no protection against token-guessing or request-flood abuse. `/health/ready` also opens a database connection on every unauthenticated call, which is a cheap amplification vector. Tokens are symmetric HS256 with a single shared secret, so any holder of `JWT_KEY` can mint tokens for any principal, and verification is hand-rolled rather than library-backed. |
| **Recommendation** | Front the service with API Gateway or an ALB and apply a per-client throttle; keep `/health/*` reachable only from the load balancer's security group rather than from any caller. Move to asymmetric signing (RS256/ES256) with a JWKS endpoint so the API only ever holds a public key, which also removes the shared-secret minting risk. Retain the existing claim-validation strictness and the `403`-vs-`401` distinction — both are correct and worth carrying forward verbatim into whatever framework replaces the handler. |
| **Evidence** | `booking_lab/service.py` (`Handler.dispatch` auth and scope selection, `Handler.payments` bearer comparison, `main()` `JWT_KEY` length check, `/health/*` routes); `booking_lab/auth.py` (`verify`); `booking_lab/run.py` (`auth()`, `isolation()`) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Medium · Phase 2 |
| **Finding** | The application manages its own authentication end to end with no external identity provider. `booking_lab/auth.py` is both the issuer (`encode()`, minting tokens with `iss='booking-lab'`, `aud='booking-api'`, a 300-second lifetime and a hard-coded default scope `bookings:read bookings:write`) and the verifier (`verify()`), using one symmetric HMAC key supplied as `JWT_KEY`. `booking_lab/run.py` generates that key with `secrets.token_hex(32)` per run and mints tokens for the `agent-a` and `agent-b` principals. There is no `aws_cognito_*` resource, no OIDC discovery or JWKS endpoint, no SAML configuration, no federation, and no SSO. The module docstring itself states the symmetric JWT is "confined to this local lab", so this is an acknowledged scope boundary rather than an oversight. |
| **Gap** | Because the same symmetric key both signs and verifies, any component holding `JWT_KEY` — including the API itself — can mint a token for an arbitrary principal, so principal attribution in `operations.principal` and `audit_events.principal` is only as trustworthy as every holder of that key. There is no central place to revoke a principal, rotate signing material without a coordinated restart, enforce MFA, apply conditional access, or audit token issuance. Scope assignment is a code default rather than an identity-provider policy, and there are no refresh semantics. |
| **Recommendation** | Introduce a centralised IdP and reduce the application to a verifier only: Amazon Cognito user pools (or an existing enterprise OIDC provider) issuing asymmetrically-signed access tokens, with the API validating against the published JWKS and mapping the `scope`/`client_id` claim to the existing `bookings:read` / `bookings:write` checks. For machine-to-machine callers — which is what `agent-a`/`agent-b` represent — use the OAuth2 client-credentials flow with per-client scopes so each caller has its own revocable identity. Keep `booking_lab/auth.py::encode()` as a test fixture only; it should never be a deployment-time issuer. Treat `PAYMENT_TOKEN` similarly — a static shared bearer is acceptable for a synthetic double but should become a rotated credential or SigV4/mTLS for a real provider. |
| **Evidence** | `booking_lab/auth.py` (module docstring, `encode()`, `verify()`); `booking_lab/service.py` (`Handler.dispatch` `JWT_KEY` verification, `main()` key-length guard); `booking_lab/run.py` (`Lab.__init__` key and token generation); absence of any Cognito/OIDC/SAML configuration in the repository |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P1 · Effort Low · Phase 1 |
| **Finding** | There are **no plaintext credentials committed anywhere in the repository**, which is the key positive finding: every secret is generated at runtime with `secrets.token_hex` in `booking_lab/run.py::Lab.__init__` (a 32-byte `JWT_KEY`, a 32-byte `PAYMENT_TOKEN`, and 24-byte passwords for `postgres`, `booking_app`, `payment_app`, `audit_writer` and `audit_reader`), never hard-coded. `.gitignore` excludes `.env*` and `.local/`, so generated material cannot be committed by accident. The harness is also careful not to leak: `docker()` truncates stderr and its comment states it never prints container environments or bootstrap SQL/passwords, and `Handler.log_message` is overridden to a no-op specifically so bearer tokens and request bodies are never logged. However, secrets are delivered as plaintext environment variables through `.env` files on disk (`Lab.env`, `chmod 0600`) consumed via `docker run --env-file`, and read at runtime from `os.environ`. No Secrets Manager, Parameter Store, or Vault integration exists, and there is no rotation of any kind. |
| **Gap** | Production credentials would live in environment variables and on-disk `.env` files with no encryption, no rotation, no access audit trail, and no revocation path. Environment variables are visible to anything that can read the process environment or inspect the container, and the symmetric `JWT_KEY` in particular is a token-minting capability (see SEC-Q4), so its blast radius exceeds that of a normal database password. Because the harness generates fresh secrets per run, nothing exercises rotation, so a rotation path has never been designed. |
| **Recommendation** | Store the four database role passwords, `JWT_KEY` and `PAYMENT_TOKEN` in AWS Secrets Manager, and inject them into the ECS task definition via `secrets` (valueFrom) so the plaintext never reaches a file on disk. Enable automated rotation on the database credentials (Secrets Manager's managed RDS rotation) and on `PAYMENT_TOKEN`; for `JWT_KEY`, the asymmetric migration recommended in SEC-Q4 removes the shared secret entirely and is the better fix. Keep the runtime-generation approach in `booking_lab/run.py` for tests — it is the right design for a disposable fixture — and keep the existing `.gitignore` entries, the `0600`/`0700` permissions, the stderr truncation, and the `log_message` suppression, all of which are genuine strengths. |
| **Evidence** | `booking_lab/run.py` (`Lab.__init__` `secrets.token_hex` generation, `Lab.env` file write and `chmod(0o600)`, `Lab.start` `--env-file`, `docker()` stderr truncation); `booking_lab/service.py` (`db()`, `payment()`, `Handler.dispatch` `os.environ` reads, `Handler.log_message` no-op); `.gitignore` (`.env*`, `.local/`) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity **Low** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | Runtime hardening is unusually thorough for a lab. `booking_lab/Dockerfile` runs as a non-root numeric user (`USER 65532:65532`), installs from a pinned requirement with `--no-cache-dir`, copies only the three needed source files, and sets `PYTHONDONTWRITEBYTECODE=1`; `booking_lab/.dockerignore` excludes everything except those files, so no test harness, git metadata or local state enters the image. Base images are pinned by digest, not tag (`booking_lab/images.lock.json`), and the harness records the resolved `RepoDigests` and the built image ID as evidence. Containers are launched with `--read-only --cap-drop=ALL --security-opt=no-new-privileges`, a `tmpfs /tmp:rw,noexec,nosuid,size=16m`, and `--memory 256m --cpus 1 --pids-limit 128` when the host supports cgroups — with an explicit message when it does not. Patching and scanning, however, are entirely absent: no `.github/dependabot.yml`, no `renovate.json`, no `.snyk`, no Inspector, no ECR image scanning, no `pip-audit`, and no SSM patch baseline. |
| **Gap** | Digest pinning without an update mechanism is a double edge: it guarantees reproducibility but also guarantees that base-image CVE fixes are never picked up, because nothing watches for a newer digest. There is no vulnerability signal at all on either the Python base image or `psycopg[binary]`, and no hardened-base-image choice (the stock `python` image rather than a distroless or minimal variant). |
| **Recommendation** | Add a dependency-update bot (`.github/dependabot.yml` covering `pip` and `docker`) so the pinned digests are proposed for refresh rather than frozen, and let the existing E2E suite gate each bump — this converts pinning from a liability back into a strength. Enable Amazon ECR enhanced scanning (or Trivy in the pipeline) on the built image, and add `pip-audit` as a pipeline step. Consider a distroless or `-slim` base to shrink the attack surface. Carry every existing runtime flag into the ECS task definition: `readonlyRootFilesystem: true`, dropped capabilities, non-root user, and explicit CPU/memory limits — these translate directly and should not be lost in the move. |
| **Evidence** | `booking_lab/Dockerfile`; `booking_lab/.dockerignore`; `booking_lab/images.lock.json`; `booking_lab/run.py` (`Lab.start` security options, `Lab.setup` resource-limit detection and `base_images`/`app_image_id` evidence); absence of `.github/dependabot.yml`, `renovate.json`, `.snyk` and any scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Low · Phase 1 |
| **Finding** | There is no security validation in any pipeline, because there is no pipeline (INF-Q11 = 1). No SAST tool (SonarQube, Semgrep, Bandit, CodeGuru Reviewer) is configured; no dependency scanning (`pip-audit`, Dependabot, Renovate, Snyk) is configured — there is no `.github/dependabot.yml`, `renovate.json` or `.snyk` file; and no container image scanning is configured. The repository's only automated verification is the functional/durability suite in `booking_lab/run.py`, which — notably — does include real negative security testing (token forgery and expiry rejection in `auth()`, cross-principal access denial in `isolation()`, and database privilege containment in `rights()`), but no vulnerability scanning of code or dependencies. |
| **Gap** | A vulnerability in `psycopg[binary]==3.3.6`, in the pinned Python base image, or a newly introduced injection or crypto flaw in the hand-rolled JWT verifier would reach a deployment undetected. There is no gate that could block on a critical finding, and the repository's reliance on hand-written security-sensitive code (HMAC verification, path regex matching, SQL construction) is precisely the profile where SAST has the highest yield. |
| **Recommendation** | Add to the pipeline created under INF-Q11, in this order: (1) `pip-audit` against `booking_lab/requirements.txt`; (2) a SAST step — Bandit as the lowest-friction Python option, or Semgrep with the Python security ruleset — configured to fail on high-severity findings; (3) container image scanning via ECR scan-on-push or Trivy, failing on critical CVEs; (4) Dependabot for `pip` and `docker` ecosystems so pinned digests are refreshed. Keep the existing security-behaviour tests in `booking_lab/run.py` as the complement to scanning — they verify properties no scanner can, and the two are not substitutes. |
| **Evidence** | `booking_lab/run.py` (`auth()`, `isolation()`, `rights()` — the only automated security verification present); `booking_lab/requirements.txt`; absence of `.github/workflows/`, `.github/dependabot.yml`, `renovate.json`, `.snyk`, and any SAST or image-scanning configuration |

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P2 · Effort Medium · Phase 2 |
| **Finding** | Correlation identity exists and is persisted, but there is no tracing instrumentation and propagation stops at the service boundary. `booking_lab/service.py::Handler.dispatch` accepts an `X-Correlation-ID` header (generating a UUID when absent) and threads it through `create()` and `cancel()` into `operations.correlation_id`, every `outbox` row via `emit()`, and every `audit_events` row via `deliver()` — so a durable, queryable correlation trail exists end to end through the data layer, and `booking_lab/run.py::happy()` asserts that `principal||':'||correlation_id` on the `booking.confirmed` event matches the caller's supplied correlation ID exactly. Cancellation is deliberately re-attributed to its own request's correlation ID rather than inheriting the creation one. However: no OpenTelemetry or X-Ray SDK is present (`booking_lab/requirements.txt` has only `psycopg[binary]`), no `traceparent` or `X-Amzn-Trace-Id` header is read or emitted, and `payment()` sends only `operation_id` and `amount` to the provider — the correlation ID is **not** forwarded, so the provider's work cannot be joined to the caller's trace. |
| **Gap** | There are no spans, no latency attribution, and no cross-service trace join. Diagnosing a slow or failing booking requires manually querying `operations`, `outbox` and `audit_events` by correlation ID; the time spent inside `payment()` versus inside the database is not measurable. The worker's recovery actions carry the original operation's correlation ID but produce no trace of their own, so asynchronous completion is invisible. Logging is also minimal by design — `Handler.log_message` is a deliberate no-op to avoid leaking bearer tokens, and the only operational output is three unstructured `print()` lines (`request_retry_pending`, `worker_retry_pending`, `recovery_pending`) with no timestamp, level, correlation ID or structure. |
| **Recommendation** | Add OpenTelemetry (or the X-Ray SDK) with auto-instrumentation for the HTTP server, the outbound `urllib` call and `psycopg`, mapping the existing `correlation_id` onto the trace as a span attribute so the durable trail and the trace join on one key. Forward the correlation ID (and `traceparent`) on the `payment()` request so provider spans attach to the caller's trace. Replace the three `print()` calls with structured JSON logs carrying correlation ID, principal, operation ID and outcome — while preserving the existing discipline of never logging tokens or request bodies, which is a genuine strength and must not be lost in the change. |
| **Evidence** | `booking_lab/service.py` (`Handler.dispatch` `X-Correlation-ID` handling, `create()`, `cancel()`, `emit()`, `deliver()`, `payment()` request headers, `Handler.log_message`, `print()` calls); `booking_lab/run.py` (`happy()` correlation assertion); `booking_lab/requirements.txt` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | Gate: `has_api_surface` is `true`, so this question is evaluated. No monitoring artifacts of any kind exist in the repository — no CloudWatch alarms (there is no IaC in which to define them), no latency or error-rate thresholds, no SLO definition file, no error-budget tracking, and no dashboard definition. The service exposes `/health/live` and `/health/ready` (the latter proving database reachability with a real query, returning `503` when the database is down), which is a correct liveness/readiness split, but nothing in the repository consumes those endpoints outside the test harness, and a health probe is not an SLO. Response-time bounds exist in the code as timeouts (4s payment, 8s socket, 10s statement) — these are protective limits, not declared service objectives. The only durable quality measurements are the test-run artifacts in the evidence JSON: per-case `duration_seconds` and the five correctness invariants (`captured_without_confirmed_booking`, `confirmed_without_captured_payment`, `pending_operations`, `undelivered_audit_events`, `audit_missing_attribution`), all asserted to be zero. |
| **Gap** | There is no declared availability or latency target for `POST /bookings`, the critical user journey, and therefore no way to know whether the service is meeting expectations or degrading. More specifically for this service, the properties that actually matter operationally are already *measurable* but not *monitored*: the count of operations stuck in `('NEW','CHARGED','COMPENSATING','CANCELLING')` and the count of undelivered outbox rows are exactly the signals that would indicate saga or audit degradation, and both have working queries sitting unused in the test harness. |
| **Recommendation** | Define three SLOs and alarm on them once IaC exists: availability and p99 latency for `POST /bookings`; saga completion — zero operations pending beyond a defined age; and audit freshness — zero outbox rows undelivered beyond a defined age. Promote the five invariant queries from `booking_lab/run.py` into continuously evaluated CloudWatch custom metrics, since they are already written and already proven to be the right correctness signals. Track an error budget against the availability objective. |
| **Evidence** | `booking_lab/service.py` (`/health/live`, `/health/ready` handlers, timeout settings); `booking_lab/run.py` (`run_tests()` invariant queries and `case()` durations); absence of any alarm, dashboard or SLO definition in the repository |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | The service publishes no metrics at all — neither business nor infrastructure. There is no `cloudwatch.put_metric_data` call, no StatsD/Prometheus client, no metrics endpoint, and no metrics library in `booking_lab/requirements.txt`. Runtime output is limited to three unstructured `print()` lines in `booking_lab/service.py` (`request_retry_pending`, `worker_retry_pending`, `recovery_pending`), none of which is counted or aggregated. Business-relevant quantities are all present in the database and queried by the test harness only: bookings confirmed, charges captured versus refunded, declined payments, operations by status, and audit event counts. |
| **Gap** | None of the outcomes that define whether this service is working — booking success rate, payment decline rate, compensation (refund-after-failed-booking) rate, cancellation rate, saga pending depth, audit delivery lag — is emitted anywhere. The compensation rate is particularly important and particularly invisible: a rising rate of `COMPENSATED` operations means customers are being charged and refunded rather than served, which is a business-visible failure that no current signal would surface. |
| **Recommendation** | Emit custom CloudWatch metrics at the points where the saga already knows the outcome — in `result()` and at the `201` return in `advance()` — covering booking created, payment declined, booking compensated, booking cancelled, and operation retry/503 returned. Add gauge metrics from the worker loop for pending-operation depth and undelivered-outbox depth. Dimension by nothing more than status initially; avoid `principal` as a dimension to prevent cardinality explosion. Build one dashboard combining these with the SLOs from OPS-Q2. |
| **Evidence** | `booking_lab/service.py` (`print()` calls, `result()`, `advance()`, worker loop in `main()`); `booking_lab/requirements.txt`; `booking_lab/run.py` (business quantities queried only as test assertions) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Low · Phase 2 |
| **Finding** | No alerting exists in any form. There are no CloudWatch alarms (no IaC), no anomaly detectors, no composite alarms, no SNS topic, and no PagerDuty/OpsGenie integration anywhere in the repository. Failure handling is entirely in-process and silent to operators: `Handler.dispatch` catches `RuntimeError`/`psycopg.Error`/`OSError` and returns `503` after a single unstructured `print('request_retry_pending ' + type(error).__name__)`; the worker loop catches every exception and prints `worker_retry_pending`; `recover()` prints `recovery_pending` per failed operation and continues. Nothing escalates, counts, or notifies. |
| **Gap** | Every failure mode the service is explicitly engineered to survive is also invisible while it is happening. A payment provider outage, a database outage, a permanently stuck saga operation, or a blocked audit delivery (the exact scenario `audit_outage()` tests, where `audit_writer` loses `INSERT` and the outbox silently backs up) would all be handled correctly by the code and reported to nobody. Because the worker retries indefinitely with no attempt ceiling, an operation that can never complete produces an unbounded stream of identical prints and no signal. |
| **Recommendation** | Once IaC exists, alarm on: 5xx rate and p99 latency for the API; `/health/ready` failures; pending-operation count above a threshold or age; undelivered-outbox count above a threshold or age; and payment decline rate deviation. Use CloudWatch anomaly detection for latency and error rate rather than fixed thresholds, since booking traffic is likely to be diurnal. Route to SNS with an on-call destination. Replace the `print()` statements with structured logs and derive metric filters from them so the existing failure-detection logic becomes an alerting source rather than being discarded. |
| **Evidence** | `booking_lab/service.py` (`Handler.dispatch` exception handler, `main()` worker exception handler, `recover()` exception handler); `booking_lab/run.py` (`audit_outage()`, `pending()` demonstrating silent-degradation scenarios); absence of any alarm, SNS topic or alerting integration in the repository |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (surface-flag) |
| **Finding** | Gate: `has_deployed_workload` is `false`. No deployed workload exists in this repository — `booking_lab/Dockerfile` is present but no deployment manifest references it (no Kubernetes/Helm/Kustomize, no `docker-compose.yml`, no Terraform/CDK/CloudFormation/SAM), and there is no CodeDeploy configuration, Argo Rollouts manifest, ALB weighted target group, or traffic-shifting definition. Deployment strategy cannot be assessed from source code alone. OPS-Q5 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A for scoring. Note for sequencing: because no deployment definition exists anywhere, deployment strategy should be designed in from the start of the IaC work (INF-Q10) rather than retrofitted — ECS rolling deployment with a deployment circuit breaker and automatic rollback is the minimum, with CodeDeploy blue/green for the API service once an ALB exists. This is tracked under the Move to Modern DevOps pathway. |
| **Evidence** | `booking_lab/Dockerfile`; `booking_lab/run.py`; absence of `.github/workflows/`, `appspec.yml`, `*.tf`, `cdk.json`, CloudFormation templates, `Chart.yaml`, `kustomization.yaml`, `docker-compose*.yml` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity **Medium** · Priority P1 · Effort Low · Phase 1 |
| **Finding** | Coverage is exceptional; automated execution is absent. `booking_lab/run.py` builds the real image, starts a real PostgreSQL container, real payment provider, two real API replicas and a real worker on isolated per-run Docker networks, then runs 17 integration cases against live HTTP and live SQL: token rejection across issuer/audience/expiry/nbf/signature/scope; happy-path create with correlation attribution; idempotent replay and payload-conflict detection across replicas; cross-principal identity isolation and identity-scoped idempotency; eight concurrent requests across two replicas yielding exactly one charge and one booking; real insert failure after charge producing a refund with no orphan booking; refund-provider outage leaving durable `COMPENSATING` state and worker-driven recovery; process crash after external commit reconciling without double charge; payment provider outage retaining intent and recovering; crash after refund recovering without a second refund; declined payment creating no booking; cancel/refund idempotency with original create-response preservation; audit delivery failure with durable outbox drain after restart; audit redelivery deduplication; runtime-role inability to rewrite audit or cross-service tables; database outage failing closed with volume survival across restart; and a real `pg_dump`/restore into a separate database verified by per-table row hashes. It closes with five global invariant assertions and emits machine-readable evidence. No test is skipped or mocked — fault injection is via a real database trigger and real process exits. However, there is no CI pipeline (INF-Q11 = 1), so none of this runs automatically; execution requires a human running `python3 booking_lab/run.py e2e` on a machine with a Docker daemon. |
| **Gap** | The rubric's discriminator between a 4 and a 2 is pipeline execution, and that is the entire gap here: the suite is never run consistently or automatically, so it provides no regression protection on change. Secondary gaps: there are no unit tests, so the saga state machine cannot be exercised without Docker and a full ~1-minute environment build; and the suite is all-or-nothing with no way to run a single case while debugging. |
| **Recommendation** | Wire `python3 booking_lab/run.py e2e --output .local/db-e2e.json` into a pull-request pipeline on a Docker-capable runner and fail the build on non-zero exit — this alone moves the score to 4 and is a small amount of work, because the harness is already self-isolating (unique resource prefix, loopback-only ephemeral ports, no global prune) and already emits an evidence artifact to upload. Add an optional case-name filter argument so a single scenario can be run during debugging. Then add unit tests for `advance()` and `auth.verify()` against a fake store so fast feedback does not require Docker. |
| **Evidence** | `booking_lab/run.py` (`Lab.setup`, `run_tests()` with 17 `case()` invocations, invariant block, `finish()` evidence emission); `booking_lab/README.md`; absence of `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (surface-flag) |
| **Finding** | Gate: `has_deployed_workload` is `false`. There is no running system in this repository for which incident response could be defined — no deployed compute, no deployment manifest referencing `booking_lab/Dockerfile`, and no IaC defining a live environment. No SSM Automation documents, Lambda remediation functions, or runbook files exist. OPS-Q7 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A for scoring. Worth recording for the operated deployment: a substantial amount of self-healing behaviour is already implemented *in the application* rather than in external automation — the worker continuously reconciles any operation left in `('NEW','CHARGED','COMPENSATING','CANCELLING')`, the outbox drains automatically after an audit outage clears, and the API fails closed and instructs clients to retry with the same idempotency key. When runbooks are written they should document and build on these mechanisms (how to observe pending depth, how to clear a stuck operation) rather than duplicate them. |
| **Evidence** | `booking_lab/service.py` (`recover()`, `deliver()`, `main()` worker loop, `Handler.dispatch` 503 retry contract); `booking_lab/run.py` (`pending()`, `audit_outage()`); absence of runbook files, SSM Automation documents, and any deployment definition |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity **Medium** · Priority P2 · Effort Low · Phase 3 |
| **Finding** | There is no observability ownership of any kind, because there are no observability assets to own. No dashboard definitions, no alarms, no SLO files, and no `CODEOWNERS` file exist anywhere in the repository. There is no team attribution, no owner metadata, and no on-call reference. The documentation (`booking_lab/README.md`) describes how to run the acceptance suite and what each source file does, but names no owner, no escalation path and no monitoring responsibility. |
| **Gap** | Nobody is identified as responsible for detecting or responding to degradation of this service. There is no per-service dashboard, no alarm with a named owner, and no SLO with team attribution — so even once monitoring exists (OPS-Q2, OPS-Q4), signals would have no defined recipient. |
| **Recommendation** | Add a `CODEOWNERS` file covering `booking_lab/` and, once created, the IaC and observability directories, so monitoring configuration has a named reviewer. Define the service's dashboard and alarms in the same IaC stack as the service itself so ownership follows the code, and tag both the AWS resources and the alarms with `Owner` and `Team` (see OPS-Q9). Record the owning team, escalation path and the SLOs from OPS-Q2 in the README alongside the existing run instructions. |
| **Evidence** | `booking_lab/README.md`; absence of `CODEOWNERS`, dashboard definitions, alarm definitions and SLO files anywhere in the repository |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (surface-flag) |
| **Finding** | Gate: `has_iac_provisioning_aws_resources` is `false`. This repository provisions no AWS resources — no Terraform `aws_*` resources, no CloudFormation `AWS::*` types, no CDK app, no SAM template — so there are no resources to tag and no tagging governance surface to assess. Tagging governance belongs in the repository that owns the AWS infrastructure. OPS-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A for scoring. Note for the IaC work under INF-Q10: establish tagging at the outset via Terraform provider `default_tags` (or CDK `Tags.of(app)`) with `Application`, `Environment`, `Owner`, `Team` and `CostCenter`, activate the corresponding cost allocation tags, and enforce with an AWS Config `required-tags` rule and an Organizations Tag Policy. The harness's existing per-run resource-prefix convention (`db-lab-{uuid}`) is a good precedent for consistent resource identification and can inform the naming standard. |
| **Evidence** | `booking_lab/run.py` (per-run resource prefix convention); absence of `*.tf`, `cdk.json`, CloudFormation templates, SAM templates and any `aws_*`/`AWS::*` resource in the repository |

---

## Learning Materials

Learning resources for the three **Triggered** pathways:

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Classification Count Reconciliation

Counts derived by tallying the emitted `findings[]` array, not by a running counter.

| Severity | Derived count | Question IDs |
|----------|---------------|--------------|
| **High** | 4 | INF-Q2 (1, core), INF-Q10 (1, core), INF-Q11 (1, core), SEC-Q2 (1, core) |
| **Medium** | 19 | Score 2 (10): INF-Q1, INF-Q3, INF-Q4, INF-Q8, APP-Q2, APP-Q6, DATA-Q4, SEC-Q5, OPS-Q1, OPS-Q6. Score 1 non-core (9): INF-Q6, INF-Q7, APP-Q5, SEC-Q4, SEC-Q7, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q8 |
| **Low** | 8 | INF-Q5, APP-Q1, APP-Q3, APP-Q4, DATA-Q2, DATA-Q3, SEC-Q3, SEC-Q6 (all score 3) |
| **Total findings** | **31** | 4 + 19 + 8 = 31 |

Question accounting: 31 findings + 1 pass (DATA-Q1, score 4) + 5 Not Evaluated (INF-Q9, SEC-Q1, OPS-Q5, OPS-Q7, OPS-Q9) = **37**. Every question appears in exactly one of `findings[]` or `evaluations[]`.

Self-check results:
1. `high_count` (4) equals the number of High entries in `findings[]` ✔
2. `medium_count` (19) equals the number of Medium entries ✔
3. `low_count` (8) equals the number of Low entries ✔
4. 4 + 19 + 8 = 31 = `len(findings[])` ✔

Tier from counts: 4 High → "2-11 High → Remediation Required". Band from `overall_score` 2.02 → 1.5–2.4 → Needs Work ≡ Remediation Required. `classification_consistency_check` = **consistent**.

`overall_score` recomputed after all category means were finalised: (1.60 + 2.33 + 3.00 + 1.83 + 1.33) / 5 = **2.02**.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `booking_lab/service.py` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q3, SEC-Q4, SEC-Q5, OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q7 | The whole application: `db()` connection factory with timeouts, `opid()`/`create()` idempotency, `locked()` advisory locking, `payment()` provider client, `advance()`/`transition()`/`result()` durable saga, `emit()`/`deliver()` transactional outbox, `recover()` reconciliation, `Handler` HTTP routing/auth/validation, `Handler.payments` synthetic provider, `main()` mode dispatch and `ThreadingHTTPServer` bootstrap. |
| `booking_lab/run.py` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, APP-Q2, APP-Q3, APP-Q4, APP-Q6, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q2, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q5, OPS-Q6, OPS-Q7, OPS-Q9 | Ephemeral Docker test harness and 17-case E2E acceptance suite: image build, network/volume/role creation, runtime secret generation, container security options and resource limits, per-case assertions (auth, replay, isolation, concurrency, compensation, crash recovery, provider outage, audit outage, privilege containment, dump/restore), and evidence emission. |
| `booking_lab/schema.sql` | INF-Q2, INF-Q3, INF-Q4, APP-Q2, DATA-Q1, DATA-Q4, SEC-Q1 | Relational schema with `CHECK`-constrained saga state machine, `operations`/`bookings`/`outbox`/`audit_events`/`charges`/`faults` tables, the `plpgsql` fault-injection function and trigger, and the `REVOKE`/`GRANT` block defining the four runtime roles and the append-only audit trail. |
| `booking_lab/Dockerfile` | INF-Q1, INF-Q9, APP-Q1, APP-Q2, OPS-Q5, SEC-Q6 | Container definition: digest-pinned Python base, minimal file copy, non-root `USER 65532:65532`, `PYTHONDONTWRITEBYTECODE`, default `api` command. |
| `booking_lab/images.lock.json` | INF-Q1, INF-Q2, APP-Q1, DATA-Q3, SEC-Q6 | Immutable base-image digest pins for `postgres` and `python`. |
| `booking_lab/requirements.txt` | INF-Q4, APP-Q1, DATA-Q1, DATA-Q2, OPS-Q1, OPS-Q3, SEC-Q7 | Sole dependency `psycopg[binary]==3.3.6`; evidences the absence of AI/ML, messaging, metrics, tracing and web-framework libraries. |
| `booking_lab/auth.py` | APP-Q1, SEC-Q3, SEC-Q4 | Hand-rolled symmetric HS256 JWT issuer (`encode`) and verifier (`verify`) with issuer/audience/expiry/nbf/iat/subject/scope validation. |
| `booking_lab/README.md` | INF-Q11, APP-Q1, OPS-Q6, OPS-Q8 | Documents Python 3.11+/Docker requirements and the single manual run command; evidences absence of owner, SLO, CI and AI/LLM intent. |
| `booking_lab/.dockerignore` | INF-Q10, SEC-Q6 | Deny-all-then-allow list restricting the build context to the five shipped files. |
| `.gitignore` | DATA-Q1, SEC-Q2, SEC-Q5 | Excludes `.local/`, `__pycache__/`, `*.pyc`, `.env*` — prevents generated secrets and local state from being committed. |
| `LICENSE` | — | MIT license for the original lab code. |
| *(absence)* `*.tf`, `*.tfvars`, `cdk.json`, `template.yaml`, `*.cfn.*` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, SEC-Q1, SEC-Q2, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q9 | Searched repository-wide; no infrastructure-as-code of any kind found. |
| *(absence)* `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `appspec.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | Searched repository-wide; no CI/CD pipeline definition found. |
| *(absence)* `Chart.yaml`, `values.yaml`, `kustomization.yaml`, `docker-compose*.yml`, `k8s/`, `manifests/` | INF-Q1, INF-Q9, INF-Q10, OPS-Q5 | Searched repository-wide; no deployment manifest found — basis for `has_deployed_workload=false`. |
| *(absence)* `.github/dependabot.yml`, `renovate.json`, `.snyk` | DATA-Q3, SEC-Q6, SEC-Q7 | Searched canonical paths; no dependency-update or scanning configuration found. |
| *(absence)* `CODEOWNERS`, dashboard/alarm/SLO definitions | OPS-Q2, OPS-Q4, OPS-Q8 | Searched repository-wide; no observability assets or ownership attribution found. |
| *(absence)* `openapi.*`, `swagger.*`, `*.graphql`, changelog | APP-Q5 | Searched repository-wide; no API specification or changelog found. |

---

*Generated by AWS Transform · Modernization Readiness Analysis*
