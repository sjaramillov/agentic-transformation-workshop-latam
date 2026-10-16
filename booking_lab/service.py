"""Original MIT booking lab: durable saga, transactional outbox, external payment double."""
import hashlib
import json
import os
import re
import sys
import signal
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from auth import verify


def db(name='DATABASE_URL'):
    return psycopg.connect(os.environ[name], autocommit=True, row_factory=dict_row,
                           connect_timeout=3, options='-c statement_timeout=10000 -c lock_timeout=8000')


def opid(principal, key):
    return hashlib.sha256(('POST /bookings\0'+principal+'\0'+key).encode()).hexdigest()


def emit(c, op, event):
    c.execute('INSERT INTO outbox(id,operation_id,principal,correlation_id,event_type) VALUES(%s,%s,%s,%s,%s)',
              (uuid.uuid4(), op['id'], op['principal'], op['correlation_id'], event))


def locked(c, oid):
    # A session lock spans local commits and external calls, across API replicas/workers.
    c.execute('SELECT pg_advisory_lock(%s)', (int(oid[:16], 16) % (2**63),))


def payment(action, op):
    data = json.dumps({'operation_id': op['id'], 'amount': op['payload']['amount']}).encode()
    req = Request(os.environ['PAYMENT_URL']+'/'+action, data=data,
                  headers={'Content-Type': 'application/json', 'Authorization': 'Bearer '+os.environ['PAYMENT_TOKEN']})
    try:
        with urlopen(req, timeout=4) as response:
            return json.load(response)
    except HTTPError as e:
        if e.code == 402:
            return {'state': 'DECLINED'}
        raise RuntimeError('payment temporarily unavailable') from None
    except OSError:
        raise RuntimeError('payment temporarily unavailable') from None


def transition(c, op, state, event):
    with c.transaction():
        c.execute('UPDATE operations SET status=%s,correlation_id=%s WHERE id=%s', (state, op['correlation_id'], op['id']))
        emit(c, op, event)
    op['status'] = state


def result(c, op, state, code, body, event):
    with c.transaction():
        c.execute('UPDATE operations SET status=%s,response_code=%s,response_body=%s WHERE id=%s',
                  (state, code, Jsonb(body), op['id']))
        emit(c, op, event)
    return code, body


def advance(c, op):
    """Resume from persisted state. Provider must honor stable charge/refund keys."""
    if op['status'] == 'NEW':
        charge = payment('charge', op)
        if charge['state'] == 'DECLINED':
            return result(c, op, 'DECLINED', 402, {'error': 'payment_declined'}, 'payment.declined')
        if os.environ.get('LAB_FAULTS') == '1' and c.execute(
                "SELECT 1 FROM faults WHERE name='crash_after_charge' AND operation_id=%s", (op['id'],)).fetchone():
            os._exit(70)  # Only armed from test-admin SQL; simulate ambiguous external success.
        if charge['state'] != 'CAPTURED':
            return result(c, op, 'COMPENSATED', 409, {'error': 'payment_already_refunded'}, 'payment.refunded')
        transition(c, op, 'CHARGED', 'payment.captured')
    if op['status'] == 'CHARGED':
        try:
            with c.transaction():
                c.execute('INSERT INTO bookings(id,principal,itinerary,amount,status) VALUES(%s,%s,%s,%s,%s)',
                          (op['id'], op['principal'], op['payload']['itinerary'], op['payload']['amount'], 'CONFIRMED'))
                body = {'id': op['id'], 'status': 'CONFIRMED', **op['payload']}
                c.execute("UPDATE operations SET status='CONFIRMED',response_code=201,response_body=%s WHERE id=%s",
                          (Jsonb(body), op['id']))
                emit(c, op, 'booking.confirmed')
            return 201, body
        except psycopg.Error:
            # A failed COMMIT may have succeeded server-side. Re-read before refunding.
            current = c.execute('SELECT * FROM operations WHERE id=%s', (op['id'],)).fetchone()
            if current['status'] == 'CONFIRMED':
                return current['response_code'], current['response_body']
            transition(c, op, 'COMPENSATING', 'booking.compensation_requested')
    if op['status'] in ('COMPENSATING', 'CANCELLING'):
        payment('refund', op)  # Ambiguous timeouts stay retryable, never mark refunded early.
        if os.environ.get('LAB_FAULTS') == '1' and c.execute(
                "SELECT 1 FROM faults WHERE name='crash_after_refund' AND operation_id=%s", (op['id'],)).fetchone():
            os._exit(71)
        if op['status'] == 'CANCELLING':
            with c.transaction():
                c.execute("UPDATE bookings SET status='CANCELLED' WHERE id=%s", (op['id'],))
                c.execute("UPDATE operations SET status='CANCELLED' WHERE id=%s", (op['id'],))
                emit(c, op, 'booking.cancelled')
            return 200, {'id': op['id'], 'status': 'CANCELLED'}
        return result(c, op, 'COMPENSATED', 409,
                      {'error': 'booking_failed_payment_refunded', 'operation_id': op['id']}, 'payment.refunded')
    return op['response_code'], op['response_body']


def create(principal, key, payload, correlation):
    oid = opid(principal, key)
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    with db() as c:
        locked(c, oid)
        op = c.execute('SELECT * FROM operations WHERE id=%s', (oid,)).fetchone()
        if op and op['fingerprint'] != fingerprint:
            return 409, {'error': 'idempotency_payload_mismatch'}
        if not op:
            with c.transaction():
                c.execute('INSERT INTO operations(id,principal,request_key,fingerprint,payload,correlation_id,status) VALUES(%s,%s,%s,%s,%s,%s,%s)',
                          (oid, principal, key, fingerprint, Jsonb(payload), correlation, 'NEW'))
                op = c.execute('SELECT * FROM operations WHERE id=%s', (oid,)).fetchone()
                emit(c, op, 'booking.requested')
        # Preserve the original POST response even after subsequent cancellation.
        if op['response_code'] is not None:
            return op['response_code'], op['response_body']
        return advance(c, op)


def cancel(principal, oid, correlation):
    with db() as c:
        locked(c, oid)
        op = c.execute('SELECT * FROM operations WHERE id=%s AND principal=%s', (oid, principal)).fetchone()
        if not op or op['status'] not in ('CONFIRMED', 'CANCELLING', 'CANCELLED'):
            return 404, {'error': 'booking_not_found'}
        if op['status'] == 'CANCELLED':
            return 200, {'id': oid, 'status': 'CANCELLED'}
        if op['status'] == 'CONFIRMED':
            # Attribute this cancellation to its own authenticated request.
            op['correlation_id'] = correlation
            transition(c, op, 'CANCELLING', 'booking.cancel_requested')
        return advance(c, op)


def recover():
    with db() as c:
        ids = c.execute("SELECT id FROM operations WHERE status IN ('NEW','CHARGED','COMPENSATING','CANCELLING') ORDER BY id LIMIT 100").fetchall()
    for row in ids:
        try:
            with db() as c:
                locked(c, row['id'])
                op = c.execute('SELECT * FROM operations WHERE id=%s', (row['id'],)).fetchone()
                advance(c, op)
        except Exception:
            print('recovery_pending', flush=True)


def deliver():
    with db() as c, c.transaction():
        rows = c.execute('SELECT * FROM outbox WHERE delivered_at IS NULL ORDER BY created_at,id LIMIT 100 FOR UPDATE SKIP LOCKED').fetchall()
        if not rows:
            return
        with db('AUDIT_DATABASE_URL') as sink, sink.transaction():
            for row in rows:
                sink.execute('INSERT INTO audit_events(id,operation_id,principal,correlation_id,event_type,created_at) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',
                             tuple(row[k] for k in ('id','operation_id','principal','correlation_id','event_type','created_at')))
        # Delivery may repeat after a crash here. Sink event UUID deduplicates.
        c.execute('UPDATE outbox SET delivered_at=clock_timestamp() WHERE id=ANY(%s)', ([r['id'] for r in rows],))


class Handler(BaseHTTPRequestHandler):
    server_version = 'BookingLab/1'

    def log_message(self, *_):
        pass  # Never log bearer tokens or request bodies.

    def send(self, code, body):
        raw = json.dumps(body, separators=(',', ':')).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length < 1 or length > 8192 or self.headers.get('Content-Type') != 'application/json':
            raise ValueError()
        d = json.loads(self.rfile.read(length))
        if not isinstance(d, dict):
            raise ValueError()
        return d

    def dispatch(self):
        try:
            self.connection.settimeout(8)
            if self.command == 'GET' and self.path == '/health/live':
                return self.send(200, {'live': True})
            if self.command == 'GET' and self.path == '/health/ready':
                with db() as c:
                    c.execute('SELECT 1 FROM charges LIMIT 1' if self.server.mode=='payments' else 'SELECT 1 FROM operations LIMIT 1')
                return self.send(200, {'ready': True})
            if self.server.mode == 'payments':
                return self.payments()
            if self.path != '/bookings' and not re.fullmatch(r'/bookings/[a-f0-9]{64}', self.path):
                return self.send(404, {'error': 'not_found'})
            required = 'bookings:read' if self.command == 'GET' else 'bookings:write'
            token = self.headers.get('Authorization', '')
            principal, code = verify(token.removeprefix('Bearer ') if token.startswith('Bearer ') else '',
                                     os.environ['JWT_KEY'], required)
            if not principal:
                return self.send(code, {'error': 'unauthorized' if code == 401 else 'forbidden'})
            if self.command == 'POST' and self.path == '/bookings':
                key = self.headers.get('Idempotency-Key', '')
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', key):
                    raise ValueError()
                p = self.body()
                if (set(p) != {'itinerary', 'amount'} or type(p['amount']) is not int
                        or not 0 < p['amount'] <= 10000000 or not isinstance(p['itinerary'], str)
                        or not re.fullmatch(r'[A-Z]{3}-[A-Z]{3}', p['itinerary'])):
                    raise ValueError()
                correlation = uuid.UUID(self.headers.get('X-Correlation-ID', str(uuid.uuid4())))
                code, body = create(principal, key, p, correlation)
                return self.send(code, body)
            if self.command == 'DELETE' and self.path != '/bookings':
                return self.send(*cancel(principal, self.path.rsplit('/', 1)[1], uuid.UUID(self.headers.get('X-Correlation-ID', str(uuid.uuid4())))))
            if self.command == 'GET':
                with db() as c:
                    rows = c.execute('SELECT id,itinerary,amount,status FROM bookings WHERE principal=%s ORDER BY id', (principal,)).fetchall()
                if self.path != '/bookings':
                    rows = [r for r in rows if r['id'] == self.path.rsplit('/', 1)[1]]
                    return self.send(200 if rows else 404, rows[0] if rows else {'error': 'booking_not_found'})
                return self.send(200, {'bookings': rows})
            return self.send(405, {'error': 'method_not_allowed'})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return self.send(400, {'error': 'invalid_request'})
        except (RuntimeError, psycopg.Error, OSError) as error:
            print('request_retry_pending '+type(error).__name__,flush=True)
            return self.send(503, {'error': 'temporarily_unavailable', 'retry_same_idempotency_key': True})

    def payments(self):
        import hmac
        if not hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+os.environ['PAYMENT_TOKEN']):
            return self.send(401, {'error': 'unauthorized'})
        if self.command != 'POST' or self.path not in ('/charge','/refund'):
            return self.send(404, {'error': 'not_found'})
        p = self.body()
        if not re.fullmatch(r'[a-f0-9]{64}', p['operation_id']) or type(p['amount']) is not int or p['amount'] <= 0:
            raise ValueError()
        with db() as c, c.transaction():
            # Two-int lock namespace is distinct from the booking saga's bigint locks.
            c.execute('SELECT pg_advisory_xact_lock(%s,%s)', (17, int(p['operation_id'][:8],16) % 2**31))
            charge = c.execute('SELECT * FROM charges WHERE operation_id=%s', (p['operation_id'],)).fetchone()
            if self.path == '/charge':
                if charge and charge['amount'] != p['amount']:
                    return self.send(409, {'error': 'amount_mismatch'})
                if not charge:
                    decline = c.execute("SELECT 1 FROM faults WHERE name='payment_decline' AND operation_id=%s", (p['operation_id'],)).fetchone()
                    c.execute('INSERT INTO charges(operation_id,amount,state,captures) VALUES(%s,%s,%s,%s)',
                              (p['operation_id'],p['amount'],'DECLINED' if decline else 'CAPTURED',0 if decline else 1))
                charge = c.execute('SELECT * FROM charges WHERE operation_id=%s', (p['operation_id'],)).fetchone()
                reply = (402 if charge['state']=='DECLINED' else 200, {'state':charge['state']})
            else:
                if c.execute("SELECT 1 FROM faults WHERE name='refund_unavailable' AND operation_id=%s", (p['operation_id'],)).fetchone():
                    return self.send(503, {'error': 'refund_unavailable'})
                if not charge or charge['state']=='DECLINED':
                    return self.send(404, {'error': 'charge_not_found'})
                c.execute("UPDATE charges SET state='REFUNDED',refunds=1 WHERE operation_id=%s AND state='CAPTURED'", (p['operation_id'],))
                reply = (200, {'state':'REFUNDED'})
        # Respond only after the provider transaction is durably committed.
        return self.send(*reply)

    do_GET = dispatch
    do_POST = dispatch
    do_DELETE = dispatch


def main():
    mode = sys.argv[1] if len(sys.argv)>1 else 'api'
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    if mode == 'worker':
        while True:
            try:
                recover()
                deliver()
            except Exception:
                print('worker_retry_pending', flush=True)
            time.sleep(0.25)
    else:
        if mode == 'api' and len(os.environ.get('JWT_KEY','')) < 32:
            raise SystemExit('JWT_KEY must contain at least 32 characters')
        server = ThreadingHTTPServer(('0.0.0.0',8080), Handler)
        server.mode = mode
        server.serve_forever()


if __name__ == '__main__':
    main()
