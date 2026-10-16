-- Original MIT schema. Bootstrap owner is separate from every runtime role.
CREATE TABLE operations (
 id text PRIMARY KEY, principal text NOT NULL, request_key text NOT NULL,
 fingerprint text NOT NULL, payload jsonb NOT NULL, correlation_id uuid NOT NULL,
 status text NOT NULL CHECK (status IN ('NEW','CHARGED','CONFIRMED','COMPENSATING','COMPENSATED','DECLINED','CANCELLING','CANCELLED')),
 response_code integer, response_body jsonb,
 UNIQUE(principal, request_key)
);
CREATE TABLE bookings (
 id text PRIMARY KEY REFERENCES operations(id), principal text NOT NULL,
 itinerary text NOT NULL, amount integer NOT NULL CHECK(amount > 0),
 status text NOT NULL CHECK(status IN ('CONFIRMED','CANCELLED'))
);
CREATE TABLE outbox (
 id uuid PRIMARY KEY, operation_id text NOT NULL REFERENCES operations(id),
 principal text NOT NULL, correlation_id uuid NOT NULL, event_type text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(), delivered_at timestamptz
);
CREATE TABLE audit_events (
 id uuid PRIMARY KEY, operation_id text NOT NULL, principal text NOT NULL,
 correlation_id uuid NOT NULL, event_type text NOT NULL, created_at timestamptz NOT NULL
);
CREATE TABLE charges (
 operation_id text PRIMARY KEY, amount integer NOT NULL CHECK(amount > 0),
 state text NOT NULL CHECK(state IN ('CAPTURED','REFUNDED','DECLINED')),
 captures integer NOT NULL DEFAULT 1, refunds integer NOT NULL DEFAULT 0
);
-- Only the test administrator may arm faults; there is no HTTP fault endpoint.
CREATE TABLE faults (name text NOT NULL, operation_id text NOT NULL, PRIMARY KEY(name,operation_id));
CREATE FUNCTION fail_booking_insert() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS (SELECT 1 FROM faults WHERE name='booking_insert' AND operation_id=NEW.id) THEN
  RAISE EXCEPTION 'injected booking insert failure';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER test_booking_insert BEFORE INSERT ON bookings FOR EACH ROW EXECUTE FUNCTION fail_booking_insert();
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO booking_app, payment_app, audit_writer, audit_reader;
GRANT SELECT,INSERT,UPDATE ON operations,bookings,outbox TO booking_app;
GRANT SELECT ON faults TO booking_app,payment_app;
GRANT SELECT,INSERT,UPDATE ON charges TO payment_app;
GRANT INSERT ON audit_events TO audit_writer;
GRANT SELECT(id) ON audit_events TO audit_writer;
GRANT SELECT ON audit_events TO audit_reader;
