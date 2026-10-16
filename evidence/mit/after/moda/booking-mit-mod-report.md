# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | booking-mit |
| **Date** | 2026-10-16 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application (auto-detected) |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | — |
| **Tags** | — |
| **Context** | Original MIT Python booking service (`booking_lab/`) with PostgreSQL, a synthetic HTTP payment provider and a recovery/audit worker. Goal: a simple reproducible container-based workshop with a clear path to an operated deployment. No pre-existing EKS cluster or platform pipeline may be assumed; prefer the smallest compatible runtime. `run.py` executes integration tests with disposable isolated Docker resources. Current runnable implementation is distinguished from proposed infrastructure throughout. Application code was not modified. |
| **Overall Score** | 1.99 / 4.0 |

**Repo Type Justification**: Application source with deployable entry points (`booking_lab/service.py` `main()`, `booking_lab/audit.py` `__main__`), a dependency manifest (`booking_lab/requirements.txt`) and a `booking_lab/Dockerfile` are present; there is no multi-service sibling layout and no resource-provisioning IaC. Classified as `application`.

**Archetype Justification**: The service owns persistent state in PostgreSQL (`booking_lab/schema.sql`, `psycopg` connections in `booking_lab/service.py`) and exposes create/read/cancel operations on business entities with per-principal scoping. It calls one downstream provider (payments) plus an audit sink, which is below the 3+ coordinated-downstream bar for `orchestrator`. Classified as `stateful-crud`.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true, has_iac_provisioning_aws_resources=false

Flag rationale: PostgreSQL runs as a container with a named Docker volume and the SQLite audit ledger uses its own volume (`booking_lab/run.py`), giving both a persistent data store and an at-rest surface. A built container image is the unit of execution (`booking_lab/Dockerfile`), HTTP endpoints exist (`booking_lab/service.py`, `booking_lab/audit.py`), and two API replicas (`api-a`, `api-b`) run concurrently. No Terraform/CDK/CloudFormation/SAM exists anywhere in the repository, so no AWS resources are provisioned from this repo.

**Classification Tier**: 🟠 Remediation Required — rule matched: "2-11 High → Remediation Required".

This repo has 5 High findings, 19 Medium findings and 11 Low findings. The matched rule is "2-11 High → Remediation Required". Note that MOD classification is deliberately softer than the Agentic Readiness Analysis on a single High finding: in ARA one High is an agent-deployment gate, whereas in MOD one High is typically a single modernization gap and maps to Pilot-Ready. Five High findings — self-managed database, no CI/CD, no encryption at rest, no deployment strategy and local-filesystem-only retention of audit artifacts — place this repository in Remediation Required.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.64 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Critical |
| Security Baseline (SEC) | 1.83 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.50 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **1.99 / 4.0** | **🟠 Needs Work** | **Critical** |

### Scoring Notes

- INF: (2+1+2+2+3+1+1+2+1+2+1) / 11 = 18/11 = **1.64**
- APP: (3+3+3+3+1+2) / 6 = 15/6 = **2.50**
- DATA: (1+3+3+3) / 4 = 10/4 = **2.50**
- SEC: (1+3+1+2+3+1) / 6 = 11/6 = **1.83** (SEC-Q1 Not Evaluated — excluded)
- OPS: (2+1+1+1+1+2+3+1) / 8 = 12/8 = **1.50** (OPS-Q9 Not Evaluated — excluded)
- Overall: (1.64+2.50+2.50+1.83+1.50) / 5 = 9.97/5 = **1.99**

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q11: CI/CD Automation | 1 | No pipeline definition of any kind — `run.py` must be invoked manually by a human with Docker access | Every build, test and release is a manual act; blocks the Modern DevOps pathway and makes all other modernization steps unverifiable |
| 2 | INF-Q2: Managed Databases | 1 | PostgreSQL runs as a self-managed container with no managed failover, patching or backup automation | Operational burden and data-loss exposure; triggers the Move to Managed Databases pathway |
| 3 | SEC-Q2: Encryption at Rest | 1 | No encryption configured for the PostgreSQL volume or the SQLite audit ledger; protection is POSIX mode 0600 only | Signed audit records and booking data are readable from the host volume; blocks any compliance-bearing deployment |
| 4 | OPS-Q5: Deployment Strategy | 1 | Containers are started directly by `run.py`; no canary, blue/green, rolling or traffic-shifting artifact exists | No safe release path to an operated environment; regressions reach all replicas at once |
| 5 | DATA-Q1: Unstructured Data Storage | 1 | Audit snapshots, checkpoints, pg_dump output and container logs are written only to local disk (`.local/db-lab-*`) and container volumes | The repo's own `AUDIT.md` identifies an immutable object archive as a prerequisite; without it retention claims cannot be met |

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | Primary trigger APP-Q2 < 3 not met (APP-Q2 = 3 — enforced module boundaries via HTTP contracts and per-role table grants) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 2 is below threshold, but the supporting condition fails: container definitions exist (`booking_lab/Dockerfile`, pinned `images.lock.json`). The workload is already containerized; only orchestration is missing |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 3 and no commercial engine detected — PostgreSQL and SQLite are already open source |
| 4 | Move to Managed Databases | **Triggered** | High | Medium | INF-Q2 = 1 (PostgreSQL self-managed in a container). DATA-Q3 = 3 strengthens the case (digest-pinned image, no documented version-update procedure) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 2 is below threshold, but the contextual guard blocks: no streaming, ETL, data-pipeline or analytics artifacts were found (searched `booking_lab/` for Kafka/Kinesis/Glue/Airflow signals — none) |
| 6 | Move to Modern DevOps | **Triggered** | High | Medium | INF-Q11 = 1 (no CI/CD) and INF-Q10 = 2 (no IaC). Supporting: OPS-Q5 = 1, OPS-Q6 = 2 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent evidenced in the repository (no AI-related signal terms in dependencies, source, configuration, IaC or documentation) |

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current database topology (INF-Q2).** Two independent data stores are self-managed:
- PostgreSQL in a container started by `booking_lab/run.py` (`docker run -d --name <prefix>-db ... -v <prefix>-db-data:/var/lib/postgresql/data`), image pinned by digest in `booking_lab/images.lock.json`. It holds `operations`, `bookings`, `outbox`, `audit_events`, `charges` and `faults` (`booking_lab/schema.sql`).
- SQLite in the independent audit sink, on its own volume (`AUDIT_PATH=/audit/ledger.sqlite`, `booking_lab/audit.py`), with WAL and `synchronous=FULL`.

There is no managed failover, no automated patching, no automated backup and no point-in-time recovery. Durability today rests on a single host volume plus manually invoked `pg_dump` and SQLite `backup()` inside the E2E (`booking_lab/run.py`).

**Engine versions and EOL (DATA-Q3).** The engine is pinned by image digest only; the major version is discovered at runtime (`SHOW server_version;`). No documented upgrade/rollback window exists.

**Data access patterns (DATA-Q2).** Connections are centralized in `db()` in `booking_lab/service.py` and `connect()` in `booking_lab/audit.py`, so repointing a connection string is a small, contained change — this materially lowers migration effort.

**Recommended targets (smallest compatible runtime first, no pre-existing cluster assumed):**
- Amazon RDS for PostgreSQL (Multi-AZ, Single-DB-instance class to start) as the direct replacement for the container. The schema uses standard PostgreSQL only (`jsonb`, `pg_advisory_lock`, `FOR UPDATE SKIP LOCKED`, `clock_timestamp()`) and is portable as-is. Aurora PostgreSQL is the next step up when read scaling or faster failover is needed.
- For the audit ledger, the relevant managed primitive is not a database but immutable object storage: Amazon S3 with Object Lock (compliance mode) for signed records and externally retained checkpoints, which is exactly the control `booking_lab/AUDIT.md` says must exist in an operated deployment. Amazon QLDB-style append-only semantics are already implemented in-process; keep the cryptographic chain and add the archive.
- Secrets for the managed instance move to AWS Secrets Manager with rotation (see SEC-Q5).

**Representative AWS services:** Amazon RDS for PostgreSQL, Aurora PostgreSQL, AWS Secrets Manager, Amazon S3 (Object Lock), AWS Backup.
**Migration tools:** AWS DMS and AWS SCT are not required for the PostgreSQL→RDS move (homogeneous, no proprietary SQL); `pg_dump`/`pg_restore` — already exercised in the E2E — is sufficient.

**Immediate actions:**
1. Parameterize `DATABASE_URL`/`AUDIT_DATABASE_URL` sourcing so the same image runs against RDS without code change (already true — only env wiring is needed).
2. Define the RDS instance, its subnet group, security group and backup retention in IaC (closes INF-Q2, INF-Q8, INF-Q9, INF-Q10 together).
3. Enable KMS encryption on the instance and on the audit archive bucket (closes SEC-Q2).

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC coverage (INF-Q10 = 2).** No Terraform, CDK, CloudFormation, SAM, Helm chart, Kubernetes manifest or Compose file exists. Environment construction is a Python script that drives the Docker CLI (`booking_lab/run.py`): it creates an internal network, a front network, two volumes, a database, an audit sink, a payments process, two API replicas and a worker, with pinned image digests and generated per-run secrets. This is reproducible and scripted — materially better than ClickOps — but it is a disposable local lab, not a declarative definition of an operated environment, and it covers no networking, data, monitoring or DR resources for a deployed target.

**Current CI/CD state (INF-Q11 = 1).** No `.github/workflows/`, `buildspec.yml`, `appspec.yml`, `Jenkinsfile` or pipeline definition anywhere in the repository. The E2E is valuable but runs only when a human with Docker daemon access invokes `python3 booking_lab/run.py e2e`.

**Deployment strategy gap (OPS-Q5 = 1).** Release is `docker run`/`docker restart`. There is no traffic shifting, no canary weight, no rollback artifact. The E2E does prove restart tolerance and fail-closed behaviour during a database outage, which is the behavioural prerequisite for rolling deployments — the mechanism is simply absent.

**Testing gap (OPS-Q6 = 2).** Coverage is genuinely strong: 18 integration cases against a real PostgreSQL, including concurrent duplicate requests across two replicas, injected insert failure with refund, process crash after an external commit, payment-provider outage, refund crash, audit-delivery failure with outbox drain, role-privilege denial, dump/restore row-hash comparison and signed-ledger tamper/truncation/restore verification. The gap is purely that none of it runs in a pipeline.

**Recommended toolchain (no pre-existing platform pipeline assumed):**
- Start with a single pipeline that builds the image, runs `run.py e2e` against disposable Docker resources, and publishes the digest. GitHub Actions or AWS CodeBuild both satisfy this; CodeBuild keeps credentials and the registry inside AWS.
- Add dependency and container scanning to the same pipeline (closes SEC-Q7) and Dependabot/Renovate for `requirements.txt` and base-image digests (closes part of SEC-Q6, which digest pinning otherwise freezes).
- Express the operated environment declaratively. The smallest compatible runtime for this workload is Amazon ECS on Fargate: three task definitions (api, worker, payments provider) plus the audit sink, an ALB in front of the api service, RDS for PostgreSQL behind it. This avoids standing up EKS, which the context explicitly does not assume.
- Adopt ECS rolling deployments with health checks first (`/health/live`, `/health/ready` already exist in `booking_lab/service.py`), then CodeDeploy blue/green with ALB target-group shifting.

**Representative AWS services:** AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy, Amazon ECR (with scan-on-push), Amazon ECS/Fargate, AWS CloudFormation or AWS CDK, Amazon CloudWatch.

**Immediate actions:**
1. Commit a pipeline that runs the existing E2E on every change — this converts an excellent test suite into an enforced gate.
2. Author IaC for the target environment (ECS services, ALB, RDS, secrets, log groups, alarms).
3. Replace direct container starts with a deployment action that supports health-gated rollout and rollback.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | The workload is containerized (`booking_lab/Dockerfile`, non-root `USER 65532`, pinned base image digest) and runs as five container roles — database, audit sink, payments provider, two API replicas and a worker — but all are started directly against a local Docker daemon by `booking_lab/run.py`. There is no managed container orchestration (no ECS/EKS task or service definition, no Kubernetes manifest) and no serverless function. No `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` or `aws_instance` resource exists anywhere in the repository. |
| **Gap** | Container images exist but no managed orchestration platform schedules, scales, heals or places them. Compute lifecycle is a developer laptop / CloudShell Docker daemon. |
| **Recommendation** | Define the four process roles as Amazon ECS on Fargate services (api, worker, payments, audit sink) — the smallest compatible managed runtime that requires no pre-existing cluster. Keep the single image with its `CMD` override per task, which the current design already supports via `service.py <mode>`. |
| **Evidence** | `booking_lab/Dockerfile`, `booking_lab/run.py` (lines ~160–200, `docker run` invocations), `booking_lab/images.lock.json` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: High · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | PostgreSQL is self-managed: `booking_lab/run.py` runs the pinned `postgres@sha256:...` image with a local named volume `<prefix>-db-data:/var/lib/postgresql/data`, creates roles and applies `booking_lab/schema.sql` at bootstrap. The authoritative audit ledger is a self-managed SQLite file on a second volume (`booking_lab/audit.py`, `AUDIT_PATH`). No managed database resource is defined. |
| **Gap** | No managed failover, automated patching, automated backup or PITR for either store. Durability depends on one host's volumes. |
| **Recommendation** | Move the application database to Amazon RDS for PostgreSQL with Multi-AZ; the schema uses only standard PostgreSQL constructs so the move is homogeneous. Pair the signed SQLite ledger with an S3 Object Lock archive for its records and externally retained checkpoints. |
| **Evidence** | `booking_lab/run.py`, `booking_lab/schema.sql`, `booking_lab/audit.py`, `booking_lab/images.lock.json` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 · *archetype-calibrated* |
| **Finding** | The booking saga is a hand-written but genuinely durable state machine: `operations.status` is constrained to `NEW/CHARGED/CONFIRMED/COMPENSATING/COMPENSATED/DECLINED/CANCELLING/CANCELLED` (`booking_lab/schema.sql`) and `advance()` in `booking_lab/service.py` resumes from persisted state, with `pg_advisory_lock` serializing concurrent progress and a recovery worker (`recover()`) re-driving stuck operations. No dedicated orchestration service (Step Functions, Temporal, Camunda) is used. |
| **Gap** | Orchestration semantics — retries, compensation, timeouts, visibility — are encoded in application code and SQL status checks. There is no external execution history, no visual workflow surface and no managed retry/backoff policy. |
| **Recommendation** | Keep the durable-state design (it is the correct foundation) and consider AWS Step Functions for the charge → confirm → compensate sequence if workflow visibility and managed retry become operational requirements. This is a Phase 2 improvement, not a correctness defect. |
| **Evidence** | `booking_lab/service.py` (`advance`, `transition`, `recover`), `booking_lab/schema.sql` (status CHECK constraint) |

*Archetype calibration note:* scored against the `stateful-crud` column. For that archetype, a structured in-code state machine without a dedicated orchestration service is Score 2. Had this service been classified `orchestrator`, the same evidence would not change the score materially; had it been `stateless-utility`, the question would have been recorded as Not Evaluated (archetype-N/A) because no multi-step workflow would exist.

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 · *archetype-calibrated* |
| **Finding** | Cross-boundary event propagation uses a transactional outbox implemented in PostgreSQL: `emit()` inserts into `outbox` in the same transaction as the state change, and `deliver()` claims rows with `FOR UPDATE SKIP LOCKED`, posts each event to the independent audit sink over HTTP, writes the PostgreSQL projection, and only then stamps `delivered_at` (`booking_lab/service.py`). Redelivery is idempotent by event UUID (`booking_lab/audit.py` `append()`). There is no managed broker — no SQS, SNS, EventBridge, MSK or Kinesis — and no self-managed Kafka/RabbitMQ either; the queue is a database table polled every 250 ms by the worker. |
| **Gap** | The messaging substrate is self-managed (a DB table plus a polling loop). Throughput, fan-out, dead-lettering, backoff and consumer scaling must all be hand-built, and the polling worker is a single point of delivery. |
| **Recommendation** | Retain the transactional outbox — it is the correct pattern for atomicity — but relay it to Amazon SQS (with a DLQ) or EventBridge so delivery, retry and fan-out are managed. This preserves the existing exactly-once-by-UUID semantics while removing the hand-built transport. |
| **Evidence** | `booking_lab/service.py` (`emit`, `deliver`), `booking_lab/schema.sql` (`outbox` table), `booking_lab/audit.py` (`append`) |

*Archetype calibration note:* scored against the `stateful-crud` column, where managed messaging for cross-service state changes is the Score 4 bar and a self-managed transport for those flows is Score 2. For a `stateless-utility` or `data-gateway`, synchronous-only communication would have scored 4 and no messaging recommendation would be made.

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P1 · Effort: Medium · Phase: 2 |
| **Finding** | The network surface the repo owns is the Docker topology in `booking_lab/run.py`, and it is deliberately segmented: an `--internal` network carries database, payments, audit and worker traffic with no route to the internet; a separate front network carries only the API replicas; API ports are published to `127.0.0.1` on ephemeral ports only; the audit sink publishes no host port at all and is queried through its own namespace. Containers run `--read-only --cap-drop=ALL --security-opt=no-new-privileges` with a `noexec,nosuid` tmpfs. No `0.0.0.0/0` exposure and no default-VPC-equivalent flat network exists. |
| **Gap** | This segmentation exists only for the disposable local lab. There are no VPC, subnet, security-group, NetworkPolicy or service-mesh definitions for an operated deployment, so the intended topology is not expressed anywhere a deployment can consume. |
| **Recommendation** | Translate the current two-network split into IaC: private subnets for database, worker, payments and audit sink; API tasks behind an ALB with a security group that admits only the ALB; VPC endpoints for S3/Secrets Manager/ECR so no NAT egress is required. |
| **Evidence** | `booking_lab/run.py` (`network create --internal`, `-p 127.0.0.1:{port}:8080`, container hardening options) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 |
| **Finding** | The API is a `ThreadingHTTPServer` bound directly to `0.0.0.0:8080` inside the container and published to a host port (`booking_lab/service.py` `main()`, `booking_lab/run.py` `start()`). There is no API Gateway, AppSync, ALB or CloudFront in front of it. Throttling, request-size limits and auth are implemented in the handler itself (8 KiB body cap, 8 s socket timeout, bearer verification). |
| **Gap** | No managed entry point, so no centralized throttling, WAF, TLS termination, request validation or routing control. Clients reach the service process directly. |
| **Recommendation** | Place an Application Load Balancer in front of the API tasks for TLS termination and health-gated routing, and add Amazon API Gateway if per-client throttling, usage plans and request validation are required. The existing `/health/live` and `/health/ready` endpoints are already suitable as target-group health checks. |
| **Evidence** | `booking_lab/service.py` (`ThreadingHTTPServer(('0.0.0.0',8080), Handler)`), `booking_lab/run.py` (`start`) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 |
| **Finding** | Capacity is fixed and hard-coded: exactly two API replicas (`api-a`, `api-b`) and one worker are started by `booking_lab/run.py`, with static per-container limits (`--memory 256m --cpus 1 --pids-limit 128`, and `512m` for the database). No auto-scaling group, no ECS/Kubernetes scaling policy, no Lambda concurrency setting and no data-tier scaling configuration exists. |
| **Gap** | No mechanism responds to load. The design is horizontally scalable — advisory locks and identity-scoped idempotency are proven correct across replicas by the 8-concurrent-request test — but nothing adds or removes replicas. |
| **Recommendation** | Once the services run on ECS/Fargate, configure Application Auto Scaling target tracking on the api service (request count per target via the ALB) and on the worker (outbox backlog published as a custom CloudWatch metric — a more faithful load signal than CPU for a polling worker). |
| **Evidence** | `booking_lab/run.py` (`resource_options`, fixed `('api-a','api-b')` loop) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 |
| **Finding** | Restore capability is genuinely exercised but not automated. The E2E performs a real `pg_dump`, restores into a separate database and compares per-table row hashes for `operations`, `bookings`, `charges`, `outbox`, `audit_events` and `faults`; it also takes a SQLite `backup()` of the audit ledger into a different file, runs `PRAGMA integrity_check` and re-verifies the restored chain against an externally retained checkpoint (`booking_lab/run.py`, `booking_lab/audit_verify.py`, `booking_lab/AUDIT.md`). There is no scheduled backup, no retention configuration, no PITR and no off-host copy — dumps and checkpoints land in `.local/db-lab-*` on the same machine. |
| **Gap** | Backups are a test artifact, not an operational control: no schedule, no retention policy, no cross-region or off-host replication. `AUDIT.md` states retention is at least 90 days and that this implementation has no automatic purge, so retention is asserted rather than enforced by storage. |
| **Recommendation** | Enable RDS automated backups with an explicit retention period and PITR, add AWS Backup plans, and write audit snapshots plus checkpoints to an S3 bucket with Object Lock and a lifecycle policy. Keep the existing restore-verification steps and run them from the pipeline so restore testing stays continuous. |
| **Evidence** | `booking_lab/run.py` (`dump_restore`, `audit_integrity`), `booking_lab/audit_verify.py`, `booking_lab/AUDIT.md` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 |
| **Finding** | Everything runs on a single host: one PostgreSQL container, one audit sink, one payments process, one worker and two API replicas sharing the same Docker daemon and the same volumes (`booking_lab/run.py`). There is no AZ concept, no replica database, no cross-zone load balancing. Fault behaviour is nonetheless well characterised — the E2E proves the API fails closed with 503 while the database is down and that state survives container restarts — but the failure domain is one machine. |
| **Gap** | No multi-AZ topology for compute or data; a single host or volume loss is total loss. |
| **Recommendation** | Deploy the api and worker services across at least two AZs on Fargate behind a cross-zone ALB, and use RDS Multi-AZ for the database. The audit sink needs the same treatment plus its off-host archive, since it holds the authoritative ledger. |
| **Evidence** | `booking_lab/run.py` (single-daemon container creation, `restart` test case) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | No declarative IaC exists: searched for `*.tf`, `*.tfvars`, CDK entry points, `cdk.json`, CloudFormation/SAM templates, `Chart.yaml`, `kustomization.yaml`, Kubernetes manifests and `docker-compose*.yml` — none are present. Environment construction is imperative Python driving the Docker CLI (`booking_lab/run.py`), with image digests pinned in `booking_lab/images.lock.json` and the schema and role grants declared in `booking_lab/schema.sql`. Source file SHA-256 digests and base-image digests are recorded in the evidence output, so the lab is reproducible. |
| **Gap** | Scripted provisioning covers only a disposable local lab. Nothing defines the operated environment: no networking, data store, entry point, scaling, monitoring, alarm, DNS or secret resources. For the surfaces this repo demonstrably exposes (api entry point, persistent data store, multi-replica compute), in-repo IaC coverage is zero. |
| **Recommendation** | Author CloudFormation or CDK for the target environment — ECS services and task definitions, ALB and target groups, RDS instance and subnet group, security groups, Secrets Manager secrets, CloudWatch log groups and alarms, S3 audit archive. Keep `run.py` as the local integration harness; the two are complementary, not alternatives. |
| **Evidence** | `booking_lab/run.py`, `booking_lab/images.lock.json`, `booking_lab/schema.sql`, absence of `*.tf` / `template.yaml` / `Chart.yaml` / `k8s/` anywhere in the repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: High · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | No pipeline definition exists anywhere in the repository: searched for `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `appspec.yml` and CodePipeline definitions in IaC — none found. The repository root contains only `booking_lab/`, `.gitignore` and `LICENSE`. Build, test and release are a manual `python3 booking_lab/run.py e2e --output .local/db-e2e.json` performed by a human with Docker daemon access (`booking_lab/README.md`). |
| **Gap** | Nothing is automated or enforced. A strong 18-case integration suite exists but no gate requires it to pass before a change is accepted, and no artifact is built, scanned or published reproducibly by a machine. |
| **Recommendation** | Add one pipeline that builds the image, runs `run.py e2e` against disposable Docker resources, records the evidence JSON as a build artifact and publishes the image digest to Amazon ECR. This single step converts the existing suite into an enforced quality gate and unblocks every other modernization action. |
| **Evidence** | `booking_lab/README.md`, absence of `.github/workflows/`, `buildspec.yml`, `Jenkinsfile` at repository root |

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P2 · Effort: Low · Phase: 3 |
| **Finding** | Python is the only language (1,043 lines across `service.py`, `run.py`, `audit.py`, `client.py`, `auth.py`, `audit_verify.py`). `booking_lab/README.md` requires Python 3.11+, the base image is pinned by digest, and the single dependency is current: `psycopg[binary]==3.3.6` (`booking_lab/requirements.txt`). The HTTP layer is the standard library (`http.server.ThreadingHTTPServer`, `BaseHTTPRequestHandler`) and JWT verification is hand-rolled HMAC in `booking_lab/auth.py`. No AWS SDK is present. |
| **Gap** | The language and runtime are modern, but the web layer is a stdlib HTTP server with hand-written routing, parsing and auth rather than a maintained framework — a framework-maturity lag that increases the surface the team must keep correct themselves (and the project accepts this deliberately for teaching purposes). |
| **Recommendation** | No language change is warranted. If the service moves toward an operated deployment, adopt a maintained ASGI framework (FastAPI/Starlette) behind a production server for routing, validation and middleware, and a vetted JWT library in place of `auth.py` for anything beyond fixtures — `auth.py` already documents that it is lab-confined. |
| **Evidence** | `booking_lab/requirements.txt`, `booking_lab/README.md`, `booking_lab/service.py`, `booking_lab/auth.py` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P1 · Effort: Medium · Phase: 3 |
| **Finding** | One image and one codebase deploy as four distinct process roles selected by argv (`service.py api`, `service.py payments`, `service.py worker`, `audit.py`). Boundaries are explicit and enforced at runtime rather than merely conventional: the booking service reaches the payment provider only over HTTP with a bearer token (`payment()` in `booking_lab/service.py`), and `booking_lab/schema.sql` grants each role only its own tables (`booking_app` → `operations,bookings,outbox`; `payment_app` → `charges`; `audit_writer` → INSERT on `audit_events`). The E2E asserts these denials — `payment_app` cannot read `bookings`, `booking_app` cannot read `audit_events` or create tables. The authoritative audit ledger is a fully separate process with its own store and signing key. |
| **Gap** | All roles share a single PostgreSQL instance and a single `public` schema, and ship as one image, so independent deployability and independent scaling of the payment provider are limited. Isolation is enforced by privilege grants rather than by schema or instance separation. |
| **Recommendation** | No decomposition programme is warranted — the boundaries already exist and are tested. When moving to an operated deployment, give the payment provider its own schema (or its own database) and its own image tag so it can be deployed and scaled independently, and keep the HTTP contract as the only coupling. |
| **Evidence** | `booking_lab/service.py` (`main` mode dispatch, `payments`), `booking_lab/schema.sql` (GRANT/REVOKE block), `booking_lab/run.py` (`rights` test case) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P2 · Effort: Medium · Phase: 3 · *archetype-calibrated* |
| **Finding** | Mixed by design. The payment call is synchronous HTTP with a 4 s timeout and explicit ambiguity handling (`payment()` maps 402 to DECLINED and all transport errors to a retryable RuntimeError, never marking a refund early). Audit propagation is asynchronous and durable through the outbox and worker. Compensation and recovery are asynchronous: on a refund outage the API returns 503 with `retry_same_idempotency_key: true` and the worker completes the saga later. |
| **Gap** | The critical charge path still holds a client connection open across an external provider call, so provider latency is caller-visible; cross-service propagation uses a hand-built transport rather than managed async messaging. |
| **Recommendation** | Keep synchronous charge semantics (they are appropriate for a booking confirmation) and move the outbox relay onto managed messaging. Converting the charge itself to async would change the API contract and is not recommended for this archetype. |
| **Evidence** | `booking_lab/service.py` (`payment`, `deliver`, `advance`), `booking_lab/run.py` (`pending`, `provider_outage` test cases) |

*Archetype calibration note:* scored against the `stateful-crud` column, where "mix of async and sync with async for key workflows" is Score 3. Under the `orchestrator` column the same synchronous-fan-out evidence would be penalised more heavily; under `stateless-utility` the question would be Not Evaluated (archetype-N/A) because synchronous request/response would be the correct design by definition.

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P2 · Effort: Medium · Phase: 3 · *archetype-calibrated* |
| **Finding** | No operation is designed to exceed 30 seconds: `connect_timeout=3`, `statement_timeout=10000`, `lock_timeout=8000` on the database, 4 s on provider calls and an 8 s socket timeout on the request (`booking_lab/service.py`). Work that cannot finish inline is not blocked on — it is persisted and resumed by the recovery worker, and the client receives 503 with `retry_same_idempotency_key: true`. |
| **Gap** | Resumption is discoverable only by retrying the original POST with the same idempotency key; there is no job-status resource or callback, so a caller cannot observe in-flight progress of a compensating or pending operation. |
| **Recommendation** | Expose operation state as a retrievable resource (e.g. `GET /operations/{id}`) so callers can poll progress instead of inferring it from repeated POSTs. The durable state needed for this already exists in the `operations` table. |
| **Evidence** | `booking_lab/service.py` (`db` timeouts, `dispatch` 503 branch, `recover`), `booking_lab/schema.sql` (`operations.status`) |

*Archetype calibration note:* scored against the `stateful-crud` column, where asynchronous handling with status polling or callbacks is the Score 4 bar; durable async resumption without a status surface is Score 3. For `stateless-utility` this question would be Not Evaluated (archetype-N/A).

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Low · Phase: 2 |
| **Finding** | Routes are unversioned and matched literally: `/bookings`, `/bookings/{64-hex}`, `/health/live`, `/health/ready` (`booking_lab/service.py` `dispatch`), and the payment provider exposes `/charge` and `/refund` (`payments`). No `/v1/` path segment, no `Accept-Version` or custom version header, no content negotiation and no OpenAPI/AsyncAPI/GraphQL specification exists in the repository. The only version signal is the `Server: BookingLab/1` header. |
| **Gap** | Any breaking change to the request or response contract — and the contract is strict, rejecting unknown body keys outright — breaks all callers simultaneously, with no machine-readable spec for consumers to diff against. |
| **Recommendation** | Introduce a `/v1/` prefix (keeping unversioned paths as aliases during transition) and publish an OpenAPI document generated from or checked against the handler, so the contract that the E2E already enforces becomes consumable by clients. |
| **Evidence** | `booking_lab/service.py` (`dispatch` path matching, `server_version`), absence of `openapi.*` / `swagger.*` / `*.graphql` in the repository |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P2 · Effort: Low · Phase: 3 |
| **Finding** | Endpoints come from environment variables — `DATABASE_URL`, `AUDIT_DATABASE_URL`, `PAYMENT_URL`, `AUDIT_URL` (`booking_lab/service.py`) — injected per run from generated `.env` files mode 0600 (`booking_lab/run.py` `env`/`start`). Resolution relies on Docker's embedded DNS for container names on the internal network. No endpoint is hard-coded in source, but there is no service registry, mesh or Cloud Map namespace either. |
| **Gap** | Externalized configuration without dynamic discovery: topology changes require re-injecting environment variables and restarting consumers. |
| **Recommendation** | Register the services in AWS Cloud Map (ECS Service Connect/Service Discovery) so `PAYMENT_URL` and `AUDIT_URL` resolve through a namespace rather than per-run static values. This is a small change given that endpoints are already fully externalized. |
| **Evidence** | `booking_lab/service.py` (`os.environ['PAYMENT_URL']`, `os.environ['AUDIT_URL']`), `booking_lab/run.py` (`start`, `env`) |

### Data Platform Modernization (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: High · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | Every file-shaped artifact the system produces lives on local disk or a local container volume, never in object storage. `booking_lab/run.py` writes the audit snapshot, the separately retained audit checkpoint, the `pg_dump` output, per-container logs, `review.json` and the generated `.env` files into `.local/db-lab-<id>/`; the signed ledger itself is a SQLite file on a Docker volume (`booking_lab/audit.py`). No S3 bucket, object-storage client or archive target exists anywhere in the repository, and `.gitignore` excludes `.local`, so these artifacts are purely host-local. |
| **Gap** | Retention-bearing artifacts — signed audit records and the external checkpoint that detects tail truncation — have no durable, immutable, off-host home. `booking_lab/AUDIT.md` states the requirement explicitly: an operated deployment "should place the sink and checkpoint archive in a separate administrative boundary ... and an immutable object archive with its retention policy". Today the 90-day retention claim is enforced only by SQL triggers inside a file on one host. |
| **Recommendation** | Add an S3 bucket with Object Lock in compliance mode for audit snapshots and checkpoints, with versioning, a lifecycle policy matching the 90-day minimum and a KMS key; write checkpoints from the pipeline so they are retained outside the sink's administrative boundary, as `AUDIT.md` requires. |
| **Evidence** | `booking_lab/run.py` (`Lab.work`, `audit_integrity`, `finish`), `booking_lab/audit.py` (`AUDIT_PATH`), `booking_lab/AUDIT.md`, `.gitignore` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P2 · Effort: Low · Phase: 3 |
| **Finding** | Connection creation is centralized: `db(name='DATABASE_URL')` in `booking_lab/service.py` is the single factory for every PostgreSQL connection (autocommit, `dict_row`, fixed timeouts), and `connect()` in `booking_lab/audit.py` is the single factory for the ledger. All SQL for a given store lives in that store's module, and no other module imports a database driver. |
| **Gap** | There is no repository/DAO abstraction above the connection factory — parameterized SQL statements are written inline throughout the handler and saga functions, so the data contract is distributed across call sites even though connection handling is not. |
| **Recommendation** | No restructuring is required at this size. If the service grows, extract the `operations`/`bookings`/`outbox` statements into a thin repository module so the table contract has one owner; keep the existing single connection factory. |
| **Evidence** | `booking_lab/service.py` (`db`, inline `c.execute` calls), `booking_lab/audit.py` (`connect`) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P1 · Effort: Low · Phase: 2 |
| **Finding** | The PostgreSQL image is pinned immutably by digest (`"postgres": "postgres@sha256:721873c3..."` in `booking_lab/images.lock.json`) and the same file pins the Python base image; the Dockerfile repeats the Python digest. The resolved server version is captured at runtime into the evidence file (`SHOW server_version;` in `booking_lab/run.py`) rather than declared. The client driver is pinned exactly (`psycopg[binary]==3.3.6`). |
| **Gap** | Digest pinning gives reproducibility but no declared major version, no EOL tracking and no documented version-update procedure covering downtime window, rollback or risk acknowledgment — and because digests are immutable, security updates to the engine are not picked up until someone deliberately re-pins. |
| **Recommendation** | Record the intended PostgreSQL major version alongside the digest, document the upgrade and rollback procedure, and automate digest refresh (Dependabot/Renovate for base images) so pinning does not silently become staleness. On RDS, set `engine_version` explicitly in IaC and track the AWS deprecation calendar. |
| **Evidence** | `booking_lab/images.lock.json`, `booking_lab/Dockerfile`, `booking_lab/requirements.txt`, `booking_lab/run.py` (`postgres_version` evidence field) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P1 · Effort: Low · Phase: 3 |
| **Finding** | Business logic is in the application layer; the database holds integrity constraints rather than behaviour. `booking_lab/schema.sql` defines CHECK constraints on `operations.status`, `bookings.status`, `charges.state` and amounts, a `UNIQUE(principal, request_key)` idempotency key and foreign keys. The only procedural SQL is `CREATE FUNCTION fail_booking_insert()` with trigger `test_booking_insert`, which exists purely to let the test administrator inject an insert failure, plus two SQLite triggers in the audit sink (`immutable_update`, `immutable_delete`) that enforce append-only retention (`booking_lab/audit.py`). No proprietary dialect (T-SQL, PL/SQL) and no commercial engine is involved. |
| **Gap** | Two PL/pgSQL objects and a `faults` table exist only for fault injection yet live in the production schema and are granted to runtime roles (`GRANT SELECT ON faults TO booking_app,payment_app`), and the API consults them when `LAB_FAULTS=1`. That test machinery is engine-coupled and would need to be excluded from any operated deployment. |
| **Recommendation** | No migration blocker exists — the schema is portable to RDS/Aurora PostgreSQL as written. Separate the fault-injection function, trigger and `faults` grants into a test-only migration that is never applied to an operated environment, keeping the retention triggers (which are a deliberate integrity control). |
| **Evidence** | `booking_lab/schema.sql` (`fail_booking_insert`, `test_booking_insert`, `faults`), `booking_lab/audit.py` (`immutable_update`, `immutable_delete`), `booking_lab/service.py` (`LAB_FAULTS` checks) |

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repository provisions no AWS resources at all (`has_iac_provisioning_aws_resources=false`; no Terraform, CDK, CloudFormation or SAM found), so there is no account-level IaC scope to evaluate. CloudTrail evaluation belongs in the foundation/account-level infrastructure repository. Note separately that the application implements its own independent signed application-level audit ledger (`booking_lab/audit.py`), which is evaluated under DATA-Q1 and SEC-Q2 rather than here. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of `*.tf`, `template.yaml`, `cdk.json` anywhere in the repository |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: High · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | Two at-rest surfaces exist and neither is encrypted. The PostgreSQL data volume `<prefix>-db-data` is a plain Docker volume with no encryption configuration (`booking_lab/run.py`), and the authoritative audit ledger is an unencrypted SQLite file whose only protection is POSIX mode 0600 and ownership by uid 65532 (`booking_lab/audit.py` `initialize()` → `chmod(0o600)`; `run.py` chowns `/audit` to 65532 mode 0700). Generated secret files, the `pg_dump` output and audit snapshots are likewise plaintext on disk at mode 0600. No KMS key, no `kms_key_id`, no volume- or application-level encryption appears anywhere. |
| **Gap** | Booking data, payment charge state and signed audit records are readable by anyone with host filesystem or volume access. HMAC signatures provide tamper *detection* for the ledger but no confidentiality, and `AUDIT.md` already acknowledges that a host root or sink administrator can defeat the boundary. |
| **Recommendation** | Encrypt both surfaces with customer-managed KMS keys: `storage_encrypted` with a CMK on the RDS instance, SSE-KMS on the S3 audit archive, and encrypted EBS/EFS if the sink keeps local state. Define a documented rotation policy, and keep the ledger signing key in AWS KMS or Secrets Manager rather than an environment variable. |
| **Evidence** | `booking_lab/run.py` (`docker volume create`, `env` 0600 files), `booking_lab/audit.py` (`initialize`), `booking_lab/AUDIT.md` (trust-boundary section) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P2 · Effort: Low · Phase: 3 |
| **Finding** | Every business endpoint requires a bearer token verified per request, with a scope mapped per method: `GET → bookings:read`, `POST → bookings:write`, `DELETE → bookings:cancel` (`booking_lab/service.py` `dispatch`). `booking_lab/auth.py` validates the HMAC signature with `compare_digest`, pins the header to exactly `{"alg":"HS256","typ":"JWT"}`, checks issuer, audience, `exp`/`nbf`/`iat`, caps lifetime at 300 s, rejects non-finite and boolean NumericDate values, constrains `sub` by regex and returns 403 on scope mismatch. All reads are filtered to the authenticated principal, and the E2E asserts 401 for ten malformed/forged token variants, 403 for insufficient scope and 404 for cross-principal access. The payment provider and audit sink each require their own bearer token with constant-time comparison; only `/health/live` and `/health/ready` are unauthenticated, which is intentional. |
| **Gap** | Authentication is a symmetric HS256 secret shared between issuer and verifier, with no key rotation, no JWKS and no asymmetric verification — `auth.py` documents that it is confined to the local lab. There is also no gateway-level throttling or request validation in front of the handler. |
| **Recommendation** | For an operated deployment, replace the symmetric lab issuer with an external authorization server issuing asymmetrically signed tokens (RS256/ES256) validated against a cached JWKS, and keep the existing scope and principal-isolation checks exactly as they are — they are the strongest part of the current security posture. Add gateway throttling per client. |
| **Evidence** | `booking_lab/auth.py` (`verify`), `booking_lab/service.py` (`dispatch` scope map, `payments` token check), `booking_lab/audit.py` (`do_POST`/`do_GET` token checks), `booking_lab/run.py` (`auth`, `isolation` test cases) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 |
| **Finding** | The application both issues and verifies its own tokens with a locally generated symmetric key: `booking_lab/run.py` creates `self.key = secrets.token_hex(32)` and mints tokens for `agent-a` / `agent-b` via `encode()` in `booking_lab/auth.py`, which the API verifies with the same key injected as `JWT_KEY`. There is no Cognito user pool, no OIDC discovery, no SAML federation and no external IdP configuration anywhere in the repository. The module docstring states the symmetric JWT is confined to this local lab. |
| **Gap** | Identity is self-managed and non-federatable: no SSO, no central revocation, no user lifecycle, and the verifying key is also the signing key. |
| **Recommendation** | Integrate an external identity provider (Amazon Cognito, or an existing enterprise OIDC provider) as token issuer and validate tokens against its JWKS. The service's scope-based authorization model maps directly onto OAuth2 scopes, so only the issuance and key-distribution halves need to change. |
| **Evidence** | `booking_lab/auth.py` (`encode`, module docstring), `booking_lab/run.py` (`self.key`, `self.tokens`), `booking_lab/service.py` (`os.environ['JWT_KEY']`) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | No plaintext credential is committed anywhere: every secret is generated per run with `secrets.token_hex` — the JWT key, five PostgreSQL role passwords, the payment token, and the audit signing/write/read tokens (`booking_lab/run.py`) — written to `.env` files at mode 0600 inside a 0700 directory, injected via `docker run --env-file`, and excluded from version control by `.gitignore`. Minimum-length guards are enforced at startup (`JWT_KEY` ≥ 32 chars in `service.py`; all three audit secrets ≥ 32 chars in `audit.py`), `docker()` deliberately never prints container environments or bootstrap SQL, and the HTTP handlers suppress request logging so bearer tokens are never written to logs. |
| **Gap** | Production-equivalent credentials live in environment variables and unencrypted on-disk env files with no managed store, no rotation and no audit trail of access. `booking_lab/AUDIT.md` notes that the verification secret must be preserved securely and that managed secret rotation is a deployment decision not provided here. |
| **Recommendation** | Store the database credentials, payment token and audit signing/read/write tokens in AWS Secrets Manager with automated rotation, inject them into ECS tasks by secret ARN rather than env files, and hold the ledger signing key in KMS so it is never materialized in a container environment. Keep the existing length guards and log-suppression behaviour. |
| **Evidence** | `booking_lab/run.py` (`passwords`, `audit_key`, `env` with `chmod(0o600)`), `booking_lab/service.py` (`JWT_KEY` guard), `booking_lab/audit.py` (`initialize` guard), `.gitignore`, `booking_lab/AUDIT.md` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P2 · Effort: Low · Phase: 2 |
| **Finding** | Runtime hardening is thorough for a lab: the image runs as `USER 65532:65532` with `PYTHONDONTWRITEBYTECODE` and no build toolchain beyond pip (`booking_lab/Dockerfile`), and every container is started `--read-only --cap-drop=ALL --security-opt=no-new-privileges` with a `noexec,nosuid,size=16m` tmpfs for `/tmp` and, where cgroups allow, `--memory 256m --cpus 1 --pids-limit 128` (`booking_lab/run.py`). Base images are pinned by digest and the resolved `RepoDigests` are recorded in the evidence output. The internal network is `--internal`, so most containers have no egress. |
| **Gap** | There is no patching or vulnerability-scanning process at all: no Dependabot or Renovate configuration (searched `.github/dependabot.yml`, `renovate.json` — absent), no image scanning, no SSM Patch Manager equivalent. Because images are pinned by immutable digest and the sole dependency is version-pinned, the stack cannot receive security updates without a manual re-pin, which turns a reproducibility strength into a patching liability over time. |
| **Recommendation** | Add Dependabot or Renovate for `requirements.txt` and the base-image digests in `images.lock.json`/`Dockerfile`, and enable Amazon ECR scan-on-push (or Amazon Inspector for the running tasks) so re-pinning is driven by findings rather than by memory. Retain all existing runtime hardening flags when translating to ECS task definitions (`readonlyRootFilesystem`, dropped capabilities, non-root user). |
| **Evidence** | `booking_lab/Dockerfile`, `booking_lab/run.py` (container options, `base_images` evidence), `booking_lab/images.lock.json`, absence of `.github/dependabot.yml` / `renovate.json` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 |
| **Finding** | There is no pipeline, therefore no security stage. Searched for SAST configuration (SonarQube, Semgrep, CodeGuru), dependency scanning (`.github/dependabot.yml`, `renovate.json`, `pip-audit`, `safety`), container scanning and `.snyk` policies — none exist. The repository contains no CI definition at all (see INF-Q11). |
| **Gap** | No automated detection of vulnerable dependencies, insecure code patterns or vulnerable base-image layers before changes land. The single runtime dependency and digest-pinned images reduce exposure but do not substitute for scanning. |
| **Recommendation** | In the first pipeline, add `pip-audit` against `requirements.txt`, a SAST pass (Semgrep or CodeGuru Reviewer) over `booking_lab/`, and ECR scan-on-push for the built image, with the build failing on critical findings. |
| **Evidence** | Absence of `.github/workflows/`, `.github/dependabot.yml`, `renovate.json`, `.snyk` at repository root; `booking_lab/requirements.txt` |

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 2 |
| **Finding** | A correlation identity exists and is persisted end-to-end within the data plane: the API accepts `X-Correlation-ID` (defaulting to a fresh UUID), stores it on `operations`, stamps it on every `outbox` row, carries it into the signed audit record and into the `audit_events` projection, and re-attributes cancellation to its own request's correlation id (`booking_lab/service.py`, `booking_lab/schema.sql`, `booking_lab/audit.py`). The E2E asserts principal and correlation attribution on `booking.confirmed`. However, no tracing SDK is present (no OpenTelemetry, no X-Ray in `requirements.txt`), and the correlation id is not forwarded on the outbound HTTP calls to the payment provider or the audit sink — `payment()` and `deliver()` send only `Content-Type` and `Authorization`. |
| **Gap** | Correlation is strong inside the database and audit trail but does not propagate across process boundaries as a trace context, so there is no cross-service span view of a charge or a delivery, and no latency breakdown. |
| **Recommendation** | Adopt OpenTelemetry with the AWS Distro, propagate `traceparent` (and the existing `X-Correlation-ID`) on the payment and audit calls, and export to AWS X-Ray or an OTLP backend. The existing correlation id makes a natural trace attribute, so instrumentation is additive rather than a redesign. |
| **Evidence** | `booking_lab/service.py` (`X-Correlation-ID` handling, `payment`, `deliver` headers), `booking_lab/schema.sql` (`correlation_id` columns), `booking_lab/requirements.txt` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 3 |
| **Finding** | No monitoring artifact of any kind exists in the repository: no SLO definition file, no CloudWatch alarm, no latency or error-rate threshold, no dashboard definition. The only service-level contract expressed anywhere is in-code timeouts (`statement_timeout=10000`, `lock_timeout=8000`, 4 s provider timeout, 8 s request timeout) and the test harness's own 35 s wait bound (`booking_lab/service.py`, `booking_lab/run.py`). The E2E does assert hard correctness invariants after every run — zero captured charges without a confirmed booking, zero confirmed bookings without a captured charge, zero pending operations, zero undelivered audit events, zero audit rows missing attribution — which are business invariants rather than service-level objectives. |
| **Gap** | No availability or latency objective for the booking API, no error budget and no measurement, so degradation cannot be detected or prioritized. |
| **Recommendation** | Define SLOs for the two user journeys that matter — booking creation availability and p99 latency, and audit delivery lag (time from `outbox.created_at` to `delivered_at`) — and implement them as CloudWatch alarms with error-budget tracking once the service is deployed. |
| **Evidence** | `booking_lab/run.py` (`invariants` block), `booking_lab/service.py` (timeout settings), absence of alarm or SLO definitions anywhere in the repository |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 3 |
| **Finding** | The running services emit no metrics. There is no metrics client, no `put_metric_data`, no Prometheus endpoint and no counter instrumentation; `log_message` is deliberately suppressed in both HTTP handlers and the only runtime output is three coarse strings (`request_retry_pending`, `recovery_pending`, `worker_retry_pending`). Business-relevant counts exist only as post-hoc SQL in the test harness, which writes `audit_event_count`, per-table row hashes and the invariant counters into a one-shot evidence JSON (`booking_lab/run.py`). |
| **Gap** | Operationally meaningful quantities that the schema already makes computable — bookings confirmed, payments declined, compensations performed, outbox backlog, cancellations — are never published, so there is no way to observe business behaviour in a running system. |
| **Recommendation** | Publish custom CloudWatch metrics (or OTLP metrics) for booking outcomes by terminal status, compensation events, undelivered outbox depth and audit delivery lag, and build a dashboard from them. Outbox depth in particular doubles as the correct auto-scaling signal for the worker (see INF-Q7). |
| **Evidence** | `booking_lab/service.py` (`log_message` pass, `print` statements), `booking_lab/run.py` (`evidence` dictionary), absence of any metrics client in `booking_lab/requirements.txt` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Medium · Phase: 3 |
| **Finding** | No alerting exists. There is no CloudWatch alarm, no anomaly detector, no SNS topic, no PagerDuty/OpsGenie integration and no notification path in the repository. Failures surface either as HTTP status codes to the caller (503 with `retry_same_idempotency_key`) or as plain stdout lines captured to per-container log files only when `finish()` runs at the end of a lab session (`booking_lab/run.py`). |
| **Gap** | Nobody is notified of anything: a stalled worker, a growing undelivered outbox, repeated compensation or an audit sink returning 503 would all pass unobserved until someone queried the database. |
| **Recommendation** | After metrics exist (OPS-Q3), configure CloudWatch alarms on API 5xx rate and latency, on undelivered outbox depth and on audit-delivery failures, route them to SNS, and enable CloudWatch anomaly detection on the primary paths once a baseline accumulates. |
| **Evidence** | `booking_lab/run.py` (`finish` log capture), `booking_lab/service.py` (503 branch), absence of alarm/notification definitions anywhere in the repository |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: High · Priority: P1 · Effort: Medium · Phase: 1 |
| **Finding** | Deployment is direct container creation: `docker build` followed by `docker run -d` per role, with in-place `docker stop` / `docker start` / `docker restart` used during the test scenarios (`booking_lab/run.py`). There is no CodeDeploy configuration, no Helm release, no Argo Rollouts, no ALB weighted target group, no Lambda alias shifting and no feature-flag mechanism. Health endpoints suitable for gating a rollout do exist (`/health/live`, `/health/ready` with a real database probe in `booking_lab/service.py`) and the E2E proves both replicas can be restarted without losing state or duplicating charges, but nothing consumes those endpoints to stage a release. |
| **Gap** | No staged rollout or rollback path: a bad image would reach every replica at once, and recovery would be a manual re-run of the previous image. |
| **Recommendation** | Start with ECS rolling deployments gated on the existing `/health/ready` probe and a minimum-healthy-percent setting, then move to CodeDeploy blue/green with ALB target-group traffic shifting. The service's idempotency and advisory-lock design already makes mixed-version replicas safe, which is the hard prerequisite most workloads lack. |
| **Evidence** | `booking_lab/run.py` (`setup`, `start`, `docker restart` usage), `booking_lab/service.py` (`/health/live`, `/health/ready`) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 — Needs Work · Severity: Medium · Priority: P1 · Effort: Low · Phase: 1 |
| **Finding** | The integration suite is the strongest asset in the repository. `booking_lab/run.py` provisions disposable, isolated Docker resources (uniquely prefixed networks, volumes and containers; generated secrets; ephemeral host ports) and runs 18 cases against a real PostgreSQL and a real audit sink: token forgery and scope enforcement, happy path with attribution, cross-replica idempotent replay and payload conflict, cross-principal isolation, eight concurrent requests across two replicas yielding exactly one charge, injected insert failure with refund and no orphan, refund outage with durable COMPENSATING state and worker recovery, process crash after an external commit reconciled without double charge, payment-provider outage, crash after refund with no second refund, declined payment, cancellation with preserved POST response, audit delivery failure with outbox drain after restart, role-privilege denial, redelivery deduplication, database outage fail-closed plus volume survival, real `pg_dump` restore with per-table row-hash comparison, and signed-ledger tamper/truncation/restart/restore verification. Final invariant assertions must all be zero, and assertions are protected against `-O` (`if not __debug__: raise SystemExit`). None of this runs in CI — there is no pipeline (INF-Q11). |
| **Gap** | Coverage is not the gap; enforcement is. The suite runs only when a human invokes it, so nothing prevents a regression from being committed, and there is no stored history of pass/fail across changes. |
| **Recommendation** | Run `python3 booking_lab/run.py e2e --output .local/db-e2e.json` on every pull request in CI with a Docker-capable runner, publish the evidence JSON as a build artifact, and make the invariant block a required status check. This is the single highest-leverage change available. |
| **Evidence** | `booking_lab/run.py` (`run_tests`, `invariants`, `main` `__debug__` guard), `booking_lab/README.md`, absence of `.github/workflows/` |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 3 — Partial · Severity: Low · Priority: P2 · Effort: Medium · Phase: 3 |
| **Finding** | A defined class of incidents is genuinely self-healing without human intervention. The worker loop runs `recover()` and `deliver()` every 250 ms: `recover()` re-drives every operation left in `NEW`, `CHARGED`, `COMPENSATING` or `CANCELLING` under an advisory lock, and `deliver()` drains undelivered outbox rows, deduplicating by event UUID (`booking_lab/service.py`). The E2E proves this recovers from a refund outage, an API crash after an external commit, a payment-provider outage, a crash after refund and an audit-delivery privilege failure. Procedural documentation exists for the audit path: `booking_lab/AUDIT.md` gives the verification command and the retention/checkpoint procedure, and `booking_lab/audit_verify.py` is an executable offline verifier. |
| **Gap** | Remediation is limited to saga and delivery reconciliation; there is no runbook for operational incidents outside that class (database unavailability, sink outage, key compromise, host loss), no alert-to-action wiring, no escalation path and no machine-readable automation document — the guidance is prose markdown and the worker is the only automation. |
| **Recommendation** | Keep the recovery worker as the primary self-healing mechanism and add structured runbooks (SSM Automation documents) for the incidents it cannot resolve, each linked to the alarm that detects it. Convert the `AUDIT.md` verification procedure into a scheduled automated check so ledger integrity is confirmed continuously rather than on demand. |
| **Evidence** | `booking_lab/service.py` (`main` worker loop, `recover`, `deliver`), `booking_lab/AUDIT.md`, `booking_lab/audit_verify.py`, `booking_lab/run.py` (recovery test cases) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 — Not Ready · Severity: Medium · Priority: P2 · Effort: Low · Phase: 3 |
| **Finding** | There are no observability assets to own: no dashboard, no alarm, no SLO file, and no `CODEOWNERS` file in the repository. Logs are written to per-container files only at session teardown, into a session-local directory (`booking_lab/run.py` `finish()`), with no retention, aggregation or named owner. The repository root contains only `booking_lab/`, `.gitignore` and `LICENSE`. |
| **Gap** | No team attribution for monitoring, no per-service dashboard, and no durable log destination — monitoring would be reactive and ad hoc in any operated deployment. |
| **Recommendation** | When the service is deployed, create a per-service CloudWatch dashboard and alarms defined in IaC with owner tags, ship container logs to CloudWatch Logs with an explicit retention period, and add a `CODEOWNERS` entry covering the observability and IaC directories. |
| **Evidence** | `booking_lab/run.py` (`finish` log write), absence of `CODEOWNERS`, dashboards or alarm definitions anywhere in the repository |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This repo provisions no AWS resources (`has_iac_provisioning_aws_resources=false`; no Terraform, CDK, CloudFormation or SAM found), so there are no resources to tag. Tagging governance belongs in the repo that owns the AWS infrastructure. For completeness: the local Docker resources the lab creates are consistently name-prefixed per run (`db-lab-<10-hex>`), which serves the same disambiguation purpose at lab scope but is not AWS tagging. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of `*.tf`, `template.yaml`, `cdk.json` anywhere in the repository; `booking_lab/run.py` (`self.prefix`) |

---

## Learning Materials

Applicable to the two triggered pathways:

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Classification Count Reconciliation

Counts derived by tallying the emitted findings array (not a running counter):

| Severity | Count | Derivation |
|----------|-------|------------|
| High | 5 | INF-Q2, INF-Q11, DATA-Q1, SEC-Q2, OPS-Q5 (score 1 on core questions) |
| Medium | 19 | Score 1 non-core: INF-Q6, INF-Q7, INF-Q9, APP-Q5, SEC-Q4, SEC-Q7, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q8 (10). Score 2: INF-Q1, INF-Q3, INF-Q4, INF-Q8, INF-Q10, APP-Q6, SEC-Q5, OPS-Q1, OPS-Q6 (9) |
| Low | 11 | Score 3: INF-Q5, APP-Q1, APP-Q2, APP-Q3, APP-Q4, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q3, SEC-Q6, OPS-Q7 |
| **Total findings** | **35** | 5 + 19 + 11 = 35 |

Questions recorded in `evaluations[]` instead of `findings[]`: SEC-Q1 (not evaluated — no account-level IaC), OPS-Q9 (not evaluated — no AWS resources provisioned). 35 findings + 2 evaluations = 37 questions. No question scored 4, so no pass-status evaluations exist.

Tier derivation: 5 High → rule "2-11 High → Remediation Required". Score band: overall 1.99 falls in 1.5–2.4 (Needs Work) ≡ Remediation Required. Count-based tier and score-based band agree → `classification_consistency_check: "consistent"`.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `booking_lab/service.py` | INF-Q1, INF-Q3, INF-Q4, INF-Q6, INF-Q7, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q2, DATA-Q4, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q5, OPS-Q7 | API handler, durable saga (`advance`), transactional outbox (`emit`/`deliver`), recovery worker, synthetic payment provider, health endpoints, connection factory |
| `booking_lab/run.py` | INF-Q1, INF-Q2, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, APP-Q6, DATA-Q1, DATA-Q3, SEC-Q2, SEC-Q4, SEC-Q5, SEC-Q6, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q5, OPS-Q6, OPS-Q8, OPS-Q9 | Isolated Docker environment construction, per-run secret generation, network segmentation, container hardening, 18-case E2E, dump/restore and audit-integrity verification, evidence output |
| `booking_lab/schema.sql` | INF-Q2, INF-Q3, INF-Q4, APP-Q2, DATA-Q4, OPS-Q1 | Tables and CHECK constraints, idempotency uniqueness, outbox and audit projection, per-role GRANT/REVOKE isolation, test-only fault function and trigger |
| `booking_lab/audit.py` | INF-Q2, INF-Q4, DATA-Q1, DATA-Q4, SEC-Q2, SEC-Q3, SEC-Q5, OPS-Q1 | Independent append-only signed ledger, SQLite WAL/`synchronous=FULL`, immutability triggers, bearer-token endpoints, secret length guards |
| `booking_lab/auth.py` | APP-Q1, SEC-Q3, SEC-Q4 | Local symmetric JWT issuer/verifier, claim and scope validation, non-finite NumericDate rejection |
| `booking_lab/audit_verify.py` | INF-Q8, OPS-Q7 | Offline ledger chain and checkpoint verifier |
| `booking_lab/Dockerfile` | INF-Q1, INF-Q2, DATA-Q3, SEC-Q6 | Digest-pinned base image, non-root user, minimal image content |
| `booking_lab/images.lock.json` | INF-Q1, INF-Q2, INF-Q10, DATA-Q3, SEC-Q6 | Immutable image digest pins for PostgreSQL and Python |
| `booking_lab/requirements.txt` | APP-Q1, DATA-Q3, OPS-Q1, OPS-Q3, SEC-Q7 | Single pinned dependency (`psycopg[binary]==3.3.6`); absence of tracing, metrics and AI libraries |
| `booking_lab/AUDIT.md` | INF-Q8, DATA-Q1, SEC-Q2, SEC-Q5, OPS-Q7 | Retention, external checkpoint and trust-boundary statements; explicitly defers TLS, managed rotation and immutable object archive to deployment |
| `booking_lab/README.md` | APP-Q1, INF-Q11, OPS-Q6 | Manual execution instructions, Python 3.11+/Docker requirements, component overview |
| `.gitignore` | DATA-Q1, SEC-Q5 | Excludes `.local` session artifacts and generated secrets from version control |
| Absence: `*.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`, `k8s/`, `docker-compose*.yml` | INF-Q10, SEC-Q1, OPS-Q9 | No declarative IaC or deployment manifests anywhere in the repository |
| Absence: `.github/workflows/`, `buildspec.yml`, `Jenkinsfile`, `appspec.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | No CI/CD or deployment pipeline definition |
| Absence: `.github/dependabot.yml`, `renovate.json`, `.snyk` | SEC-Q6, SEC-Q7, DATA-Q3 | No dependency-update automation or security scanning configuration |
| Absence: `openapi.*`, `swagger.*`, `*.graphql` | APP-Q5 | No machine-readable API contract |
| Absence: `CODEOWNERS`, dashboards, alarm definitions | OPS-Q2, OPS-Q4, OPS-Q8 | No observability assets or ownership attribution |
