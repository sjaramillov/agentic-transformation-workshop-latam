# Agentic Readiness Analysis Report
**Target**: ${HOME}/ccs-mit-analysis-20261016/after/ara/booking-mit  
**Date**: 2026-10-16  
**Analyzed by**: AWS Transform Custom - Agentic Readiness Analysis  
**TD Version**: agentic-readiness-analysis (version ID unresolved - `atx custom def get -n agentic-readiness-analysis` reported the definition as not found; the definition name is recorded instead)  
**Repository Type**: application (user-provided)  
**Service Archetype**: stateful-crud (auto-detected)  
**Agent Scope**: write-enabled (user-provided)  
**Context**: Original MIT booking service assessed for write-enabled agents that create, read and cancel their own bookings. Business invariants: one captured payment per confirmed booking; no unreconciled charge after failure; stable idempotency across replicas; authorization scoped to the authenticated principal; durable attributed audit events. The service comprises an HTTP API, a synthetic HTTP payment provider and a recovery/audit worker over PostgreSQL, with an independent signed audit sink. Payment amounts are synthetic lab data. The current runtime binds API ports to 127.0.0.1 only.

**Archetype Justification**: The service owns persistent PostgreSQL state (operations, bookings, charges, outbox, audit_events in booking_lab/schema.sql) and exposes create, read and cancel operations on a business entity with an explicit status lifecycle, scoped to a per-principal identity. It is not an orchestrator (it calls one downstream dependency, the synthetic payment provider, plus its own audit sink), not a data-gateway (writes dominate the logic), and not an event-processor (it has a synchronous HTTP surface).

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: false

`has_logging_of_user_data` is false because booking_lab/service.py and booking_lab/audit.py both override `log_message` to a no-op and the only emitted log lines are fixed strings carrying an exception type name - no request body, token, principal or identifier is logged.

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 11 | **INFOs**: 8

**Classification Tier**: Pilot-Ready - Pilot-Ready (Safety Concerns)

This repository has 0 BLOCKER findings and 8 RISK-SAFETY findings (plus 11 RISK-QUALITY and 8 INFO findings, neither of which affects the tier). The matched rule is "0 BLOCKER, >=3 RISK-SAFETY -> Pilot-Ready (Safety Concerns)", which assigns the classification tier **Pilot-Ready** with sub-qualifier **Pilot-Ready (Safety Concerns)** and the readiness profile **Pilot-Ready (Safety Concerns)** - the classification tier and the readiness profile are a named roll-up of the same two counts.

Supervised pilot with elevated safety oversight: (1) human approval gates on irreversible actions and an agent limited to low-blast-radius operations, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) a dedicated safety review cadence, (4) agent restricted to the lowest-blast-radius operations until the RISK-SAFETY count drops below 3.

The write-safety core of this service is implemented and executable-tested rather than asserted: identity-scoped idempotency, a durable saga with real compensation, cross-replica advisory locking, least-privilege database roles, and an independent HMAC-chained append-only audit ledger all passed on code evidence corroborated by the 17-case harness in booking_lab/run.py. What remains open is containment and oversight - there is no rate or transaction limit, no way to suspend one agent identity, no reviewable pre-commit state and no approval gate - plus the operational layer (specification, observability, IaC, CI/CD, rollback, encryption at rest) that a future externally exposed deployment would require.

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 11 |
| INFO | 8 |
| Pass (no finding) | 16 |
| N/A | 0 |
| Not Evaluated (extended) | 0 |
| **Total** | **43** |

**Core Questions Evaluated**: 25  
**Extended Questions Triggered**: 18  
**Extended Questions Not Triggered**: 0  
**Questions N/A (repo_type: application)**: 0  
**Service Archetype**: stateful-crud (auto-detected)

All 18 extended questions were triggered: the archetype is stateful-crud with persistent state and external dependencies, `agent_scope` is write-enabled, the service sits on the payment critical path, and collection endpoints can return unbounded results.

## BLOCKERs - Must Resolve Before Agent Deployment

No BLOCKERs identified.

All five conditional BLOCKER questions were evaluated at BLOCKER severity under `agent_scope: write-enabled` and each passed on implemented, test-verified controls:

- **API-Q4 (idempotent writes)** - principal-scoped idempotency keys, payload fingerprinting, `UNIQUE(principal, request_key)`, verbatim response replay and advisory locking across replicas.
- **STATE-Q1 (compensation and rollback)** - durable saga with persisted status, refund compensation, crash recovery worker and an explicit cancel/undo path.
- **AUTH-Q6 (immutable audit logging)** - transactional outbox delivered to an independent signed, HMAC-chained, append-only ledger with a 90-day minimum retention and verified tamper/truncation detection.
- **DATA-Q1 (sensitive data scoping)** - B1 and B2 clear (explicit column projection, principal-scoped reads, three independent scopes, four least-privilege database roles); only the informational B3 classification sub-check is outstanding.
- **DATA-Q2 (data residency)** - synthetic, non-regulated data in a single local volume with no cross-region replication, no managed data service and no third-party egress.

## RISKs

### RISK-SAFETY - Must Address for Agent Safety

#### AUTH-Q4: Identity Propagation and Delegation - RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The system carries exactly one identity dimension. booking_lab/auth.py issues tokens whose only subject claim is sub (agent-a/agent-b in the fixtures) with no act, azp or on-behalf-of claim, and booking_lab/service.py treats the verified sub as the sole principal. Internal hops do not propagate it: payment() and deliver() authenticate to the payment provider and audit sink with the static shared bearer tokens PAYMENT_TOKEN and AUDIT_WRITE_TOKEN, so the payment provider authorizes any holder of the token and performs no per-principal check (charges has no principal column in booking_lab/schema.sql). There is no token exchange, no OAuth on-behalf-of flow, and no audit field distinguishing agent-as-self from agent-acting-for-a-user: booking_lab/audit.py FIELDS records principal only.
- **Gap**: An agent acting for a specific human cannot be bounded by that human's permissions, and the audit ledger cannot show which end user a booking was made for. Any component holding PAYMENT_TOKEN can charge or refund any operation_id regardless of which principal owns it.
- **Compensating Controls**:
  - Restrict the pilot to agents acting under their own service identity only - never on behalf of named end users - so the single sub claim is complete attribution.
  - Keep the payment provider on the internal-only Docker network (booking_lab/run.py creates it with --internal) so PAYMENT_TOKEN is never reachable from the agent-facing network.
- **Remediation Timeline**: 60-90 days
- **Recommendation**: Add a delegation claim (for example act.sub or an explicit obo subject) to the token contract, persist both the actor and the subject on operations/outbox/audit events, and have the payment provider verify the booking principal alongside its service token.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 2
- **Evidence**: booking_lab/auth.py

#### AUTH-Q5: Credential Management - RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No secret is hardcoded anywhere in the source: booking_lab/run.py generates every credential per run with secrets.token_hex (JWT key, five PostgreSQL role passwords, PAYMENT_TOKEN, AUDIT_SIGNING_KEY, AUDIT_WRITE_TOKEN, AUDIT_READ_TOKEN), writes them to 0600 env files under .local/ which .gitignore excludes (.local/, .env*), and docker() deliberately never prints container environments. Minimum key strength is enforced at startup (service.py refuses a JWT_KEY shorter than 32 characters; audit.py initialize() refuses audit secrets shorter than 32). There is, however, no secrets-manager integration (no aws_secretsmanager_* or Vault reference exists - no IaC files are present) and no rotation path: all secrets are process-lifetime environment variables, and the JWT key is a single symmetric secret shared between the token issuer fixture (booking_lab/auth.py encode) and the verifying API, so any API host can mint tokens for any principal.
- **Gap**: Rotation requires restarting every container, and compromise of an API host or its env file yields the ability to forge any agent identity. There is no managed rotation, no asymmetric verification key and no audit of secret access.
- **Compensating Controls**:
  - Keep the 5-minute maximum token lifetime enforced in booking_lab/auth.py verify, which bounds the window of a leaked token.
  - Keep env files at 0600 under .local/ and keep the API bound to 127.0.0.1 (booking_lab/run.py publishes 127.0.0.1:{port}:8080) while rotation is being built.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Move JWT verification to an asymmetric key pair (private key held only by the issuer, API verifying against a published JWKS) and source all runtime secrets from AWS Secrets Manager or Vault with scheduled rotation before any externally exposed deployment.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 2
- **Evidence**: booking_lab/run.py

#### AUTH-Q7: Agent Identity Suspension - RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is no mechanism to revoke one agent identity. booking_lab/auth.py verify performs stateless signature and claim validation with no jti, no denylist lookup and no principal allowlist; booking_lab/service.py accepts any sub matching [a-zA-Z0-9_-]{1,64} that is signed with the shared JWT_KEY. Because the key is shared by all principals, the only revocation action available is rotating JWT_KEY and restarting the API, which invalidates every agent at once. No API-key table, account-disable endpoint or external identity store exists - searched the repository for revocation endpoints and IaC, none present.
- **Gap**: A misbehaving or compromised agent cannot be isolated without a platform-wide outage for all agents.
- **Compensating Controls**:
  - Token lifetime is capped at 300 s (booking_lab/auth.py verify rejects exp-iat > 300), so stopping token issuance for one principal at the operator fixture retires its access within five minutes.
  - Operate the pilot with one agent principal per deployment so that all-or-nothing key rotation is equivalent to single-identity revocation.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Introduce a per-principal status check in the authorization path (a principals table consulted by Handler.dispatch, or an external IdP supporting per-client disablement) so a single sub can be suspended without rotating the shared key.
- **Effort**: Medium | **Priority**: P1 | **Phase**: 2
- **Evidence**: booking_lab/auth.py

#### STATE-Q4: Circuit Breakers and Resilience - RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Timeouts and durable retries are implemented, but there is no circuit breaker and no backoff. booking_lab/service.py sets connect_timeout=3, statement_timeout=10000 and lock_timeout=8000 on every PostgreSQL connection, urlopen timeout=4 on both the payment provider and the audit sink, and an 8 s socket timeout per request; failures are converted to a retryable 503 rather than a hang. Retry is durable but unthrottled: main() in worker mode loops recover() + deliver() every 250 ms unconditionally, and recover() re-drives up to 100 pending operations each pass, so a provider that is down or slow is re-called four times a second indefinitely with no breaker, no exponential backoff and no per-operation attempt ceiling. No resilience library is present (booking_lab/requirements.txt contains only psycopg[binary]==3.3.6).
- **Gap**: A dependency outage produces a sustained retry storm from the worker (amplified by each 4 s timeout held open), and there is no fast-fail state to stop the API from queuing more work against a known-bad provider.
- **Compensating Controls**:
  - Bounded timeouts on every outbound call plus fail-closed 503 responses (verified by run.py database_outage_fail_closed_and_volume_survives_restart) keep failures contained to latency rather than data loss.
  - Run a single worker replica during the pilot and alert on the outbox backlog (SELECT count(*) FROM outbox WHERE delivered_at IS NULL) to cap retry amplification.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Add exponential backoff with jitter and an attempt or age ceiling to the worker loop, and a circuit breaker around payment() and the audit POST that short-circuits to the existing retryable 503 while open.
- **Effort**: Medium | **Priority**: P1 | **Phase**: 2
- **Evidence**: booking_lab/service.py

#### STATE-Q5: Rate Limiting and Throttling - RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling exists anywhere on the agent-facing surface. booking_lab/service.py serves the API from ThreadingHTTPServer with no limiter, no per-principal counter and no concurrency cap; searched the repository for API-gateway/WAF throttling (no IaC files of any kind exist), rate-limiting middleware and X-RateLimit/Retry-After headers - none found. The only protections are per-request bounds: an 8 KiB body cap, an 8 s connection timeout, and the per-container cgroup limits booking_lab/run.py applies to the lab (--memory 256m --cpus 1 --pids-limit 128), which shed load by exhaustion rather than by a documented limit.
- **Gap**: A runaway agent loop can saturate the API replicas, the PostgreSQL connection pool and the synthetic payment provider at machine speed; a thread is spawned per connection with no ceiling.
- **Compensating Controls**:
  - Cap concurrency and request rate in the agent orchestration layer, and keep the API bound to 127.0.0.1 (booking_lab/run.py publishes 127.0.0.1:{port}:8080) so only local callers can reach it.
  - Keep the per-container cgroup limits from booking_lab/run.py so a traffic storm degrades one replica instead of the host.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Enforce per-principal request-rate and concurrency limits in front of the API (an API Gateway usage plan, a reverse proxy, or middleware keyed on the verified sub) and return 429 with Retry-After so agents can self-throttle.
- **Effort**: Medium | **Priority**: P1 | **Phase**: 2
- **Evidence**: booking_lab/service.py

#### STATE-Q6: Blast Radius and Transaction Limits - RISK-SAFETY (scope-calibrated)

- **Severity**: RISK-SAFETY
- **Scope resolution**: Scope-calibrated to RISK-SAFETY: agent_scope=write-enabled, so absent business-transaction limits are a safety risk rather than informational.
- **Finding**: Only per-request value bounds exist; there are no per-principal business limits. booking_lab/service.py validates a single booking amount as an int in 1..10000000 and booking_lab/schema.sql enforces amount > 0, which caps one transaction but not aggregate exposure. Nothing limits bookings per principal per hour, cumulative synthetic spend per session, or cancellations and refunds per principal: cancel() has no counter, and the only LIMIT 100 clauses are internal worker batch sizes in recover() and deliver(), not caller-facing caps. There are no bulk endpoints, so blast radius grows by repetition rather than by a single large call.
- **Gap**: A correct-but-runaway agent can create or cancel an unbounded number of bookings and drive an unbounded number of synthetic captures and refunds; the maximum business impact of an agent error is undefined.
- **Compensating Controls**:
  - Enforce per-principal booking and cancellation quotas in the agent orchestration layer until they exist in the service.
  - Monitor the charges table (count and sum per principal via the operations join) and alert on deviation from the expected pilot envelope.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Add configurable per-principal limits enforced in the write path (bookings per interval, cumulative amount per session, cancellations per interval) keyed on the verified sub, returning a distinct terminal error code when exceeded.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 2
- **Evidence**: booking_lab/service.py

#### HITL-Q1: Draft/Pending State - RISK-SAFETY (scope-calibrated)

- **Severity**: RISK-SAFETY
- **Scope resolution**: Scope-calibrated to RISK-SAFETY: agent_scope=write-enabled, so the absence of a reviewable pre-commit state is a safety risk.
- **Finding**: There is no reviewable pre-commit state. booking_lab/service.py create() inserts the operation with status NEW and immediately calls advance(), which charges the payment provider and commits the CONFIRMED booking within the same request; the operations status values in booking_lab/schema.sql (NEW, CHARGED, CONFIRMED, COMPENSATING, COMPENSATED, DECLINED, CANCELLING, CANCELLED) are saga progress markers, not approval states - NEW is already a committed intent to charge, and the worker will drive it to CONFIRMED without any human action. bookings.status allows only CONFIRMED or CANCELLED. There is no draft, PENDING_REVIEW or proposed record and no create-then-confirm two-step API.
- **Gap**: An agent cannot propose a booking for human review; every accepted POST captures a payment and confirms a booking autonomously.
- **Compensating Controls**:
  - Use DELETE /bookings/{id} as the reversal path - cancellation refunds the capture and is proven idempotent (run.py cancel_refund_repeat_and_preserve_create_response) - and require human review after the fact for the pilot.
  - Hold agent-proposed bookings in the orchestration layer and call POST /bookings only after a human approves.
- **Remediation Timeline**: 60-90 days
- **Recommendation**: Add a proposed/pending status to operations and bookings plus a separate confirm endpoint requiring a distinct scope, so an agent-initiated booking is materialised only after review. The existing saga and idempotency machinery can carry the extra state without redesign.
- **Effort**: High | **Priority**: P1 | **Phase**: 2
- **Evidence**: booking_lab/schema.sql

#### HITL-Q2: Configurable Approval Gates - RISK-SAFETY (scope-calibrated)

- **Severity**: RISK-SAFETY
- **Scope resolution**: Scope-calibrated to RISK-SAFETY: agent_scope=write-enabled, so the absence of configurable approval gates is a safety risk.
- **Finding**: No approval gate exists or can be configured. booking_lab/service.py authorizes a request on token scope alone and then executes it; there is no approval endpoint, no per-operation flag, no amount threshold that diverts to review, and no external workflow integration. The only operator-facing control in the repository is the faults table, which booking_lab/schema.sql documents as test-administrator-only with no HTTP endpoint, and LAB_FAULTS=1 is set only for the lab API containers in booking_lab/run.py.
- **Gap**: High-risk operations (large synthetic amounts, cancellation of a confirmed booking) cannot be made to require a human decision at the application layer.
- **Compensating Controls**:
  - Implement the approval gate in the agent orchestration layer for operations above an agreed amount, and scope the pilot token to bookings:read + bookings:write only (withholding bookings:cancel) so cancellations require an operator.
  - Grant bookings:cancel only to an operator-driven identity, using the independent scope already enforced in booking_lab/service.py.
- **Remediation Timeline**: 60-90 days
- **Recommendation**: Introduce a configurable policy check in Handler.dispatch (for example amount above a threshold, or DELETE on a CONFIRMED booking) that parks the operation in a pending-approval state and exposes an approve/reject endpoint gated by a distinct scope.
- **Effort**: High | **Priority**: P1 | **Phase**: 2
- **Evidence**: booking_lab/service.py

### RISK-QUALITY - Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification exists. Searched for openapi.*/swagger.* (yaml/json), *.graphql/*.gql, *.smithy, AsyncAPI documents and spec-generating libraries in booking_lab/requirements.txt (only psycopg[binary]==3.3.6) - zero results. The contract is described only in prose: booking_lab/README.md points to ../LABORATORIO_MIT.md, which is not present in this repository.
- **Gap**: Agent tool definitions for POST/GET/DELETE /bookings, the required Idempotency-Key and X-Correlation-ID headers, the bookings:read|write|cancel scopes and the error vocabulary must be hand-authored and will drift from booking_lab/service.py.
- **Compensating Controls**:
  - Hand-author and version the agent tool schema from booking_lab/service.py Handler.dispatch and keep it under review with the code.
  - Pin the agent to the request shapes exercised by booking_lab/run.py run_tests, which cover every route and error path.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Publish an OpenAPI 3.1 document covering the five routes, the Authorization/Idempotency-Key/X-Correlation-ID headers, the request schema (itinerary [A-Z]{3}-[A-Z]{3}, amount 1..10000000) and every documented error code, and validate it against booking_lab/service.py in a build step.
- **Effort**: Low | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/requirements.txt

#### DATA-Q3: Selective Query Support - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The collection endpoint is unbounded. booking_lab/service.py answers GET /bookings with SELECT id,itinerary,amount,status FROM bookings WHERE principal=%s ORDER BY id and returns every row in a single {"bookings":[...]} body; there is no limit, offset, cursor, status filter or sort parameter, and the path regex accepts only /bookings or /bookings/{64-hex}, so no query string is interpreted at all. Single-item retrieval is implemented by fetching the full principal-scoped set and filtering it in Python, so the database read grows with the principal history even for a one-record lookup.
- **Gap**: An agent with a long booking history receives an unbounded array that can exhaust its context window, and the service cannot express "most recent N" or "CONFIRMED only".
- **Compensating Controls**:
  - Cap the agent pilot to principals with small booking counts and truncate results in the tool adapter.
  - Use GET /bookings/{id} for targeted reads so the full-collection call is rarely needed.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Add limit/cursor pagination plus a status filter to GET /bookings with a server-side default and maximum page size, and push the single-id lookup into SQL (WHERE principal=%s AND id=%s) instead of filtering in the handler.
- **Effort**: Low | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/service.py

#### DATA-Q4: Input Validation and Schema Enforcement - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Validation is strict but rejections are opaque. booking_lab/service.py enforces Content-Type application/json, a 1..8192 byte body, a JSON object, an exact field set {itinerary, amount}, amount of Python type int in 1..10000000, itinerary matching [A-Z]{3}-[A-Z]{3}, Idempotency-Key matching [A-Za-z0-9_-]{1,100}, a parseable UUID X-Correlation-ID and a path matching /bookings/[a-f0-9]{64}; all database access is parameterised through psycopg and CHECK constraints back the enum and amount rules (booking_lab/schema.sql). Every one of those failures raises a bare ValueError that the single handler converts to the same response: 400 {"error":"invalid_request"} with no field name, no constraint and no accepted format. The payment provider likewise raises ValueError on a bad operation_id or amount.
- **Gap**: An agent that constructs a malformed payload cannot tell which field was rejected or why, so it must guess across several candidate fixes - the blind-retry loop the rubric warns about.
- **Compensating Controls**:
  - Encode the full validation contract (field set, regex, numeric range, required headers) in the agent tool schema so malformed calls are prevented client-side.
  - Mirror the request shapes exercised by booking_lab/run.py, which cover the accepted payloads and header combinations.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Return a structured validation body (for example {"error":"invalid_request","fields":[{"field":"itinerary","constraint":"pattern","expected":"[A-Z]{3}-[A-Z]{3}"}]}) by raising a typed validation error carrying the field and constraint, instead of a bare ValueError.
- **Effort**: Low | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/service.py

#### DATA-Q5: Temporal Metadata and Freshness - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Temporal metadata is partial and is not exposed to callers. booking_lab/schema.sql defines created_at timestamptz NOT NULL DEFAULT clock_timestamp() on outbox and created_at timestamptz NOT NULL on audit_events, and the signed ledger records carry created_at plus a retain_until deadline (booking_lab/audit.py), so the audit path is timestamped in timezone-aware form. The business tables have no temporal columns at all: operations, bookings and charges carry no created_at or updated_at, and the API responses from booking_lab/service.py return only id, itinerary, amount, status - no timestamp, no X-Data-Age, no consistency indicator. Reads are strongly consistent (direct PostgreSQL reads with Cache-Control: no-store), so freshness is implicitly current, but nothing states it.
- **Gap**: An agent cannot tell when a booking was created or last changed, cannot order its own history by time, and cannot assert freshness from the response itself.
- **Compensating Controls**:
  - Derive approximate timing from the audit ledger or outbox created_at when an agent needs ordering.
  - Treat every response as current - reads are uncached and strongly consistent - and record the retrieval time in the agent trace.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Add created_at/updated_at timestamptz columns to operations, bookings and charges and surface them (UTC, ISO-8601) in the booking responses; optionally emit an explicit consistency marker since reads are strongly consistent.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/schema.sql

#### DISC-Q1: Schema Versioning and API Contracts - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Schemas and contracts are neither versioned nor change-detected. booking_lab/schema.sql is a single create-from-scratch DDL file with no migration history and no version marker; the HTTP paths carry no version segment (booking_lab/service.py matches /bookings and /bookings/[a-f0-9]{64} only) and no Accept-Version header is read, although the server does advertise Server: BookingLab/1. There is no JSON Schema, Avro, Protobuf or OpenAPI artifact, no schema registry, no changelog or deprecation notice, and no breaking-change detection or consumer-driven contract test - there is no CI configuration at all (searched for .github/workflows, .gitlab-ci.yml, Jenkinsfile, buildspec.yml: none present). The audit event contract is the one explicitly pinned surface: booking_lab/audit.py validates an exact FIELDS set and the ledger record shape is stable.
- **Gap**: A change to the booking response shape, the scope names or the error vocabulary would break agent tool bindings silently, with nothing in the repository to detect it.
- **Compensating Controls**:
  - Pin the agent tool definition to a specific source revision (booking_lab/run.py already records source_sha256 per file in its evidence) and re-validate on every change.
  - Treat the 17 acceptance cases in booking_lab/run.py as the de facto contract suite and run them before promoting any change.
- **Remediation Timeline**: 60-90 days
- **Recommendation**: Version the HTTP surface (/v1/bookings or an Accept-Version header), adopt forward-only migration files for schema.sql, and add an automated contract diff against a published specification once API-Q2 is addressed.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/schema.sql

#### OBS-Q1: Distributed Tracing and Structured Logging - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Correlation is carried through the data path but not through logs, and there is no tracing. booking_lab/service.py accepts X-Correlation-ID (or generates a UUID4), validates it as a UUID, stores it on operations, stamps every outbox event with it, attributes a cancellation to its own request correlation, and propagates it into the signed audit ledger (booking_lab/audit.py FIELDS includes correlation_id); booking_lab/run.py asserts the principal and correlation id reach the outbox for booking.confirmed. Logging, by contrast, is deliberately minimal and unstructured: Handler.log_message is a no-op and the only emitted lines are plain strings 'request_retry_pending <ExceptionTypeName>', 'worker_retry_pending' and 'recovery_pending' with no JSON envelope, no correlation_id, no principal and no operation id. No OpenTelemetry or X-Ray instrumentation exists and traceparent is neither read nor forwarded on the outbound payment and audit calls (booking_lab/requirements.txt contains only psycopg[binary]==3.3.6).
- **Gap**: A failed agent-initiated request cannot be reconstructed from logs: the retry line cannot be tied to a principal, operation or correlation id, and there is no span linking the API, payment provider and audit sink.
- **Compensating Controls**:
  - Reconstruct request history from the signed audit ledger and the outbox, which carry principal, operation_id, correlation_id, event_type and created_at per transition.
  - Have the agent orchestrator generate and record X-Correlation-ID per task so failures can be joined to ledger records after the fact.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Emit JSON log lines including correlation_id, principal, operation_id, route and outcome (continuing to exclude tokens and bodies), and add OpenTelemetry instrumentation that reads and forwards traceparent across the payment and audit calls.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/service.py

#### OBS-Q2: Alerting on Error Rates and Latency - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting exists. Searched the repository for CloudWatch alarms, Prometheus rules, anomaly detection and PagerDuty/OpsGenie integration - none present, and there is no IaC or monitoring configuration of any kind. The health surface an external monitor could use is implemented (GET /health/live, GET /health/ready with a real dependency query in booking_lab/service.py), and booking_lab/run.py captures per-container logs at the end of a run, but nothing watches error rates, latency, the undelivered-outbox backlog or the saga invariants while the system is running.
- **Gap**: Degradation of the agent-facing API would be detected only by the agent failing, with no operator signal and no threshold on the backlog of undelivered audit events or stranded operations.
- **Compensating Controls**:
  - Monitor the pilot externally by polling /health/ready and the two backlog queries on a fixed interval.
  - Keep the agent pilot supervised so a human notices sustained 503 responses.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Scrape /health/ready plus the invariant counters from booking_lab/run.py (pending_operations, undelivered_audit_events) and configure alerts on 5xx rate, p99 latency, readiness failures and backlog growth.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/service.py

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The agent-facing surface is not defined as infrastructure as code. Searched for Terraform (.tf/.tfvars), CloudFormation, CDK, Pulumi, SAM, Helm charts, Kustomize, Kubernetes manifests, Ansible and docker-compose: none exist in the repository. Provisioning is an imperative Python/Docker harness, booking_lab/run.py, which does apply strong hardening in code - pinned image digests from booking_lab/images.lock.json, an --internal network for the data plane, --read-only --cap-drop=ALL --security-opt=no-new-privileges, a noexec tmpfs, cgroup memory/CPU/PID limits, non-root USER 65532 in booking_lab/Dockerfile, per-run secrets, 0600 env files and 127.0.0.1-only port publication. But it is a test harness, not a deployment definition: there is no gateway, IAM, TLS or network definition for a real environment, no peer-review gate (no CI configuration exists) and no drift detection.
- **Gap**: Nothing declaratively defines the authentication, networking and exposure of the agent-facing API for a deployed environment, so changes cannot be plan-reviewed or drift-checked.
- **Compensating Controls**:
  - Treat booking_lab/run.py plus booking_lab/images.lock.json as the reviewed, version-pinned environment definition for the pilot, since it is fully reproducible and records source_sha256 and image digests in its evidence output.
  - Keep the API bound to 127.0.0.1 so the undefined external surface is not exposed while IaC is being written.
- **Remediation Timeline**: 60-90 days
- **Recommendation**: Express the deployed topology as IaC (gateway or load balancer with TLS, the two API replicas, worker, payment provider, audit sink, PostgreSQL, secrets and network policy), require review on changes, and enable drift detection - reusing the hardening flags already encoded in booking_lab/run.py as the baseline.
- **Effort**: High | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/run.py

#### ENG-Q2: CI/CD with API Contract Testing - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: There is no CI/CD pipeline. Searched for .github/workflows, .gitlab-ci.yml, Jenkinsfile, buildspec.yml, appspec.yml and any pipeline definition - none exist; the repository contains only booking_lab/ source, .gitignore and LICENSE. The 17-case acceptance suite in booking_lab/run.py must be invoked manually (python3 booking_lab/run.py e2e), and because no machine-readable API specification exists (API-Q2) there is nothing a pipeline could diff for breaking changes.
- **Gap**: A change that alters the booking response shape, a scope name or an error code reaches consumers with no automated gate; agent tool breakage would not be detected before deployment.
- **Compensating Controls**:
  - Make a passing booking_lab/run.py e2e run (with its JSON evidence artifact) a mandatory manual gate before any change is promoted.
  - Pin consumers to a reviewed revision and re-run the suite plus agent tool validation on every bump.
- **Remediation Timeline**: 30-60 days
- **Recommendation**: Add a pipeline that builds the pinned image, runs booking_lab/run.py e2e against the real PostgreSQL/Docker stack, and - once a specification exists - fails on a breaking API diff.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/run.py

#### ENG-Q3: Rollback Capability - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment or rollback mechanism is defined. There is no blue/green or canary configuration, no CodeDeploy or Helm release, no traffic shifting and no feature flag in the repository; booking_lab/run.py starts containers directly with docker run and its finish() deliberately retains containers and volumes for review rather than managing a release lifecycle. The ingredients for a fast, deterministic rollback are present - immutable base image digests in booking_lab/images.lock.json, a reproducible build from booking_lab/Dockerfile, a recorded app image id and per-file source_sha256 in the run evidence, and additive DDL - but the procedure itself is undefined, and schema.sql has no migration or down-path.
- **Gap**: There is no defined, time-bounded way to return the agent-facing API to a known-good version, and no owner or runbook for doing so.
- **Compensating Controls**:
  - Redeploy the previously recorded app image id and pinned base digests manually as an interim rollback, keeping the two API replicas so one can be restored at a time.
  - Keep the database volume separate from the application containers (booking_lab/run.py uses a named volume, verified by database_outage_fail_closed_and_volume_survives_restart) so a code rollback does not touch data.
- **Remediation Timeline**: 60-90 days
- **Recommendation**: Define a versioned release with an explicit rollback path (previous image digest redeployed behind a load balancer, or two-slot traffic shifting), add forward-only migrations with compatibility rules so a code rollback does not strand the schema, and rehearse the rollback to confirm a 15-30 minute recovery.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/images.lock.json

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data - RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: There is no encryption at rest. PostgreSQL data lives in a plain Docker volume created by booking_lab/run.py (docker volume create {prefix}-db-data) and the signed audit ledger in a second plain volume holding /audit/ledger.sqlite; neither is encrypted. No KMS key, kms_key_id, LUKS/dm-crypt setting, PostgreSQL TDE extension or SQLite encryption provider appears anywhere (no IaC files exist; booking_lab/requirements.txt lists only psycopg[binary]==3.3.6). Confidentiality rests on filesystem permissions and process isolation instead: booking_lab/audit.py chmods the ledger to 0600 and the volume is chowned to uid 65532 with mode 0700, env files are 0600, containers run read-only, non-root and cap-drop ALL, and the pg_dump produced during the e2e is written 0600. Transport is also unencrypted (plain HTTP and non-TLS libpq on Docker networks, mitigated today by the --internal network and 127.0.0.1-only publication). The data at rest is synthetic and non-PII.
- **Gap**: A host-level compromise or a copied volume exposes the full booking and synthetic charge history and the audit ledger in cleartext; the ledger HMAC gives tamper evidence but no confidentiality.
- **Compensating Controls**:
  - Rely on the existing 0600/0700 permissions, non-root read-only containers and internal-only networking while encrypted storage is provisioned.
  - Keep the dataset synthetic - booking_lab/run.py records payments as synthetic with no money moved - so a disclosure has no regulated-data impact.
- **Remediation Timeline**: 60-90 days
- **Recommendation**: Place both volumes on encrypted storage with a managed key (KMS-backed EBS/EFS or an encrypted RDS instance, plus an encrypted archive for the ledger), and enable TLS for libpq and for the payment and audit HTTP hops before any externally exposed deployment.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/run.py

## INFOs - Architecture and Design Inputs

#### API-Q5: Structured Response Format - INFO

- **Severity**: INFO
- **Finding**: All request and response bodies are UTF-8 JSON objects. booking_lab/service.py Handler.send uses json.dumps with Content-Type application/json, Cache-Control no-store and an explicit Content-Length; Handler.body rejects any request that is not application/json, is empty, exceeds 8192 bytes, or does not decode to a JSON object. The independent audit sink uses the same convention with canonical, sorted-key JSON (booking_lab/audit.py canonical).
- **Gap**: None - the format is directly LLM-consumable.
- **Implication**: Agent tools can bind to the responses with no transformation layer; the 8 KiB body cap and strict Content-Type check should be surfaced in the tool contract so agents do not emit oversized payloads.
- **Recommendation**: Keep the flat JSON shape; no parsing adapter layer is needed for agent tooling. Reflect the 8 KiB body cap and the strict Content-Type requirement in the tool contract.
- **Effort**: Low | **Priority**: P3 | **Phase**: 3
- **Evidence**: booking_lab/service.py

#### API-Q7: Event Emission for State Changes - INFO

- **Severity**: INFO
- **Finding**: State changes are emitted as durable domain events, but only to internal consumers. booking_lab/service.py emit() writes booking.requested, payment.captured, payment.declined, payment.refunded, booking.confirmed, booking.compensation_requested, booking.cancel_requested and booking.cancelled into the transactional outbox (booking_lab/schema.sql outbox) in the same transaction as the state change; deliver() forwards each event to the independent audit sink and the audit_events projection. There is no webhook registration, SNS/EventBridge/Kafka publisher or consumer-facing event stream - booking_lab/audit.py exposes only POST /events (write token) and GET /events (read token) for the ledger.
- **Gap**: External and agent consumers cannot subscribe to state transitions; they must poll GET /bookings.
- **Implication**: Agents must be designed as request/response pollers today; the transactional outbox is a ready foundation for an event-reactive design later.
- **Recommendation**: If event-reactive agents are targeted, publish the existing outbox events to a consumer-facing bus (the outbox row already carries operation_id, principal, correlation_id and event_type) rather than adding a second emission path.
- **Effort**: Medium | **Priority**: P2 | **Phase**: 3
- **Evidence**: booking_lab/service.py

#### API-Q8: Rate Limit Documentation and Headers - INFO

- **Severity**: INFO
- **Finding**: No rate limits are documented and no rate-limit headers are returned. booking_lab/service.py Handler.send emits only Content-Type, Cache-Control and Content-Length; there is no X-RateLimit-Remaining or Retry-After anywhere in the repository, no API gateway or WAF (no IaC files exist), and no throttling middleware (the server is ThreadingHTTPServer from the standard library). The only self-throttling signal available to a caller is the 503 retry_same_idempotency_key flag.
- **Gap**: Agents have no machine-readable budget signal and will discover capacity limits only as failures.
- **Implication**: Until limits and headers exist, agent concurrency must be capped in the orchestration layer.
- **Recommendation**: Emit Retry-After on 503 and, once limits are enforced (see STATE-Q5), publish X-RateLimit-Limit/Remaining/Reset and document the limits in the API specification.
- **Effort**: Low | **Priority**: P3 | **Phase**: 3
- **Evidence**: booking_lab/service.py

#### DATA-Q1: Sensitive Data Classification - INFO (scope-calibrated)

- **Severity**: INFO
- **Scope resolution**: Resolved to INFO: B1 did not fire (responses are explicitly projected and subject-scoped) and B2 did not fire (scope- and role-level differentiation exists), so only the B3 informational sub-check is outstanding.
- **Finding**: Stage A = Yes: the system persists principal-scoped business data and synthetic financial transactions (booking_lab/schema.sql operations, bookings, charges, outbox, audit_events). Stage B1 is CLEAR - agent-facing responses are explicitly projected and subject-scoped: the GET handler in booking_lab/service.py selects only id, itinerary, amount, status WHERE principal=%s, the charges table is never exposed through the booking API, no credential or token is persisted or serialized, and the payment and audit sinks sit on an internal-only network. Stage B2 is CLEAR - access is differentiated by independent token scopes (bookings:read / bookings:write / bookings:cancel) and by four least-privilege PostgreSQL roles with per-table and per-column grants. Stage B3 is absent: there is no machine-readable classification metadata - no field-level sensitivity annotations in booking_lab/service.py or schema.sql, no classification tags (no IaC files exist), and no PII-detection tooling (booking_lab/requirements.txt lists only psycopg[binary]==3.3.6).
- **Gap**: No formal data classification layer exists; field sensitivity is implicit in the code and in the itinerary/amount column semantics. Per the rubric this is aspirational, not a deployment gate.
- **Implication**: Agent tool definitions can be bound to the current response shape safely, but a future schema change has no classification guardrail to prevent widening the agent-visible field set.
- **Recommendation**: Record a short classification table for the five business tables (labelling the synthetic nature of charges.amount) so future schema changes do not silently widen agent-visible fields; keep the explicit column projection in the GET handler as the enforcement point.
- **Effort**: Low | **Priority**: P0 | **Phase**: 3
- **Evidence**: booking_lab/schema.sql

#### DATA-Q7: Data Quality Awareness - INFO

- **Severity**: INFO
- **Finding**: Data correctness is expressed as executable invariants rather than as a quality score. booking_lab/run.py computes, at the end of every e2e run, captured_without_confirmed_booking, confirmed_without_captured_payment, pending_operations, undelivered_audit_events and audit_missing_attribution and asserts all are zero; it also compares per-table md5 row-set hashes between the live database and a real pg_dump restore, and asserts the signed ledger record count equals the audit_events projection count. None of this runs in production: there is no null-rate or duplicate monitoring, no freshness SLA and no data-quality dashboard.
- **Gap**: Quality signal exists only at test time, so an agent cannot know at call time whether the invariants still hold.
- **Implication**: The invariant set is a ready-made definition of "healthy data" for agent-facing monitoring; it simply needs to run outside the test harness.
- **Recommendation**: Promote the five invariant queries in booking_lab/run.py to a scheduled runtime check that publishes each count as a metric, so drift is detected while agents are live.
- **Effort**: Low | **Priority**: P3 | **Phase**: 3
- **Evidence**: booking_lab/run.py

#### DISC-Q2: Semantically Meaningful Field Names - INFO

- **Severity**: INFO
- **Finding**: Field and identifier names are semantically explicit with no legacy codes requiring a dictionary. booking_lab/schema.sql uses principal, request_key, fingerprint, payload, correlation_id, itinerary, amount, status, operation_id, event_type, created_at, delivered_at, captures and refunds; status enums are spelled out (NEW, CHARGED, CONFIRMED, COMPENSATING, COMPENSATED, DECLINED, CANCELLING, CANCELLED; CAPTURED, REFUNDED, DECLINED). Event types are dotted and self-describing (booking.requested, payment.captured, payment.declined, booking.confirmed, booking.compensation_requested, booking.cancel_requested, booking.cancelled, payment.refunded). Error codes read as sentences (payment_declined, idempotency_payload_mismatch, booking_failed_payment_refunded, temporarily_unavailable) and scopes are namespaced (bookings:read, bookings:write, bookings:cancel). The ledger fields in booking_lab/audit.py follow the same convention.
- **Gap**: None. The one abbreviation, opid/oid in booking_lab/service.py, is internal to the implementation and never appears in a response body or column name.
- **Implication**: Field semantics can be inferred directly from the response, reducing the prompt context needed for agent tool descriptions.
- **Recommendation**: Preserve the convention; it lets LLM-based reasoning interpret responses and audit events without a lookup table.
- **Effort**: Low | **Priority**: P3 | **Phase**: 3
- **Evidence**: booking_lab/schema.sql

#### DISC-Q3: Data Catalog / Metadata Layer - INFO

- **Severity**: INFO
- **Finding**: There is no data catalog or metadata layer. Searched for Glue/DataHub/Collibra/Alation references, data dictionaries and metadata manifests - none exist (and no IaC files are present). Discoverability rests on three prose/DDL artifacts: booking_lab/schema.sql as the authoritative table and permission definition, booking_lab/AUDIT.md describing the ledger record structure, retention, verification procedure and trust boundary, and booking_lab/README.md describing each module and the scope model. booking_lab/README.md also references ../LABORATORIO_MIT.md for the full API contract, which is not part of this repository.
- **Gap**: Agent tool authors must read the DDL and source to learn what the system holds; semantics are not published anywhere machine-readable.
- **Implication**: Tool-definition work requires reading source; budget for it, or close the gap with a short committed data dictionary.
- **Recommendation**: For a system of this size a short data dictionary committed beside schema.sql is sufficient; a catalog product is not warranted. Bringing the referenced LABORATORIO_MIT.md contract into the repository would close the main documentation gap.
- **Effort**: Low | **Priority**: P3 | **Phase**: 3
- **Evidence**: booking_lab/README.md

#### OBS-Q3: Business Outcome Metrics - INFO

- **Severity**: INFO
- **Finding**: No metrics are published at runtime. There is no put_metric_data call, StatsD/Prometheus client or dashboard definition anywhere in the repository. Business outcomes are nevertheless computed at test time: booking_lab/run.py writes a structured evidence document containing per-case results and durations, audit_event_count, the five business invariants, restored_table_row_hashes and the independent_audit summary. The underlying business state is queryable from PostgreSQL (bookings by status, charges by state, captures and refunds per operation), so the measurements exist but are never emitted as metrics.
- **Gap**: There is no live signal for whether agent interactions produce good business outcomes (confirmation rate, cancellation rate, decline rate, compensation rate).
- **Implication**: Per-principal metrics are the cheapest way to make agent impact measurable, since principal is already recorded on every operation and audit event.
- **Recommendation**: Publish the existing counts as custom metrics - bookings confirmed, bookings cancelled, payments declined, compensations executed, undelivered audit events - segmented by principal so agent-driven outcomes can be compared with human-driven ones.
- **Effort**: Low | **Priority**: P3 | **Phase**: 3
- **Evidence**: booking_lab/run.py

## Detailed Findings

### 01 - API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: Pass (no finding)
- **Finding**: Documented REST interface implemented in booking_lab/service.py (Handler.dispatch): POST /bookings, GET /bookings, GET|DELETE /bookings/{64-hex id}, GET /health/live, GET /health/ready, all JSON over HTTP. No direct-database, file-exchange or UI-automation integration path exists for callers; database credentials are held only by the service roles themselves (booking_lab/schema.sql GRANTs). booking_lab/client.py is a reference HTTP client for the same contract.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification exists. Searched for openapi.*/swagger.* (yaml/json), *.graphql/*.gql, *.smithy, AsyncAPI documents and spec-generating libraries in booking_lab/requirements.txt (only psycopg[binary]==3.3.6) - zero results. The contract is described only in prose: booking_lab/README.md points to ../LABORATORIO_MIT.md, which is not present in this repository.
- **Gap**: Agent tool definitions for POST/GET/DELETE /bookings, the required Idempotency-Key and X-Correlation-ID headers, the bookings:read|write|cancel scopes and the error vocabulary must be hand-authored and will drift from booking_lab/service.py.
- **Recommendation**: Publish an OpenAPI 3.1 document covering the five routes, the Authorization/Idempotency-Key/X-Correlation-ID headers, the request schema (itinerary [A-Z]{3}-[A-Z]{3}, amount 1..10000000) and every documented error code, and validate it against booking_lab/service.py in a build step.
- **Evidence**: booking_lab/requirements.txt

#### API-Q3: Structured Error Responses
- **Severity**: Pass (no finding)
- **Finding**: Every response is a JSON object with a stable machine-readable code: booking_lab/service.py Handler.send serializes JSON with Content-Type application/json and Cache-Control no-store; terminal errors return {'error':'payment_declined'} (402), 'booking_not_found' (404), 'idempotency_payload_mismatch' (409), 'booking_failed_payment_refunded' (409), 'forbidden' (403), 'unauthorized' (401), 'method_not_allowed' (405); retriable failures return 503 {'error':'temporarily_unavailable','retry_same_idempotency_key':true}, an explicit machine-readable retry signal naming the safe retry mechanism. Field-level detail on validation rejections is absent and is attributed to DATA-Q4 rather than counted twice here.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### API-Q4: Idempotent Write Operations (conditional)
- **Severity**: Pass (no finding)
- **Conditional**: agent_scope is "write-enabled" - evaluated at the write-enabled severity (BLOCKER for conditional BLOCKERs, RISK-SAFETY for scope-calibrated RISKs) and passed.
- **Finding**: Write idempotency is implemented and tested. booking_lab/service.py requires an Idempotency-Key matching [A-Za-z0-9_-]{1,100} on POST /bookings; opid() derives the operation id from sha256("POST /bookings"+principal+key) so keys are scoped per principal; operations has UNIQUE(principal, request_key) (booking_lab/schema.sql); a payload fingerprint mismatch on an existing key returns 409 idempotency_payload_mismatch; the stored response_code/response_body is replayed verbatim and is deliberately preserved after later cancellation. pg_advisory_lock serializes concurrent replays across API replicas, and the payment provider de-duplicates by operation_id under pg_advisory_xact_lock with a charges PRIMARY KEY. DELETE is idempotent (already-CANCELLED returns 200). booking_lab/run.py cases stable_replay_and_payload_conflict_across_replicas and eight_concurrent_requests_two_api_replicas_one_charge assert exactly one capture. Conditional resolution: agent_scope=write-enabled would have made this a BLOCKER had idempotency been absent.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All request and response bodies are UTF-8 JSON objects. booking_lab/service.py Handler.send uses json.dumps with Content-Type application/json, Cache-Control no-store and an explicit Content-Length; Handler.body rejects any request that is not application/json, is empty, exceeds 8192 bytes, or does not decode to a JSON object. The independent audit sink uses the same convention with canonical, sorted-key JSON (booking_lab/audit.py canonical).
- **Gap**: None - the format is directly LLM-consumable.
- **Recommendation**: Keep the flat JSON shape; no parsing adapter layer is needed for agent tooling. Reflect the 8 KiB body cap and the strict Content-Type requirement in the tool contract.
- **Evidence**: booking_lab/service.py

#### API-Q6: Asynchronous Operation Support
- **Severity**: Pass (no finding)
- **Finding**: Long-running saga work is handled asynchronously with a client-visible resume path rather than a blocking call. booking_lab/service.py main() runs a worker mode looping recover() + deliver() every 250 ms; recover() resumes any operation left in NEW/CHARGED/COMPENSATING/CANCELLING. When the synchronous attempt cannot complete, the API returns 503 with retry_same_idempotency_key=true, and GET /bookings/{id} exposes the settled state, giving agents a submit/poll pattern. Request-path timeouts are bounded (connection 8 s, payment and audit 4 s, DB connect 3 s, statement_timeout 10 s), so no operation is designed to exceed 30 s synchronously. booking_lab/run.py refund_outage_durable_state_and_worker_recovery and payment_provider_outage_retains_intent_and_recovers exercise asynchronous completion.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: State changes are emitted as durable domain events, but only to internal consumers. booking_lab/service.py emit() writes booking.requested, payment.captured, payment.declined, payment.refunded, booking.confirmed, booking.compensation_requested, booking.cancel_requested and booking.cancelled into the transactional outbox (booking_lab/schema.sql outbox) in the same transaction as the state change; deliver() forwards each event to the independent audit sink and the audit_events projection. There is no webhook registration, SNS/EventBridge/Kafka publisher or consumer-facing event stream - booking_lab/audit.py exposes only POST /events (write token) and GET /events (read token) for the ledger.
- **Gap**: External and agent consumers cannot subscribe to state transitions; they must poll GET /bookings.
- **Recommendation**: If event-reactive agents are targeted, publish the existing outbox events to a consumer-facing bus (the outbox row already carries operation_id, principal, correlation_id and event_type) rather than adding a second emission path.
- **Evidence**: booking_lab/service.py

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits are documented and no rate-limit headers are returned. booking_lab/service.py Handler.send emits only Content-Type, Cache-Control and Content-Length; there is no X-RateLimit-Remaining or Retry-After anywhere in the repository, no API gateway or WAF (no IaC files exist), and no throttling middleware (the server is ThreadingHTTPServer from the standard library). The only self-throttling signal available to a caller is the 503 retry_same_idempotency_key flag.
- **Gap**: Agents have no machine-readable budget signal and will discover capacity limits only as failures.
- **Recommendation**: Emit Retry-After on 503 and, once limits are enforced (see STATE-Q5), publish X-RateLimit-Limit/Remaining/Reset and document the limits in the API specification.
- **Evidence**: booking_lab/service.py

### 02 - Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: Pass (no finding)
- **Finding**: Machine identity is authenticated and attributed. booking_lab/service.py requires a bearer token on every /bookings request and calls auth.verify, which validates the HS256 signature with hmac.compare_digest, pins the header to {"alg":"HS256","typ":"JWT"}, checks iss=booking-lab, aud=booking-api, exp/nbf/iat including rejection of non-finite and boolean NumericDate values, caps token lifetime at 300 s, and constrains sub to [a-zA-Z0-9_-]{1,64}. The verified sub becomes the principal and is persisted on operations, bookings, outbox and every signed audit record (booking_lab/schema.sql; booking_lab/audit.py FIELDS includes principal). Service-to-service hops use separate bearer tokens (PAYMENT_TOKEN, AUDIT_WRITE_TOKEN/AUDIT_READ_TOKEN). booking_lab/run.py authentication_issuer_audience_expiry_signature_scope asserts rejection of ten malformed or forged tokens. The mechanism exists in code; the symmetric-key and issuer-fixture weaknesses are attributed to AUTH-Q5 and the revocation gap to AUTH-Q7 rather than double-counted here.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: Pass (no finding)
- **Finding**: The authorization model supports scoped, differentiated permissions at two layers. Token scopes are independent strings checked per request (booking_lab/service.py maps GET->bookings:read, POST->bookings:write, DELETE->bookings:cancel), so a read-only or create-but-not-cancel identity can be issued; booking_lab/run.py asserts 403 for a bookings:read token on POST and for a read+write token on DELETE. At the data layer booking_lab/schema.sql revokes PUBLIC access and grants narrowly per runtime role: booking_app gets SELECT,INSERT,UPDATE on operations,bookings,outbox only; payment_app only on charges; audit_writer INSERT on audit_events plus SELECT(id); audit_reader SELECT only. No wildcard grants exist, and runtime_roles_cannot_rewrite_audit_or_cross_service_tables asserts cross-service and audit writes are denied.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### AUTH-Q3: Action-Level Authorization
- **Severity**: Pass (no finding)
- **Finding**: Action-level authorization is enforced per HTTP method on the same resource type. booking_lab/service.py Handler.dispatch resolves required = {'GET':'bookings:read','POST':'bookings:write','DELETE':'bookings:cancel'} and auth.verify returns 403 when the scope is absent, so read can be granted without create and create without cancel. Reads and cancels are additionally constrained to the authenticated subject: cancel() selects WHERE id=%s AND principal=%s and the GET handler filters WHERE principal=%s, so cross-principal access returns 404. booking_lab/run.py identity_isolation_and_identity_scoped_idempotency asserts agent-b cannot read or cancel agent-a's booking.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-SAFETY
- **Finding**: The system carries exactly one identity dimension. booking_lab/auth.py issues tokens whose only subject claim is sub (agent-a/agent-b in the fixtures) with no act, azp or on-behalf-of claim, and booking_lab/service.py treats the verified sub as the sole principal. Internal hops do not propagate it: payment() and deliver() authenticate to the payment provider and audit sink with the static shared bearer tokens PAYMENT_TOKEN and AUDIT_WRITE_TOKEN, so the payment provider authorizes any holder of the token and performs no per-principal check (charges has no principal column in booking_lab/schema.sql). There is no token exchange, no OAuth on-behalf-of flow, and no audit field distinguishing agent-as-self from agent-acting-for-a-user: booking_lab/audit.py FIELDS records principal only.
- **Gap**: An agent acting for a specific human cannot be bounded by that human's permissions, and the audit ledger cannot show which end user a booking was made for. Any component holding PAYMENT_TOKEN can charge or refund any operation_id regardless of which principal owns it.
- **Recommendation**: Add a delegation claim (for example act.sub or an explicit obo subject) to the token contract, persist both the actor and the subject on operations/outbox/audit events, and have the payment provider verify the booking principal alongside its service token.
- **Evidence**: booking_lab/auth.py

#### AUTH-Q5: Credential Management
- **Severity**: RISK-SAFETY
- **Finding**: No secret is hardcoded anywhere in the source: booking_lab/run.py generates every credential per run with secrets.token_hex (JWT key, five PostgreSQL role passwords, PAYMENT_TOKEN, AUDIT_SIGNING_KEY, AUDIT_WRITE_TOKEN, AUDIT_READ_TOKEN), writes them to 0600 env files under .local/ which .gitignore excludes (.local/, .env*), and docker() deliberately never prints container environments. Minimum key strength is enforced at startup (service.py refuses a JWT_KEY shorter than 32 characters; audit.py initialize() refuses audit secrets shorter than 32). There is, however, no secrets-manager integration (no aws_secretsmanager_* or Vault reference exists - no IaC files are present) and no rotation path: all secrets are process-lifetime environment variables, and the JWT key is a single symmetric secret shared between the token issuer fixture (booking_lab/auth.py encode) and the verifying API, so any API host can mint tokens for any principal.
- **Gap**: Rotation requires restarting every container, and compromise of an API host or its env file yields the ability to forge any agent identity. There is no managed rotation, no asymmetric verification key and no audit of secret access.
- **Recommendation**: Move JWT verification to an asymmetric key pair (private key held only by the issuer, API verifying against a published JWKS) and source all runtime secrets from AWS Secrets Manager or Vault with scheduled rotation before any externally exposed deployment.
- **Evidence**: booking_lab/run.py

#### AUTH-Q6: Immutable Audit Logging (conditional)
- **Severity**: Pass (no finding)
- **Conditional**: agent_scope is "write-enabled" - evaluated at the write-enabled severity (BLOCKER for conditional BLOCKERs, RISK-SAFETY for scope-calibrated RISKs) and passed.
- **Finding**: Every write is attributed to the authenticated principal in an independent, tamper-evident ledger. booking_lab/service.py writes an outbox event in the same database transaction as each state transition (emit/transition/result), carrying operation_id, principal, correlation_id and event_type; deliver() POSTs each event to a separate audit process before acknowledging the outbox, and acknowledges only after both the signed append and the PostgreSQL projection succeed. booking_lab/audit.py appends under BEGIN IMMEDIATE with WAL and synchronous=FULL, chains each record by SHA256 digest over {sequence, previous, event, retain_until}, signs it with HMAC-SHA256 using a key the API, payment process and application database never receive, enforces append-only semantics with SQL triggers that ABORT UPDATE and DELETE, exposes no update or delete HTTP verb, and sets a 90-day minimum retention. Replay of the same event UUID returns the existing record; conflicting content is rejected. booking_lab/run.py independent_signed_audit_retention_tamper_restart_restore verifies the chain against a separately retained checkpoint, detects row tampering and tail truncation, shows the application DB administrator cannot alter the ledger, and verifies a restored SQLite backup; audit_delivery_failure_restart_and_durable_outbox_drain shows no event is lost during an audit outage. booking_lab/AUDIT.md states explicitly that this is not hardware WORM and that an externally operated deployment needs a separate administrative boundary, TLS, managed rotation and an immutable object archive. Conditional resolution: agent_scope=write-enabled, so this question was evaluated at BLOCKER severity and passed on implemented, test-verified controls.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: There is no mechanism to revoke one agent identity. booking_lab/auth.py verify performs stateless signature and claim validation with no jti, no denylist lookup and no principal allowlist; booking_lab/service.py accepts any sub matching [a-zA-Z0-9_-]{1,64} that is signed with the shared JWT_KEY. Because the key is shared by all principals, the only revocation action available is rotating JWT_KEY and restarting the API, which invalidates every agent at once. No API-key table, account-disable endpoint or external identity store exists - searched the repository for revocation endpoints and IaC, none present.
- **Gap**: A misbehaving or compromised agent cannot be isolated without a platform-wide outage for all agents.
- **Recommendation**: Introduce a per-principal status check in the authorization path (a principals table consulted by Handler.dispatch, or an external IdP supporting per-client disablement) so a single sub can be suspended without rotating the shared key.
- **Evidence**: booking_lab/auth.py

### 03 - State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback (conditional)
- **Severity**: Pass (no finding)
- **Conditional**: agent_scope is "write-enabled" - evaluated at the write-enabled severity (BLOCKER for conditional BLOCKERs, RISK-SAFETY for scope-calibrated RISKs) and passed.
- **Finding**: Compensation is implemented as a durable saga and proven against real failures. booking_lab/service.py persists an explicit state machine (operations.status CHECK over NEW, CHARGED, CONFIRMED, COMPENSATING, COMPENSATED, DECLINED, CANCELLING, CANCELLED in booking_lab/schema.sql); advance() resumes from the persisted state, refunds the captured charge when the booking insert fails, keeps ambiguous refund timeouts retryable instead of marking them refunded, re-reads the operation before refunding in case a failed COMMIT actually succeeded, and the worker recover() picks up any operation stranded in NEW/CHARGED/COMPENSATING/CANCELLING. DELETE /bookings/{id} is an explicit undo path (CANCELLING -> refund -> CANCELLED). booking_lab/run.py asserts the behaviour end-to-end in real_insert_failure_after_charge_refunds_without_orphan, refund_outage_durable_state_and_worker_recovery, process_crash_after_external_commit_reconciles_without_double_charge, process_crash_after_refund_recovers_without_second_refund and payment_provider_outage_retains_intent_and_recovers, and the run closes by asserting zero captured-without-confirmed-booking, zero confirmed-without-captured-payment and zero pending operations. Conditional resolution: agent_scope=write-enabled, so this question was evaluated at BLOCKER severity and passed on implemented, test-verified controls.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### STATE-Q2: Queryable Current State
- **Severity**: Pass (no finding)
- **Finding**: Current state is queryable before and after any action. booking_lab/service.py exposes GET /bookings (all bookings for the authenticated principal) and GET /bookings/{id}, returning id, itinerary, amount and status; operations.status and bookings.status are explicit state-machine columns (booking_lab/schema.sql) and the stored response_code/response_body make a prior POST result re-readable by replaying the idempotency key. GET /health/live and GET /health/ready expose process and dependency state. Reads go directly to PostgreSQL with no cache, so an agent reading before acting sees committed state.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### STATE-Q3: Concurrency Controls (scope-calibrated)
- **Severity**: Pass (no finding)
- **Conditional**: agent_scope is "write-enabled" - evaluated at the write-enabled severity (BLOCKER for conditional BLOCKERs, RISK-SAFETY for scope-calibrated RISKs) and passed.
- **Finding**: Concurrency is controlled with database-level locking and unique constraints. booking_lab/service.py locked() takes a pg_advisory_lock derived from the operation id for the whole create/cancel sequence, so the lock spans local commits and the external payment call across API replicas and the worker; the payment provider takes a distinct two-int pg_advisory_xact_lock namespace; the outbox drain uses SELECT ... FOR UPDATE SKIP LOCKED; refunds are applied with a conditional UPDATE ... WHERE state='CAPTURED'; audit projection inserts use ON CONFLICT(id) DO NOTHING; and booking_lab/schema.sql enforces UNIQUE(principal, request_key), bookings.id PRIMARY KEY and charges.operation_id PRIMARY KEY. Statement and lock timeouts (10 s / 8 s) bound lock waits. booking_lab/run.py eight_concurrent_requests_two_api_replicas_one_charge drives eight concurrent identical POSTs across two replicas and asserts identical responses, one capture and one booking row. Scope calibration: agent_scope=write-enabled, so this question was evaluated at RISK-SAFETY severity and passed.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Timeouts and durable retries are implemented, but there is no circuit breaker and no backoff. booking_lab/service.py sets connect_timeout=3, statement_timeout=10000 and lock_timeout=8000 on every PostgreSQL connection, urlopen timeout=4 on both the payment provider and the audit sink, and an 8 s socket timeout per request; failures are converted to a retryable 503 rather than a hang. Retry is durable but unthrottled: main() in worker mode loops recover() + deliver() every 250 ms unconditionally, and recover() re-drives up to 100 pending operations each pass, so a provider that is down or slow is re-called four times a second indefinitely with no breaker, no exponential backoff and no per-operation attempt ceiling. No resilience library is present (booking_lab/requirements.txt contains only psycopg[binary]==3.3.6).
- **Gap**: A dependency outage produces a sustained retry storm from the worker (amplified by each 4 s timeout held open), and there is no fast-fail state to stop the API from queuing more work against a known-bad provider.
- **Recommendation**: Add exponential backoff with jitter and an attempt or age ceiling to the worker loop, and a circuit breaker around payment() and the audit POST that short-circuits to the existing retryable 503 while open.
- **Evidence**: booking_lab/service.py

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling exists anywhere on the agent-facing surface. booking_lab/service.py serves the API from ThreadingHTTPServer with no limiter, no per-principal counter and no concurrency cap; searched the repository for API-gateway/WAF throttling (no IaC files of any kind exist), rate-limiting middleware and X-RateLimit/Retry-After headers - none found. The only protections are per-request bounds: an 8 KiB body cap, an 8 s connection timeout, and the per-container cgroup limits booking_lab/run.py applies to the lab (--memory 256m --cpus 1 --pids-limit 128), which shed load by exhaustion rather than by a documented limit.
- **Gap**: A runaway agent loop can saturate the API replicas, the PostgreSQL connection pool and the synthetic payment provider at machine speed; a thread is spawned per connection with no ceiling.
- **Recommendation**: Enforce per-principal request-rate and concurrency limits in front of the API (an API Gateway usage plan, a reverse proxy, or middleware keyed on the verified sub) and return 429 with Retry-After so agents can self-throttle.
- **Evidence**: booking_lab/service.py

#### STATE-Q6: Blast Radius and Transaction Limits (scope-calibrated)
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "write-enabled" - evaluated as RISK-SAFETY. Scope-calibrated to RISK-SAFETY: agent_scope=write-enabled, so absent business-transaction limits are a safety risk rather than informational.
- **Finding**: Only per-request value bounds exist; there are no per-principal business limits. booking_lab/service.py validates a single booking amount as an int in 1..10000000 and booking_lab/schema.sql enforces amount > 0, which caps one transaction but not aggregate exposure. Nothing limits bookings per principal per hour, cumulative synthetic spend per session, or cancellations and refunds per principal: cancel() has no counter, and the only LIMIT 100 clauses are internal worker batch sizes in recover() and deliver(), not caller-facing caps. There are no bulk endpoints, so blast radius grows by repetition rather than by a single large call.
- **Gap**: A correct-but-runaway agent can create or cancel an unbounded number of bookings and drive an unbounded number of synthetic captures and refunds; the maximum business impact of an agent error is undefined.
- **Recommendation**: Add configurable per-principal limits enforced in the write path (bookings per interval, cumulative amount per session, cancellations per interval) keyed on the verified sub, returning a distinct terminal error code when exceeded.
- **Evidence**: booking_lab/service.py

#### STATE-Q7: Graceful Degradation Signaling
- **Severity**: Pass (no finding)
- **Finding**: The system has no degraded or fallback data path to misrepresent, and it signals unavailability in machine-readable form. booking_lab/service.py serves reads directly from PostgreSQL with no cache, replica or stale fallback, sets Cache-Control: no-store on every response, splits liveness from readiness (GET /health/live returns {"live":true}; GET /health/ready executes a real query and therefore fails when the database is unreachable), and converts every dependency failure into 503 {"error":"temporarily_unavailable","retry_same_idempotency_key":true} instead of a partial or guessed result. booking_lab/run.py database_outage_fail_closed_and_volume_survives_restart asserts live=200 while ready=503 and POST=503 with no charge created - fail-closed rather than silently degraded.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

### 04 - Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State (scope-calibrated)
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "write-enabled" - evaluated as RISK-SAFETY. Scope-calibrated to RISK-SAFETY: agent_scope=write-enabled, so the absence of a reviewable pre-commit state is a safety risk.
- **Finding**: There is no reviewable pre-commit state. booking_lab/service.py create() inserts the operation with status NEW and immediately calls advance(), which charges the payment provider and commits the CONFIRMED booking within the same request; the operations status values in booking_lab/schema.sql (NEW, CHARGED, CONFIRMED, COMPENSATING, COMPENSATED, DECLINED, CANCELLING, CANCELLED) are saga progress markers, not approval states - NEW is already a committed intent to charge, and the worker will drive it to CONFIRMED without any human action. bookings.status allows only CONFIRMED or CANCELLED. There is no draft, PENDING_REVIEW or proposed record and no create-then-confirm two-step API.
- **Gap**: An agent cannot propose a booking for human review; every accepted POST captures a payment and confirms a booking autonomously.
- **Recommendation**: Add a proposed/pending status to operations and bookings plus a separate confirm endpoint requiring a distinct scope, so an agent-initiated booking is materialised only after review. The existing saga and idempotency machinery can carry the extra state without redesign.
- **Evidence**: booking_lab/schema.sql

#### HITL-Q2: Configurable Approval Gates (scope-calibrated)
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "write-enabled" - evaluated as RISK-SAFETY. Scope-calibrated to RISK-SAFETY: agent_scope=write-enabled, so the absence of configurable approval gates is a safety risk.
- **Finding**: No approval gate exists or can be configured. booking_lab/service.py authorizes a request on token scope alone and then executes it; there is no approval endpoint, no per-operation flag, no amount threshold that diverts to review, and no external workflow integration. The only operator-facing control in the repository is the faults table, which booking_lab/schema.sql documents as test-administrator-only with no HTTP endpoint, and LAB_FAULTS=1 is set only for the lab API containers in booking_lab/run.py.
- **Gap**: High-risk operations (large synthetic amounts, cancellation of a confirmed booking) cannot be made to require a human decision at the application layer.
- **Recommendation**: Introduce a configurable policy check in Handler.dispatch (for example amount above a threshold, or DELETE on a CONFIRMED booking) that parks the operation in a pending-approval state and exposes an approve/reject endpoint gated by a distinct scope.
- **Evidence**: booking_lab/service.py

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: Pass (no finding)
- **Finding**: The repository ships a complete, isolated, reproducible test environment with production-shaped data. booking_lab/run.py builds the application image from pinned digests (booking_lab/images.lock.json, booking_lab/Dockerfile FROM python@sha256:...), creates an internal data-plane network plus a front network, starts real PostgreSQL, two API replicas, the synthetic payment provider, the recovery/audit worker and the independent audit sink with per-run credentials, and publishes only to 127.0.0.1. The e2e command runs 17 acceptance cases including fault injection (payment decline, booking-insert failure, refund outage, crash after charge, crash after refund, database outage, audit outage) and a real pg_dump/restore comparison; the demo command leaves the stack running with a session file for interactive use through booking_lab/client.py. Payment amounts are synthetic and no money moves (run.py evidence field "payments"). Containers, volumes, logs and evidence are retained for review instead of pruned.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

### 05 - Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification (conditional)
- **Severity**: INFO
- **Conditional**: agent_scope is "write-enabled" - evaluated as INFO. Resolved to INFO: B1 did not fire (responses are explicitly projected and subject-scoped) and B2 did not fire (scope- and role-level differentiation exists), so only the B3 informational sub-check is outstanding.
- **Finding**: Stage A = Yes: the system persists principal-scoped business data and synthetic financial transactions (booking_lab/schema.sql operations, bookings, charges, outbox, audit_events). Stage B1 is CLEAR - agent-facing responses are explicitly projected and subject-scoped: the GET handler in booking_lab/service.py selects only id, itinerary, amount, status WHERE principal=%s, the charges table is never exposed through the booking API, no credential or token is persisted or serialized, and the payment and audit sinks sit on an internal-only network. Stage B2 is CLEAR - access is differentiated by independent token scopes (bookings:read / bookings:write / bookings:cancel) and by four least-privilege PostgreSQL roles with per-table and per-column grants. Stage B3 is absent: there is no machine-readable classification metadata - no field-level sensitivity annotations in booking_lab/service.py or schema.sql, no classification tags (no IaC files exist), and no PII-detection tooling (booking_lab/requirements.txt lists only psycopg[binary]==3.3.6).
- **Gap**: No formal data classification layer exists; field sensitivity is implicit in the code and in the itinerary/amount column semantics. Per the rubric this is aspirational, not a deployment gate.
- **Recommendation**: Record a short classification table for the five business tables (labelling the synthetic nature of charges.amount) so future schema changes do not silently widen agent-visible fields; keep the explicit column projection in the GET handler as the enforcement point.
- **Evidence**: booking_lab/schema.sql

#### DATA-Q2: Data Residency and Sovereignty (conditional)
- **Severity**: Pass (no finding)
- **Conditional**: agent_scope is "write-enabled" - evaluated at the write-enabled severity (BLOCKER for conditional BLOCKERs, RISK-SAFETY for scope-calibrated RISKs) and passed.
- **Finding**: Resolved on configuration and data evidence. The data held is synthetic and non-regulated: bookings carry an agent principal (agent-a/agent-b), a three-letter route pair constrained to [A-Z]{3}-[A-Z]{3}, and an integer amount that booking_lab/run.py records as "synthetic HTTP provider backed by PostgreSQL; no money moved"; no name, email, address, card, health or credential field exists in booking_lab/schema.sql. There is no cross-boundary data movement to constrain: storage is a single local Docker volume per lab run plus the audit sink volume (booking_lab/run.py docker volume create), with no cross-region replication, no read replica, no managed cloud data service, no third-party egress and no IaC specifying any region (no IaC files exist). All published ports bind to 127.0.0.1. booking_lab/AUDIT.md states that an externally operated deployment would need a separate administrative boundary, TLS, managed rotation and an immutable archive, and does not assume such a deployment exists - so no residency obligation applies to the assessed system. Conditional resolution: agent_scope=write-enabled, so this question was evaluated at BLOCKER severity and passed on the evidence. If real passenger data is ever introduced, DATA-Q2 must be re-evaluated and a residency statement produced before agent access.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: The collection endpoint is unbounded. booking_lab/service.py answers GET /bookings with SELECT id,itinerary,amount,status FROM bookings WHERE principal=%s ORDER BY id and returns every row in a single {"bookings":[...]} body; there is no limit, offset, cursor, status filter or sort parameter, and the path regex accepts only /bookings or /bookings/{64-hex}, so no query string is interpreted at all. Single-item retrieval is implemented by fetching the full principal-scoped set and filtering it in Python, so the database read grows with the principal history even for a one-record lookup.
- **Gap**: An agent with a long booking history receives an unbounded array that can exhaust its context window, and the service cannot express "most recent N" or "CONFIRMED only".
- **Recommendation**: Add limit/cursor pagination plus a status filter to GET /bookings with a server-side default and maximum page size, and push the single-id lookup into SQL (WHERE principal=%s AND id=%s) instead of filtering in the handler.
- **Evidence**: booking_lab/service.py

#### DATA-Q4: Input Validation and Schema Enforcement
- **Severity**: RISK-QUALITY
- **Finding**: Validation is strict but rejections are opaque. booking_lab/service.py enforces Content-Type application/json, a 1..8192 byte body, a JSON object, an exact field set {itinerary, amount}, amount of Python type int in 1..10000000, itinerary matching [A-Z]{3}-[A-Z]{3}, Idempotency-Key matching [A-Za-z0-9_-]{1,100}, a parseable UUID X-Correlation-ID and a path matching /bookings/[a-f0-9]{64}; all database access is parameterised through psycopg and CHECK constraints back the enum and amount rules (booking_lab/schema.sql). Every one of those failures raises a bare ValueError that the single handler converts to the same response: 400 {"error":"invalid_request"} with no field name, no constraint and no accepted format. The payment provider likewise raises ValueError on a bad operation_id or amount.
- **Gap**: An agent that constructs a malformed payload cannot tell which field was rejected or why, so it must guess across several candidate fixes - the blind-retry loop the rubric warns about.
- **Recommendation**: Return a structured validation body (for example {"error":"invalid_request","fields":[{"field":"itinerary","constraint":"pattern","expected":"[A-Z]{3}-[A-Z]{3}"}]}) by raising a typed validation error carrying the field and constraint, instead of a bare ValueError.
- **Evidence**: booking_lab/service.py

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Temporal metadata is partial and is not exposed to callers. booking_lab/schema.sql defines created_at timestamptz NOT NULL DEFAULT clock_timestamp() on outbox and created_at timestamptz NOT NULL on audit_events, and the signed ledger records carry created_at plus a retain_until deadline (booking_lab/audit.py), so the audit path is timestamped in timezone-aware form. The business tables have no temporal columns at all: operations, bookings and charges carry no created_at or updated_at, and the API responses from booking_lab/service.py return only id, itinerary, amount, status - no timestamp, no X-Data-Age, no consistency indicator. Reads are strongly consistent (direct PostgreSQL reads with Cache-Control: no-store), so freshness is implicitly current, but nothing states it.
- **Gap**: An agent cannot tell when a booking was created or last changed, cannot order its own history by time, and cannot assert freshness from the response itself.
- **Recommendation**: Add created_at/updated_at timestamptz columns to operations, bookings and charges and surface them (UTC, ISO-8601) in the booking responses; optionally emit an explicit consistency marker since reads are strongly consistent.
- **Evidence**: booking_lab/schema.sql

#### DATA-Q6: PII Redaction in Logs
- **Severity**: Pass (no finding)
- **Finding**: The system is built not to emit user or credential data into logs. booking_lab/service.py overrides Handler.log_message to a no-op with the explicit rationale 'Never log bearer tokens or request bodies', so the default HTTP access log (which would contain the request line) is suppressed; the only application log lines are 'request_retry_pending <ExceptionTypeName>', 'worker_retry_pending' and 'recovery_pending', which carry no payload, principal, token or identifier. booking_lab/audit.py likewise suppresses log_message. booking_lab/run.py docker() never prints container environments or bootstrap SQL/passwords and truncates to the last 1500 characters of stderr on failure; credential env files are written 0600 under .local/, which .gitignore excludes. Responses set Cache-Control: no-store. The data that could reach a log is in any case non-PII (agent principal, three-letter route, synthetic integer amount). No PII-redaction middleware is present because no user-data logging pipeline exists to redact.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Data correctness is expressed as executable invariants rather than as a quality score. booking_lab/run.py computes, at the end of every e2e run, captured_without_confirmed_booking, confirmed_without_captured_payment, pending_operations, undelivered_audit_events and audit_missing_attribution and asserts all are zero; it also compares per-table md5 row-set hashes between the live database and a real pg_dump restore, and asserts the signed ledger record count equals the audit_events projection count. None of this runs in production: there is no null-rate or duplicate monitoring, no freshness SLA and no data-quality dashboard.
- **Gap**: Quality signal exists only at test time, so an agent cannot know at call time whether the invariants still hold.
- **Recommendation**: Promote the five invariant queries in booking_lab/run.py to a scheduled runtime check that publishes each count as a metric, so drift is detected while agents are live.
- **Evidence**: booking_lab/run.py

### 06 - Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Schemas and contracts are neither versioned nor change-detected. booking_lab/schema.sql is a single create-from-scratch DDL file with no migration history and no version marker; the HTTP paths carry no version segment (booking_lab/service.py matches /bookings and /bookings/[a-f0-9]{64} only) and no Accept-Version header is read, although the server does advertise Server: BookingLab/1. There is no JSON Schema, Avro, Protobuf or OpenAPI artifact, no schema registry, no changelog or deprecation notice, and no breaking-change detection or consumer-driven contract test - there is no CI configuration at all (searched for .github/workflows, .gitlab-ci.yml, Jenkinsfile, buildspec.yml: none present). The audit event contract is the one explicitly pinned surface: booking_lab/audit.py validates an exact FIELDS set and the ledger record shape is stable.
- **Gap**: A change to the booking response shape, the scope names or the error vocabulary would break agent tool bindings silently, with nothing in the repository to detect it.
- **Recommendation**: Version the HTTP surface (/v1/bookings or an Accept-Version header), adopt forward-only migration files for schema.sql, and add an automated contract diff against a published specification once API-Q2 is addressed.
- **Evidence**: booking_lab/schema.sql

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field and identifier names are semantically explicit with no legacy codes requiring a dictionary. booking_lab/schema.sql uses principal, request_key, fingerprint, payload, correlation_id, itinerary, amount, status, operation_id, event_type, created_at, delivered_at, captures and refunds; status enums are spelled out (NEW, CHARGED, CONFIRMED, COMPENSATING, COMPENSATED, DECLINED, CANCELLING, CANCELLED; CAPTURED, REFUNDED, DECLINED). Event types are dotted and self-describing (booking.requested, payment.captured, payment.declined, booking.confirmed, booking.compensation_requested, booking.cancel_requested, booking.cancelled, payment.refunded). Error codes read as sentences (payment_declined, idempotency_payload_mismatch, booking_failed_payment_refunded, temporarily_unavailable) and scopes are namespaced (bookings:read, bookings:write, bookings:cancel). The ledger fields in booking_lab/audit.py follow the same convention.
- **Gap**: None. The one abbreviation, opid/oid in booking_lab/service.py, is internal to the implementation and never appears in a response body or column name.
- **Recommendation**: Preserve the convention; it lets LLM-based reasoning interpret responses and audit events without a lookup table.
- **Evidence**: booking_lab/schema.sql

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: There is no data catalog or metadata layer. Searched for Glue/DataHub/Collibra/Alation references, data dictionaries and metadata manifests - none exist (and no IaC files are present). Discoverability rests on three prose/DDL artifacts: booking_lab/schema.sql as the authoritative table and permission definition, booking_lab/AUDIT.md describing the ledger record structure, retention, verification procedure and trust boundary, and booking_lab/README.md describing each module and the scope model. booking_lab/README.md also references ../LABORATORIO_MIT.md for the full API contract, which is not part of this repository.
- **Gap**: Agent tool authors must read the DDL and source to learn what the system holds; semantics are not published anywhere machine-readable.
- **Recommendation**: For a system of this size a short data dictionary committed beside schema.sql is sufficient; a catalog product is not warranted. Bringing the referenced LABORATORIO_MIT.md contract into the repository would close the main documentation gap.
- **Evidence**: booking_lab/README.md

### 07 - Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Correlation is carried through the data path but not through logs, and there is no tracing. booking_lab/service.py accepts X-Correlation-ID (or generates a UUID4), validates it as a UUID, stores it on operations, stamps every outbox event with it, attributes a cancellation to its own request correlation, and propagates it into the signed audit ledger (booking_lab/audit.py FIELDS includes correlation_id); booking_lab/run.py asserts the principal and correlation id reach the outbox for booking.confirmed. Logging, by contrast, is deliberately minimal and unstructured: Handler.log_message is a no-op and the only emitted lines are plain strings 'request_retry_pending <ExceptionTypeName>', 'worker_retry_pending' and 'recovery_pending' with no JSON envelope, no correlation_id, no principal and no operation id. No OpenTelemetry or X-Ray instrumentation exists and traceparent is neither read nor forwarded on the outbound payment and audit calls (booking_lab/requirements.txt contains only psycopg[binary]==3.3.6).
- **Gap**: A failed agent-initiated request cannot be reconstructed from logs: the retry line cannot be tied to a principal, operation or correlation id, and there is no span linking the API, payment provider and audit sink.
- **Recommendation**: Emit JSON log lines including correlation_id, principal, operation_id, route and outcome (continuing to exclude tokens and bodies), and add OpenTelemetry instrumentation that reads and forwards traceparent across the payment and audit calls.
- **Evidence**: booking_lab/service.py

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting exists. Searched the repository for CloudWatch alarms, Prometheus rules, anomaly detection and PagerDuty/OpsGenie integration - none present, and there is no IaC or monitoring configuration of any kind. The health surface an external monitor could use is implemented (GET /health/live, GET /health/ready with a real dependency query in booking_lab/service.py), and booking_lab/run.py captures per-container logs at the end of a run, but nothing watches error rates, latency, the undelivered-outbox backlog or the saga invariants while the system is running.
- **Gap**: Degradation of the agent-facing API would be detected only by the agent failing, with no operator signal and no threshold on the backlog of undelivered audit events or stranded operations.
- **Recommendation**: Scrape /health/ready plus the invariant counters from booking_lab/run.py (pending_operations, undelivered_audit_events) and configure alerts on 5xx rate, p99 latency, readiness failures and backlog growth.
- **Evidence**: booking_lab/service.py

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No metrics are published at runtime. There is no put_metric_data call, StatsD/Prometheus client or dashboard definition anywhere in the repository. Business outcomes are nevertheless computed at test time: booking_lab/run.py writes a structured evidence document containing per-case results and durations, audit_event_count, the five business invariants, restored_table_row_hashes and the independent_audit summary. The underlying business state is queryable from PostgreSQL (bookings by status, charges by state, captures and refunds per operation), so the measurements exist but are never emitted as metrics.
- **Gap**: There is no live signal for whether agent interactions produce good business outcomes (confirmation rate, cancellation rate, decline rate, compensation rate).
- **Recommendation**: Publish the existing counts as custom metrics - bookings confirmed, bookings cancelled, payments declined, compensations executed, undelivered audit events - segmented by principal so agent-driven outcomes can be compared with human-driven ones.
- **Evidence**: booking_lab/run.py

### 08 - Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: The agent-facing surface is not defined as infrastructure as code. Searched for Terraform (.tf/.tfvars), CloudFormation, CDK, Pulumi, SAM, Helm charts, Kustomize, Kubernetes manifests, Ansible and docker-compose: none exist in the repository. Provisioning is an imperative Python/Docker harness, booking_lab/run.py, which does apply strong hardening in code - pinned image digests from booking_lab/images.lock.json, an --internal network for the data plane, --read-only --cap-drop=ALL --security-opt=no-new-privileges, a noexec tmpfs, cgroup memory/CPU/PID limits, non-root USER 65532 in booking_lab/Dockerfile, per-run secrets, 0600 env files and 127.0.0.1-only port publication. But it is a test harness, not a deployment definition: there is no gateway, IAM, TLS or network definition for a real environment, no peer-review gate (no CI configuration exists) and no drift detection.
- **Gap**: Nothing declaratively defines the authentication, networking and exposure of the agent-facing API for a deployed environment, so changes cannot be plan-reviewed or drift-checked.
- **Recommendation**: Express the deployed topology as IaC (gateway or load balancer with TLS, the two API replicas, worker, payment provider, audit sink, PostgreSQL, secrets and network policy), require review on changes, and enable drift detection - reusing the hardening flags already encoded in booking_lab/run.py as the baseline.
- **Evidence**: booking_lab/run.py

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: There is no CI/CD pipeline. Searched for .github/workflows, .gitlab-ci.yml, Jenkinsfile, buildspec.yml, appspec.yml and any pipeline definition - none exist; the repository contains only booking_lab/ source, .gitignore and LICENSE. The 17-case acceptance suite in booking_lab/run.py must be invoked manually (python3 booking_lab/run.py e2e), and because no machine-readable API specification exists (API-Q2) there is nothing a pipeline could diff for breaking changes.
- **Gap**: A change that alters the booking response shape, a scope name or an error code reaches consumers with no automated gate; agent tool breakage would not be detected before deployment.
- **Recommendation**: Add a pipeline that builds the pinned image, runs booking_lab/run.py e2e against the real PostgreSQL/Docker stack, and - once a specification exists - fails on a breaking API diff.
- **Evidence**: booking_lab/run.py

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment or rollback mechanism is defined. There is no blue/green or canary configuration, no CodeDeploy or Helm release, no traffic shifting and no feature flag in the repository; booking_lab/run.py starts containers directly with docker run and its finish() deliberately retains containers and volumes for review rather than managing a release lifecycle. The ingredients for a fast, deterministic rollback are present - immutable base image digests in booking_lab/images.lock.json, a reproducible build from booking_lab/Dockerfile, a recorded app image id and per-file source_sha256 in the run evidence, and additive DDL - but the procedure itself is undefined, and schema.sql has no migration or down-path.
- **Gap**: There is no defined, time-bounded way to return the agent-facing API to a known-good version, and no owner or runbook for doing so.
- **Recommendation**: Define a versioned release with an explicit rollback path (previous image digest redeployed behind a load balancer, or two-slot traffic shifting), add forward-only migrations with compatibility rules so a code rollback does not strand the schema, and rehearse the rollback to confirm a 15-30 minute recovery.
- **Evidence**: booking_lab/images.lock.json

#### ENG-Q4: API Test Coverage
- **Severity**: Pass (no finding)
- **Finding**: The agent-facing API has substantial automated test coverage. booking_lab/run.py defines 17 acceptance cases that drive the real HTTP API against real PostgreSQL, two API replicas, the synthetic payment provider, the recovery worker and the independent audit sink, asserting input handling and authorization (authentication_issuer_audience_expiry_signature_scope rejects ten malformed or forged tokens and checks 403 on insufficient scope), output shape and read paths (create_charge_persist_read_list_with_attribution), idempotency and conflict handling (stable_replay_and_payload_conflict_across_replicas), principal isolation (identity_isolation_and_identity_scoped_idempotency), concurrency (eight_concurrent_requests_two_api_replicas_one_charge), error and edge paths (declined_payment_does_not_create_booking, real_insert_failure_after_charge_refunds_without_orphan, refund_outage_durable_state_and_worker_recovery, two crash-after-external-commit cases, payment_provider_outage_retains_intent_and_recovers, database_outage_fail_closed_and_volume_survives_restart), database-layer authorization (runtime_roles_cannot_rewrite_audit_or_cross_service_tables), audit delivery and de-duplication, a real pg_dump/restore row-hash comparison and ledger tamper/restore verification, plus five closing business invariants. Assertions are enforced (main() refuses to run under -O) and results are written as structured evidence. The absence of a pipeline to run this suite automatically is attributed to ENG-Q2 rather than counted again here.
- **Gap**: None identified.
- **Recommendation**: Preserve the controls cited above; re-evaluate if the implementation or the deployment topology changes.
- **Evidence**: see the files named in the finding text; indexed below.

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: There is no encryption at rest. PostgreSQL data lives in a plain Docker volume created by booking_lab/run.py (docker volume create {prefix}-db-data) and the signed audit ledger in a second plain volume holding /audit/ledger.sqlite; neither is encrypted. No KMS key, kms_key_id, LUKS/dm-crypt setting, PostgreSQL TDE extension or SQLite encryption provider appears anywhere (no IaC files exist; booking_lab/requirements.txt lists only psycopg[binary]==3.3.6). Confidentiality rests on filesystem permissions and process isolation instead: booking_lab/audit.py chmods the ledger to 0600 and the volume is chowned to uid 65532 with mode 0700, env files are 0600, containers run read-only, non-root and cap-drop ALL, and the pg_dump produced during the e2e is written 0600. Transport is also unencrypted (plain HTTP and non-TLS libpq on Docker networks, mitigated today by the --internal network and 127.0.0.1-only publication). The data at rest is synthetic and non-PII.
- **Gap**: A host-level compromise or a copied volume exposes the full booking and synthetic charge history and the audit ledger in cleartext; the ledger HMAC gives tamper evidence but no confidentiality.
- **Recommendation**: Place both volumes on encrypted storage with a managed key (KMS-backed EBS/EFS or an encrypted RDS instance, plus an encrypted archive for the ledger), and enable TLS for libpq and for the payment and audit HTTP hops before any externally exposed deployment.
- **Evidence**: booking_lab/run.py

## Evidence Index

### Source Code

| File | Questions Referenced |
|------|---------------------|
| booking_lab/service.py | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DISC-Q1, DISC-Q2, OBS-Q1, OBS-Q2 |
| booking_lab/auth.py | AUTH-Q4, AUTH-Q5, AUTH-Q7 |
| booking_lab/audit.py | API-Q5, API-Q7, AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q6, DATA-Q5, DATA-Q6, DISC-Q1, DISC-Q2, OBS-Q1, ENG-Q5 |
| booking_lab/audit_verify.py | Reviewed; not cited in a finding |
| booking_lab/client.py | API-Q1, HITL-Q3 |
| booking_lab/run.py | API-Q2, API-Q4, API-Q6, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q2, DATA-Q4, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5 |

### Database Schema and Configuration

| File | Questions Referenced |
|------|---------------------|
| booking_lab/schema.sql | API-Q1, API-Q4, API-Q7, AUTH-Q1, AUTH-Q2, AUTH-Q4, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q6, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q3 |
| .gitignore | AUTH-Q5, DATA-Q6, ENG-Q2 |

### Container Definitions

| File | Questions Referenced |
|------|---------------------|
| booking_lab/Dockerfile | HITL-Q3, ENG-Q1, ENG-Q3 |
| booking_lab/images.lock.json | HITL-Q3, ENG-Q1, ENG-Q3 |

### Dependency Manifests

| File | Questions Referenced |
|------|---------------------|
| booking_lab/requirements.txt | API-Q2, STATE-Q4, DATA-Q1, OBS-Q1, ENG-Q5 |

### Documentation

| File | Questions Referenced |
|------|---------------------|
| booking_lab/README.md | API-Q2, DISC-Q3 |
| booking_lab/AUDIT.md | AUTH-Q6, DATA-Q2, DISC-Q3 |

### Notable Absences (absence cited as evidence)

| Absent artifact | Questions Referenced |
|-----------------|---------------------|
| No OpenAPI/Swagger/GraphQL/Smithy specification | API-Q2, DISC-Q1, ENG-Q2 |
| No IaC (Terraform/CloudFormation/CDK/Helm/Kustomize/K8s/Ansible/docker-compose) | AUTH-Q5, DATA-Q2, ENG-Q1, ENG-Q5, STATE-Q5, API-Q8 |
| No CI/CD pipeline definition | ENG-Q2, ENG-Q3, DISC-Q1 |
| No rate limiting, throttling or rate-limit headers | STATE-Q5, API-Q8 |
| No tracing, metrics or alerting configuration | OBS-Q1, OBS-Q2, OBS-Q3, DATA-Q7 |
| No secrets manager, KMS key or encryption-at-rest setting | AUTH-Q5, ENG-Q5 |
| No data catalog or classification metadata | DATA-Q1, DISC-Q3 |
| ../LABORATORIO_MIT.md (API contract referenced by README) not present in repository | API-Q2, DISC-Q3 |

## Remediation Roadmap

| Phase | Phase Name | Findings | Summary |
|-------|-----------|----------|---------|
| 1 | Blockers | None | No BLOCKER findings were identified: machine identity, write idempotency, saga compensation, immutable audit logging, data scoping and data residency all passed on implemented, test-verified controls. No phase-1 remediation is required before a supervised pilot. |
| 2 | Safety | AUTH-Q4, AUTH-Q5, AUTH-Q7, STATE-Q4, STATE-Q5, STATE-Q6, HITL-Q1, HITL-Q2 | Close the eight RISK-SAFETY gaps that bound what an agent can do and how it can be contained: per-principal rate and transaction limits, circuit breaking/backoff, identity suspension, managed secret rotation with asymmetric token verification, delegation/on-behalf-of attribution, and draft-state plus configurable approval gates. |
| 3 | Quality | API-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q5, API-Q5, API-Q7, API-Q8, DATA-Q1, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3 | Raise agent effectiveness and operability: publish a machine-readable API specification and version the contract, add pagination, field-level validation errors and temporal metadata, add structured logging/tracing, alerting and runtime metrics, and establish IaC, CI/CD, a rollback procedure and encryption at rest. |

## Recommended Actions

| Action | Questions | Priority | Effort | Rationale |
|--------|-----------|----------|--------|-----------|
| Bound agent blast radius with per-principal rate and transaction limits | STATE-Q5, STATE-Q6, STATE-Q4 | P1 | Medium | The API has no throttling and no business-volume caps, so a runaway write-enabled agent is limited only by container resources; the worker additionally retries every 250 ms with no backoff. |
| Make a single agent identity suspendable and move secrets to managed rotation | AUTH-Q7, AUTH-Q5 | P1 | Medium | A shared symmetric JWT key means the only revocation available is rotating the key for every agent at once, and any API host can mint tokens for any principal. |
| Add a draft state and configurable approval gates for high-risk booking operations | HITL-Q1, HITL-Q2 | P1 | High | Every accepted POST captures a synthetic payment and confirms a booking autonomously, with no reviewable intermediate state and no way to require a human decision. |
| Distinguish agent-as-self from agent-on-behalf-of-user in tokens and audit records | AUTH-Q4 | P2 | Medium | Only a single sub claim exists, so delegated agent workflows cannot be bounded by an end user permissions and the ledger cannot show who a booking was made for. |
| Publish and version a machine-readable API contract | API-Q2, DISC-Q1, DATA-Q4, DATA-Q3, DATA-Q5 | P2 | Medium | Agent tool definitions must be hand-authored today and nothing detects a breaking change; pagination, field-level validation errors and timestamps are also missing from the contract. |
| Make agent-initiated requests observable | OBS-Q1, OBS-Q2, OBS-Q3, DATA-Q7 | P2 | Medium | Correlation ids reach the database and signed ledger but never the logs, and no alerting or runtime metric exists for the agent-facing API. |
| Establish deployment governance for an externally exposed deployment | ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q5 | P2 | High | The current runtime is a local, 127.0.0.1-bound Docker harness; a future external deployment needs IaC, CI, a rollback procedure, TLS and encryption at rest, none of which exist yet. |

## Scope Note - Future Externally Exposed Deployment

This assessment describes the system as it exists in the repository: booking_lab/run.py publishes API ports to 127.0.0.1 only, the data plane runs on an `--internal` Docker network, and booking_lab/AUDIT.md explicitly declines to assume an externally operated deployment. No external exposure is claimed here. Should the service later be exposed beyond localhost, the following additional requirements apply and are already reflected in the findings above: TLS termination and non-TLS-free libpq/HTTP hops (ENG-Q5), an edge rate limiter with per-principal quotas (STATE-Q5, STATE-Q6), asymmetric token verification against a managed issuer with revocation and rotation (AUTH-Q5, AUTH-Q7), declarative IaC for the gateway, IAM, secrets and network policy with drift detection (ENG-Q1), a deployment pipeline and rehearsed rollback (ENG-Q2, ENG-Q3), encrypted storage with a managed key for both the PostgreSQL volume and the audit ledger plus an immutable external archive for signed checkpoints (ENG-Q5, and the trust-boundary caveat in booking_lab/AUDIT.md), and structured logging, tracing, alerting and runtime metrics (OBS-Q1, OBS-Q2, OBS-Q3).

