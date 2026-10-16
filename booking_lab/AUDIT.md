# Independent signed audit ledger

The authoritative audit trail is the `audit` process in its own container and Docker volume. `audit_events` in PostgreSQL is a query projection. The application DB owner has no mount, login or signing key for the ledger.

## Delivery and integrity

The recovery worker sends each outbox event to the sink using its UUID. The sink serializes appends in a SQLite `BEGIN IMMEDIATE` transaction with WAL and `synchronous=FULL`. It commits before acknowledging. A replay of the same UUID/content returns the existing signed record; conflicting content is rejected. The worker acknowledges the outbox only after the independent append and the PostgreSQL projection both succeed. Partial delivery can repeat safely.

Each record contains sequence, previous digest, complete event, a minimum retention deadline, SHA256 digest and HMAC-SHA256 signature. The signing key exists only in the audit sink's private configuration and the operator's verification material. The API, payment process and application PostgreSQL never receive it. Read and append credentials are separate; neither HTTP endpoint supports update or delete.

Retention is at least 90 days. This implementation retains records indefinitely and has no automatic purge. SQL triggers reject UPDATE and DELETE. The volume survives a sink restart. Archive data and signed checkpoints before recycling the host.

## Verification

The E2E exports a snapshot and a separately retained checkpoint, tests row tampering and tail truncation, changes the application projection as its DB administrator, and verifies that the independent ledger remains unchanged. It denies UPDATE/DELETE in the sink runtime, restarts the sink, restores a SQLite backup into a different file and verifies the restored chain against the checkpoint.

```bash
python3 booking_lab/audit_verify.py \
  --snapshot .local/db-lab-ID/audit-snapshot.json \
  --checkpoint .local/db-lab-ID/audit-checkpoint.json \
  --secrets .local/db-lab-ID/audit.env
```

Retain the checkpoint separately from the snapshot so a deleted suffix cannot be mistaken for a shorter valid history. Preserve the verification secret securely; never commit `audit.env`. A valid HMAC authenticates the ledger writer, not the truth of a compromised upstream business event.

## Trust boundary

The lab demonstrates separation from the application DB administrator, append-only interfaces and cryptographic tamper detection. It is not hardware WORM. A host root or sink administrator who controls the ledger, signing key and external checkpoint can defeat that boundary. An externally operated deployment should place the sink and checkpoint archive in a separate administrative boundary, use TLS, managed secret rotation and an immutable object archive with its retention policy. These are deployment decisions; they are not silently assumed to exist in CloudShell.
