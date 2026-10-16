"""Original MIT independent append-only audit ledger and offline integrity verifier.

SQLite lives in a dedicated sink container/volume. The application database and
its administrator hold neither this volume nor the ledger signing key. This is
not hardware WORM: protect the sink host and archive signed checkpoints externally.
"""
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FIELDS={'id','operation_id','principal','correlation_id','event_type','created_at'}
ZERO='0'*64
RETENTION_SECONDS=90*24*60*60


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()


def proof(record,key):
    raw=canonical({k:record[k] for k in ('sequence','previous','event','retain_until')})
    digest=hashlib.sha256(raw).hexdigest()
    return digest,hmac.new(key.encode(),digest.encode(),hashlib.sha256).hexdigest()


def verify(records,key,checkpoint):
    previous=ZERO
    for seq,record in enumerate(records,1):
        if record['sequence']!=seq or record['previous']!=previous:
            raise ValueError('audit chain discontinuity')
        digest,signature=proof(record,key)
        if record['digest']!=digest or not hmac.compare_digest(record['signature'],signature):
            raise ValueError('audit signature mismatch')
        previous=digest
    expected={'sequence':len(records),'digest':previous}
    if expected!=checkpoint:
        raise ValueError('audit checkpoint mismatch (including tail deletion)')
    return True


@contextmanager
def connect():
    c=sqlite3.connect(os.environ['AUDIT_PATH'],timeout=10)
    try:
        c.execute('PRAGMA synchronous=FULL')
        with c:
            yield c
    finally:
        c.close()


def initialize():
    if any(len(os.environ.get(k,''))<32 for k in ('AUDIT_SIGNING_KEY','AUDIT_WRITE_TOKEN','AUDIT_READ_TOKEN')):
        raise SystemExit('Independent audit secrets must be at least 32 characters')
    with connect() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('CREATE TABLE IF NOT EXISTS ledger(sequence INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, record TEXT NOT NULL)')
        c.execute("CREATE TRIGGER IF NOT EXISTS immutable_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT,'audit retention: updates prohibited'); END")
        c.execute("CREATE TRIGGER IF NOT EXISTS immutable_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT,'audit retention: deletes prohibited'); END")
    Path(os.environ['AUDIT_PATH']).chmod(0o600)


def append(event):
    if not isinstance(event,dict) or set(event)!=FIELDS or any(not isinstance(v,str) or not 0<len(v)<=150 for v in event.values()):
        raise ValueError('invalid event')
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        existing=c.execute('SELECT record FROM ledger WHERE id=?',(event['id'],)).fetchone()
        if existing:
            record=json.loads(existing[0])
            if record['event']!=event:
                raise ValueError('audit event ID conflict')
            return record
        last=c.execute('SELECT record FROM ledger ORDER BY sequence DESC LIMIT 1').fetchone()
        prior=json.loads(last[0]) if last else {'sequence':0,'digest':ZERO}
        record={'sequence':prior['sequence']+1,'previous':prior['digest'],'event':event,
                'retain_until':int(time.time())+RETENTION_SECONDS}
        record['digest'],record['signature']=proof(record,os.environ['AUDIT_SIGNING_KEY'])
        c.execute('INSERT INTO ledger(sequence,id,record) VALUES(?,?,?)',(record['sequence'],event['id'],canonical(record).decode()))
    return record  # Return only after durable commit; replay uses the event UUID.


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*_):
        pass

    def send(self,status,value):
        body=canonical(value)
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+os.environ['AUDIT_WRITE_TOKEN']):
            return self.send(401,{'error':'unauthorized'})
        if self.path!='/events':
            return self.send(404,{'error':'not_found'})
        try:
            self.connection.settimeout(5)
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=8192:
                raise ValueError()
            return self.send(201,append(json.loads(self.rfile.read(n))))
        except (ValueError,KeyError,TypeError):
            return self.send(409,{'error':'invalid_or_conflicting_event'})
        except (sqlite3.Error,OSError):
            return self.send(503,{'error':'audit_unavailable'})

    def do_GET(self):
        if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+os.environ['AUDIT_READ_TOKEN']):
            return self.send(401,{'error':'unauthorized'})
        if self.path!='/events':
            return self.send(404,{'error':'not_found'})
        with connect() as c:
            records=[json.loads(row[0]) for row in c.execute('SELECT record FROM ledger ORDER BY sequence')]
        checkpoint={'sequence':len(records),'digest':records[-1]['digest'] if records else ZERO}
        return self.send(200,{'records':records,'checkpoint':checkpoint,'retention_days':90})


if __name__=='__main__':
    initialize()
    ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
