#!/usr/bin/env python3
"""Reproducible isolated Docker E2E; no cloud credentials or private workshop archive."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time
import uuid
from urllib.request import Request, ProxyHandler, build_opener
from urllib.error import HTTPError, URLError
from auth import encode
from approval import HEADER as APPROVAL_HEADER, issue as issue_approval
from audit import verify as verify_audit
from agent import NoRedirect

ROOT = Path(__file__).resolve().parent
IMAGES = json.loads((ROOT/'images.lock.json').read_text())
PG_IMAGE, PY_IMAGE = IMAGES['postgres'], IMAGES['python']


def resource_limits(info):
    """Read Docker's case-sensitive capabilities; unknown is not support."""
    capabilities = {name: info.get(name) if type(info.get(name)) is bool else None
                    for name in ('MemoryLimit', 'CpuCfsQuota', 'PidsLimit')}
    options = ['--memory', '256m', '--cpus', '1', '--pids-limit', '128'] if all(
        value is True for value in capabilities.values()) else []
    return capabilities, options


def docker(*args, data=None, check=True):
    p = subprocess.run(['docker', *args], input=data, text=True, capture_output=True)
    if check and p.returncode:
        # Never print container environments or bootstrap SQL/passwords.
        raise RuntimeError('docker '+args[0]+' failed: '+p.stderr[-1500:])
    return p


class Lab:
    def __init__(self, output):
        self.output = Path(output).resolve()
        self.work = ROOT.parent / '.local' / ('db-lab-'+uuid.uuid4().hex[:10])
        self.work.mkdir(parents=True, mode=0o700)
        self.prefix = self.work.name
        self.envs = {}
        self.key = secrets.token_hex(32)
        self.approval_key = secrets.token_hex(32)
        self.tokens = {n: encode(self.key,n) for n in ('agent-a','agent-b')}
        self.containers = []
        self.passwords = {n:secrets.token_hex(24) for n in ('postgres','booking_app','payment_app','audit_writer','audit_reader')}
        self.pay_token = secrets.token_hex(32)
        self.audit_key=secrets.token_hex(32)
        self.audit_write=secrets.token_hex(32)
        self.audit_read=secrets.token_hex(32)
        self.tests = []
        self.resource_options = []
        self.evidence = {'schema_version':1, 'started_at_utc':datetime.now(timezone.utc).isoformat(),
                         'implementation':'original MIT booking_lab', 'environment':os.environ.get('LAB_EVIDENCE_ENV','local Docker'),
                         'payments':'synthetic HTTP provider backed by PostgreSQL; no money moved',
                         'evaluation_kind':'database_e2e','cases':self.tests}
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT.parent, text=True, capture_output=True)
        dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT.parent, text=True, capture_output=True)
        self.evidence['repository_commit'] = revision.stdout.strip() if revision.returncode == 0 else None
        self.evidence['working_tree_dirty'] = bool(dirty.stdout.strip()) if dirty.returncode == 0 else None

    def sql(self, text, role='postgres', check=True):
        return docker('exec','-i',self.prefix+'-db','psql','-X','-v','ON_ERROR_STOP=1','-U',role,'-d','workshop','-At',data=text,check=check)

    def scalar(self, text):
        return self.sql(text).stdout.strip()

    def fault(self, name, oid, on=True):
        assert name in ('booking_insert','crash_after_charge','refund_unavailable','payment_decline','crash_after_refund')
        assert len(oid)==64 and all(x in '0123456789abcdef' for x in oid)
        if on:
            self.sql("INSERT INTO faults VALUES ('"+name+"','"+oid+"') ON CONFLICT DO NOTHING;")
        else:
            self.sql("DELETE FROM faults WHERE name='"+name+"' AND operation_id='"+oid+"';")

    def oid(self, key, principal='agent-a'):
        return hashlib.sha256(('POST /bookings\0'+principal+'\0'+key).encode()).hexdigest()

    def env(self, name, values):
        path = self.work / (name+'.env')
        path.write_text(''.join(k+'='+v+'\n' for k,v in values.items()))
        path.chmod(0o600)
        self.envs[name] = path
        return path

    def start(self, name, mode, role, port=None, audit=False):
        values = {'DATABASE_URL':f'postgresql://{role}:{self.passwords[role]}@{self.prefix}-db/workshop',
                  'PAYMENT_URL':f'http://{self.prefix}-payments:8080','PAYMENT_TOKEN':self.pay_token}
        if mode == 'api':
            values.update(JWT_KEY=self.key,APPROVAL_KEY=self.approval_key,LAB_FAULTS='1')
        if audit:
            values.update(AUDIT_URL=f'http://{self.prefix}-audit:8080',AUDIT_WRITE_TOKEN=self.audit_write)
            values['AUDIT_DATABASE_URL']=f'postgresql://audit_writer:{self.passwords["audit_writer"]}@{self.prefix}-db/workshop'
        options = ['--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',*self.resource_options,'--tmpfs','/tmp:rw,noexec,nosuid,size=16m']
        if port is not None:
            options += ['-p',f'127.0.0.1:{port}:8080']
        container = self.prefix+'-'+name
        docker('run','-d','--name',container,'--network',self.prefix+'-front' if mode=='api' else self.prefix,*options,
               '--env-file',str(self.env(name,values)), self.prefix+'-app','python','service.py',mode)
        self.containers.append(container)
        if mode=='api':
            docker('network','connect',self.prefix,container)

    def audit_snapshot(self):
        # Request through the sink's own network namespace, no host port published.
        code="import json,os,urllib.request; r=urllib.request.Request('http://127.0.0.1:8080/events',headers={'Authorization':'Bearer '+os.environ['AUDIT_READ_TOKEN']}); print(urllib.request.urlopen(r).read().decode())"
        return json.loads(docker('exec',self.prefix+'-audit','python','-c',code).stdout)

    def refresh_ports(self):
        ports=[]
        for name in ('api-a','api-b'):
            bindings=json.loads(docker('inspect',self.prefix+'-'+name).stdout)[0]['NetworkSettings']['Ports'].get('8080/tcp')
            if not bindings:
                return False
            ports.append(int(bindings[0]['HostPort']))
        self.ports=ports
        self.port_a,self.port_b=ports
        return True

    def wait(self, fn, timeout=35):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            try:
                if fn():
                    return
            except (OSError, RuntimeError, ValueError, HTTPError, URLError):
                pass
            time.sleep(0.2)
        raise AssertionError('condition did not become true')

    def req(self, method, path='/bookings', payload=None, key=None, principal='agent-a', token=None, port=18881, correlation=None, approval=True):
        headers={'Authorization':'Bearer '+(encode(self.key, principal) if token is None else token)}
        if key is not None:
            headers['Idempotency-Key']=key
        if correlation:
            headers['X-Correlation-ID']=correlation
        # This test-admin fixture explicitly authorizes its synthetic mutations.
        # The user-facing agent requires interactive approval; negative cases
        # pass False or a deliberately invalid capability to test server denial.
        if method in ('POST', 'DELETE') and approval is not False:
            headers[APPROVAL_HEADER] = (issue_approval(self.approval_key, principal, method, path, payload, key or '')
                                        if approval is True else approval)
        raw=None
        if payload is not None:
            raw=json.dumps(payload).encode();headers['Content-Type']='application/json'
        req=Request(f'http://127.0.0.1:{port}'+path,data=raw,headers=headers,method=method)
        try:
            with build_opener(ProxyHandler({}), NoRedirect()).open(req,timeout=12) as r:
                return r.status,json.load(r)
        except HTTPError as e:
            return e.code,json.load(e)

    def case(self, name, fn):
        start=time.monotonic()
        try:
            fn()
        except BaseException as error:
            self.tests.append({'name':name, 'result':'failed', 'failure_type':type(error).__name__,
                               'duration_seconds':round(time.monotonic()-start,3)})
            raise
        self.tests.append({'name':name,'result':'passed','duration_seconds':round(time.monotonic()-start,3)})
        print('PASS '+name,flush=True)

    def setup(self):
        info=json.loads(docker('info','--format','{{json .}}').stdout)
        capabilities, self.resource_options = resource_limits(info)
        self.evidence['resource_limit_capabilities'] = capabilities
        self.evidence['resource_limits_available'] = bool(self.resource_options)
        if not self.evidence['resource_limits_available']:
            print('Docker did not confirm all cgroup limits; retaining network, filesystem and capability isolation',flush=True)
        for image in (PG_IMAGE,PY_IMAGE):
            print('Pull '+image,flush=True)
            docker('pull',image)
        self.evidence['base_images']={image:json.loads(docker('image','inspect',image).stdout)[0]['RepoDigests'] for image in (PG_IMAGE,PY_IMAGE)}
        print('Build original application',flush=True)
        docker('build','-t',self.prefix+'-app',str(ROOT))
        self.evidence['app_image_id']=json.loads(docker('image','inspect',self.prefix+'-app').stdout)[0]['Id']
        self.evidence['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.iterdir()) if p.is_file()}
        docker('network','create','--internal',self.prefix)
        docker('network','create',self.prefix+'-front')
        docker('volume','create',self.prefix+'-db-data')
        docker('run','-d','--name',self.prefix+'-db','--network',self.prefix,*(['--memory','512m','--cpus','1','--pids-limit','128'] if self.resource_options else []),
               '--env-file',str(self.env('db',{'POSTGRES_PASSWORD':self.passwords['postgres'],'POSTGRES_DB':'workshop'})),
               '-v',self.prefix+'-db-data:/var/lib/postgresql/data',PG_IMAGE)
        self.containers.append(self.prefix+'-db')
        self.wait(lambda:docker('exec',self.prefix+'-db','pg_isready','-h','127.0.0.1','-U','postgres',check=False).returncode==0)
        self.evidence['postgres_version']=self.scalar('SHOW server_version;')
        self.evidence['synchronous_commit']=self.scalar('SHOW synchronous_commit;')
        roles='\n'.join(f"CREATE ROLE {r} LOGIN PASSWORD '{p}';" for r,p in self.passwords.items() if r!='postgres')
        self.sql(roles+'\n'+(ROOT/'schema.sql').read_text())
        # Independent sink: separate process, volume and signing key. The app DB
        # administrator has no credentials or mount for the authoritative ledger.
        docker('volume','create',self.prefix+'-audit-data')
        docker('run','--rm','--network','none','--user','0','-v',self.prefix+'-audit-data:/audit',PY_IMAGE,
               'python','-c','import os; os.chown("/audit",65532,65532); os.chmod("/audit",0o700)')
        audit_env=self.env('audit',{'AUDIT_PATH':'/audit/ledger.sqlite','AUDIT_SIGNING_KEY':self.audit_key,
                                  'AUDIT_WRITE_TOKEN':self.audit_write,'AUDIT_READ_TOKEN':self.audit_read})
        docker('run','-d','--name',self.prefix+'-audit','--network',self.prefix,'--read-only','--cap-drop=ALL',
               '--security-opt=no-new-privileges',*self.resource_options,'--env-file',str(audit_env),
               '-v',self.prefix+'-audit-data:/audit',self.prefix+'-app','python','audit.py')
        self.containers.append(self.prefix+'-audit')
        self.wait(lambda: self.audit_snapshot()['retention_days']==90)
        self.start('payments','payments','payment_app')
        # Ephemeral host ports are discovered from Docker, avoiding collisions with user services.
        self.ports=[]
        for name in ('api-a','api-b'):
            self.start(name,'api','booking_app',port=0)
        self.wait(self.refresh_ports)
        self.wait(lambda: self.req('GET','/health/ready',port=self.port_a)[0]==200)
        self.wait(lambda: self.req('GET','/health/ready',port=self.port_b)[0]==200)
        self.tokens={n:encode(self.key,n) for n in ('agent-a','agent-b')}

    def session_file(self):
        session = self.work/'session.json'
        session.write_text(json.dumps({'prefix': self.prefix, 'port': self.port_a,
                                       'key': self.key, 'approval_key': self.approval_key}))
        session.chmod(0o600)
        return session

    def quiesce_for_snapshot(self):
        """Freeze owned writers after draining recovery and audit delivery.

        pg_dump has its own consistent snapshot. Comparing that dump with a
        later live database requires stopping all writers first; otherwise the
        worker can legitimately deliver more audit events between the snapshots.
        """
        roles = ('api-a', 'api-b', 'worker', 'payments')
        barrier = {'result': 'pending', 'phase': 'verify_ownership',
                   'started_at_utc': datetime.now(timezone.utc).isoformat(),
                   'stop_order': [], 'drain_polls': 0}
        self.evidence['snapshot_barrier'] = barrier

        def running(role):
            value = docker('inspect', '-f', '{{.State.Running}}', self.prefix+'-'+role).stdout.strip()
            if value not in ('true', 'false'):
                raise RuntimeError('Cannot verify snapshot writer state: '+role)
            return value == 'true'

        def queue_counts():
            # One statement observes both counts at the same PostgreSQL snapshot.
            raw = self.scalar("SELECT (SELECT count(*) FROM operations WHERE status IN "
                              "('NEW','CHARGED','COMPENSATING','CANCELLING')),"
                              "(SELECT count(*) FROM outbox WHERE delivered_at IS NULL);")
            values = raw.split('|')
            if len(values) != 2 or any(not value.isdigit() for value in values):
                raise RuntimeError('Invalid snapshot queue counts')
            return dict(zip(('pending_operations', 'undelivered_audit_events'), map(int, values)))

        try:
            if any(self.prefix+'-'+role not in self.containers for role in roles):
                raise AssertionError('Snapshot barrier only stops registered lab writers')
            # Close ingress first so even an external caller of the lab cannot
            # add a new intention between the final drain and the snapshot.
            barrier['phase'] = 'stop_ingress'
            for role in ('api-a', 'api-b'):
                docker('stop', self.prefix+'-'+role)
                barrier['stop_order'].append(role)
                if running(role):
                    raise AssertionError('Snapshot ingress still running: '+role)
            barrier['phase'] = 'drain_recovery_and_audit'

            def drained():
                counts = queue_counts()
                barrier['drain_polls'] += 1
                barrier['last_drain_counts'] = counts
                return all(value == 0 for value in counts.values())

            self.wait(drained, timeout=60)
            barrier['phase'] = 'stop_background_writers'
            for role in ('worker', 'payments'):
                docker('stop', self.prefix+'-'+role)
                barrier['stop_order'].append(role)
                if running(role):
                    raise AssertionError('Snapshot background writer still running: '+role)
            barrier['phase'] = 'verify_quiescence'
            barrier['writers_running_before_dump'] = {role: running(role) for role in roles}
            barrier['final_queue_counts'] = queue_counts()
            if any(barrier['writers_running_before_dump'].values()):
                raise AssertionError('Snapshot writer restarted before dump')
            if any(barrier['final_queue_counts'].values()):
                raise AssertionError('Snapshot is not quiescent after writers stopped')
            barrier['phase'], barrier['result'] = 'verified', 'passed'
            barrier['verified_at_utc'] = datetime.now(timezone.utc).isoformat()
        except BaseException as error:
            barrier['result'] = 'failed'
            barrier['failure_type'] = type(error).__name__
            raise

    def verify_database_restore(self):
        self.quiesce_for_snapshot()
        dump=docker('exec',self.prefix+'-db','pg_dump','-U','postgres','--no-owner','--no-acl','workshop').stdout
        path=self.work/'workshop.sql';path.write_text(dump);path.chmod(0o600)
        self.sql('CREATE DATABASE restore_check;')
        docker('exec','-i',self.prefix+'-db','psql','-X','-v','ON_ERROR_STOP=1','-U','postgres','-d','restore_check',data=dump)
        counts=docker('exec',self.prefix+'-db','psql','-X','-U','postgres','-d','restore_check','-Atc',
                      'SELECT (SELECT count(*) FROM bookings),(SELECT count(*) FROM charges),(SELECT count(*) FROM audit_events);').stdout.strip()
        expected=self.scalar('SELECT (SELECT count(*) FROM bookings),(SELECT count(*) FROM charges),(SELECT count(*) FROM audit_events);')
        assert counts==expected,(counts,expected)
        hashes={}
        for table in ('operations','bookings','charges','outbox','audit_events','faults'):
            query="SELECT md5(coalesce(string_agg(row_to_json(r)::text,'' ORDER BY row_to_json(r)::text),'')) FROM "+table+" r;"
            original=self.scalar(query)
            restored=docker('exec',self.prefix+'-db','psql','-X','-U','postgres','-d','restore_check','-Atc',query).stdout.strip()
            assert original==restored,(table,original,restored)
            hashes[table]=original
        self.evidence['restored_table_row_hashes']=hashes
        self.evidence['restore_counts_bookings_charges_audit']=counts
        self.evidence['synthetic_dump_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

    def run_tests(self):
        p={'itinerary':'BOG-MDE','amount':12500}
        def auth():
            for token in ('',encode(self.key,exp=0),encode(self.key,aud='wrong'),encode(self.key,iss='wrong'),encode(self.key,nbf=9999999999),encode(self.key,exp=float('nan')),encode(self.key,exp=float('inf')),encode(self.key,iat=False),encode(self.key,exp=9999999999),encode('x'*64)):
                assert self.req('POST',payload=p,key='auth',token=token,port=self.port_a)[0]==401
            assert self.req('POST',payload=p,key='auth',token=encode(self.key,scope='bookings:read'),port=self.port_a)[0]==403
            assert self.req('DELETE','/bookings/'+'a'*64,token=encode(self.key,scope='bookings:read bookings:write'),port=self.port_a)[0]==403
            assert self.scalar('SELECT count(*) FROM charges;')=='0'
        self.case('authentication_issuer_audience_expiry_signature_scope',auth)
        def approval_binding():
            key = 'approval-gate'
            invalid = [False, 'malformed',
                issue_approval(self.approval_key, 'agent-b', 'POST', '/bookings', p, key),
                issue_approval(self.approval_key, 'agent-a', 'POST', '/bookings', {**p, 'amount': 1}, key),
                issue_approval(self.approval_key, 'agent-a', 'POST', '/bookings', p, 'another-key'),
                issue_approval(self.approval_key, 'agent-a', 'POST', '/bookings', p, key, now=int(time.time())-301),
                issue_approval(self.approval_key, 'agent-a', 'DELETE', '/bookings/'+'a'*64),
                issue_approval('x'*64, 'agent-a', 'POST', '/bookings', p, key)]
            for capability in invalid:
                code, body = self.req('POST', payload=p, key=key, port=self.port_a, approval=capability)
                assert (code, body) == (403, {'error': 'approval_required_or_invalid'}), (code, body)
            assert self.scalar('SELECT count(*) FROM operations;') == '0'
            assert self.scalar('SELECT count(*) FROM charges;') == '0'
        self.case('server_approval_missing_expired_subject_payload_key_action_signature_denied', approval_binding)
        correlation=str(uuid.uuid4())
        def happy():
            code,body=self.req('POST',payload=p,key='happy',port=self.port_a,correlation=correlation)
            assert code==201,(code,body)
            self.happy=body
            assert self.req('GET','/bookings/'+body['id'],port=self.port_b)==(200,body)
            assert self.req('GET',port=self.port_b)[1]['bookings']==[body]
            assert self.scalar("SELECT principal||':'||correlation_id FROM outbox WHERE event_type='booking.confirmed';")=='agent-a:'+correlation
            assert self.scalar('SELECT count(*) FROM bookings;')=='1'
        self.case('create_charge_persist_read_list_with_attribution',happy)
        def replay():
            assert self.req('POST',payload=p,key='happy',port=self.port_b)==(201,self.happy)
            assert self.req('POST',payload={**p,'amount':1},key='happy',port=self.port_b)[0]==409
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+self.happy['id']+"';")=='1'
        self.case('stable_replay_and_payload_conflict_across_replicas',replay)
        def isolation():
            assert self.req('GET','/bookings/'+self.happy['id'],principal='agent-b',port=self.port_b)[0]==404
            assert self.req('DELETE','/bookings/'+self.happy['id'],principal='agent-b',port=self.port_b)[0]==404
            code,b=self.req('POST',payload=p,key='happy',principal='agent-b',port=self.port_b)
            assert code==201 and b['id']!=self.happy['id']
        self.case('identity_isolation_and_identity_scoped_idempotency',isolation)
        def concurrent():
            with ThreadPoolExecutor(max_workers=8) as pool:
                responses=list(pool.map(lambda i:self.req('POST',payload=p,key='parallel',port=self.ports[i%2]),range(8)))
            assert all(x==responses[0] and x[0]==201 for x in responses),responses
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+self.oid('parallel')+"';")=='1'
            assert self.scalar("SELECT count(*) FROM bookings WHERE id='"+self.oid('parallel')+"';")=='1'
        self.case('eight_concurrent_requests_two_api_replicas_one_charge',concurrent)
        def compensation():
            oid=self.oid('insert-fails');self.fault('booking_insert',oid)
            assert self.req('POST',payload=p,key='insert-fails',port=self.port_a)[0]==409
            assert self.scalar("SELECT state||':'||captures||':'||refunds FROM charges WHERE operation_id='"+oid+"';")=='REFUNDED:1:1'
            assert self.scalar("SELECT count(*) FROM bookings WHERE id='"+oid+"';")=='0'
            assert self.req('POST',payload=p,key='insert-fails',port=self.port_b)[0]==409
        self.case('real_insert_failure_after_charge_refunds_without_orphan',compensation)
        def pending():
            oid=self.oid('refund-outage');self.fault('booking_insert',oid);self.fault('refund_unavailable',oid)
            assert self.req('POST',payload=p,key='refund-outage',port=self.port_a)[0]==503
            assert self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='COMPENSATING'
            assert self.scalar("SELECT state FROM charges WHERE operation_id='"+oid+"';")=='CAPTURED'
            self.fault('refund_unavailable',oid,False)
            self.start('worker','worker','booking_app',audit=True)
            self.wait(lambda:self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='COMPENSATED')
            assert self.scalar("SELECT state||':'||refunds FROM charges WHERE operation_id='"+oid+"';")=='REFUNDED:1'
        self.case('refund_outage_durable_state_and_worker_recovery',pending)
        def crash():
            # Stop the worker to control the crash window deterministically.
            docker('stop',self.prefix+'-worker')
            oid=self.oid('crash');self.fault('crash_after_charge',oid)
            try:
                self.req('POST',payload=p,key='crash',port=self.port_a)
                raise AssertionError('API should exit after provider commit')
            except (URLError,OSError):
                pass
            self.wait(lambda:docker('inspect','-f','{{.State.Running}}',self.prefix+'-api-a').stdout.strip()=='false')
            assert self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='NEW'
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';")=='1'
            self.fault('crash_after_charge',oid,False)
            docker('start',self.prefix+'-worker')
            self.wait(lambda:self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='CONFIRMED')
            docker('start',self.prefix+'-api-a')
            self.wait(lambda:self.refresh_ports() and self.req('GET','/health/ready',port=self.port_a)[0]==200)
            assert self.req('POST',payload=p,key='crash',port=self.port_b)[0]==201
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';")=='1'
        self.case('process_crash_after_external_commit_reconciles_without_double_charge',crash)
        def provider_outage():
            docker('stop',self.prefix+'-worker',self.prefix+'-payments')
            assert self.req('POST',payload=p,key='provider-outage',port=self.port_b)[0]==503
            oid=self.oid('provider-outage')
            assert self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='NEW'
            assert self.scalar("SELECT count(*) FROM charges WHERE operation_id='"+oid+"';")=='0'
            docker('start',self.prefix+'-payments',self.prefix+'-worker')
            self.wait(lambda:self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='CONFIRMED')
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';")=='1'
        self.case('payment_provider_outage_retains_intent_and_recovers',provider_outage)
        def refund_crash():
            docker('stop',self.prefix+'-worker')
            code,body=self.req('POST',payload=p,key='refund-crash',port=self.port_a)
            assert code==201
            oid=body['id'];self.fault('crash_after_refund',oid)
            try:
                self.req('DELETE','/bookings/'+oid,port=self.port_a)
                raise AssertionError('API should exit after refund commit')
            except (URLError,OSError):
                pass
            self.wait(lambda:docker('inspect','-f','{{.State.Running}}',self.prefix+'-api-a').stdout.strip()=='false')
            assert self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='CANCELLING'
            assert self.scalar("SELECT state||':'||refunds FROM charges WHERE operation_id='"+oid+"';")=='REFUNDED:1'
            self.fault('crash_after_refund',oid,False)
            docker('start',self.prefix+'-worker')
            self.wait(lambda:self.scalar("SELECT status FROM operations WHERE id='"+oid+"';")=='CANCELLED')
            assert self.scalar("SELECT refunds FROM charges WHERE operation_id='"+oid+"';")=='1'
            docker('start',self.prefix+'-api-a')
            self.wait(lambda:self.refresh_ports() and self.req('GET','/health/ready',port=self.port_a)[0]==200)
        self.case('process_crash_after_refund_recovers_without_second_refund',refund_crash)
        def decline():
            oid=self.oid('declined');self.fault('payment_decline',oid)
            assert self.req('POST',payload=p,key='declined',port=self.port_a)[0]==402
            assert self.scalar("SELECT count(*) FROM bookings WHERE id='"+oid+"';")=='0'
        self.case('declined_payment_does_not_create_booking',decline)
        def cancellation():
            path='/bookings/'+self.happy['id']
            assert self.req('DELETE',path,port=self.port_a)[1]['status']=='CANCELLED'
            assert self.req('DELETE',path,port=self.port_b)[0]==200
            assert self.req('GET',path,port=self.port_b)[1]['status']=='CANCELLED'
            assert self.req('POST',payload=p,key='happy',port=self.port_a)==(201,self.happy)
            assert self.scalar("SELECT refunds FROM charges WHERE operation_id='"+self.happy['id']+"';")=='1'
        self.case('cancel_refund_repeat_and_preserve_create_response',cancellation)
        def audit_outage():
            self.wait(lambda:self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;')=='0')
            self.sql('REVOKE INSERT ON audit_events FROM audit_writer;')
            assert self.req('POST',payload=p,key='audit-outage',port=self.port_a)[0]==201
            self.wait(lambda:int(self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;'))>=3)
            assert self.scalar("SELECT count(*) FROM audit_events WHERE operation_id='"+self.oid('audit-outage')+"';")=='0'
            docker('restart',self.prefix+'-worker')
            self.sql('GRANT INSERT ON audit_events TO audit_writer;')
            self.wait(lambda:self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;')=='0')
            assert self.scalar("SELECT count(*) FROM audit_events WHERE operation_id='"+self.oid('audit-outage')+"';")=='3'
            assert self.scalar('SELECT count(*) FROM outbox;')==self.scalar('SELECT count(*) FROM audit_events;')
        self.case('audit_delivery_failure_restart_and_durable_outbox_drain',audit_outage)
        def rights():
            for role in ('booking_app','payment_app','audit_writer','audit_reader'):
                assert self.sql('DELETE FROM audit_events;',role=role,check=False).returncode!=0
                assert self.sql("UPDATE audit_events SET principal='forged';",role=role,check=False).returncode!=0
            assert self.sql('SELECT * FROM audit_events;',role='booking_app',check=False).returncode!=0
            assert self.sql('CREATE TABLE unauthorized(id int);',role='booking_app',check=False).returncode!=0
            assert self.sql('SELECT * FROM bookings;',role='payment_app',check=False).returncode!=0
        self.case('runtime_roles_cannot_rewrite_audit_or_cross_service_tables',rights)
        def duplicate_delivery():
            self.sql('UPDATE outbox SET delivered_at=NULL;')
            self.wait(lambda:self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;')=='0')
            assert self.scalar('SELECT count(*) FROM outbox;')==self.scalar('SELECT count(*) FROM audit_events;')
        self.case('audit_redelivery_deduplicates_event_ids',duplicate_delivery)
        def restart():
            before=self.req('GET',port=self.port_b)
            docker('stop',self.prefix+'-worker',self.prefix+'-db')
            assert self.req('GET','/health/live',port=self.port_a)[0]==200
            assert self.req('GET','/health/ready',port=self.port_a)[0]==503
            assert self.req('POST',payload=p,key='db-down',port=self.port_a)[0]==503
            docker('start',self.prefix+'-db')
            self.wait(lambda:self.req('GET','/health/ready',port=self.port_b)[0]==200)
            docker('restart',self.prefix+'-api-a',self.prefix+'-api-b')
            docker('start',self.prefix+'-worker')
            self.wait(lambda:self.refresh_ports() and self.req('GET',port=self.port_b)==before)
            assert self.scalar("SELECT count(*) FROM charges WHERE operation_id='"+self.oid('db-down')+"';")=='0'
        self.case('database_outage_fail_closed_and_volume_survives_restart',restart)
        self.run_agent_tests()
        self.case('actual_pg_dump_restore_into_separate_database', self.verify_database_restore)
        self.wait(lambda:self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;')=='0')
        self.evidence['invariants']={
          'captured_without_confirmed_booking':int(self.scalar("SELECT count(*) FROM charges c LEFT JOIN bookings b ON b.id=c.operation_id AND b.status='CONFIRMED' WHERE c.state='CAPTURED' AND b.id IS NULL;")),
          'confirmed_without_captured_payment':int(self.scalar("SELECT count(*) FROM bookings b LEFT JOIN charges c ON c.operation_id=b.id AND c.state='CAPTURED' WHERE b.status='CONFIRMED' AND c.operation_id IS NULL;")),
          'pending_operations':int(self.scalar("SELECT count(*) FROM operations WHERE status IN ('NEW','CHARGED','COMPENSATING','CANCELLING');")),
          'undelivered_audit_events':int(self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;')),
          'audit_missing_attribution':int(self.scalar("SELECT count(*) FROM audit_events WHERE principal='' OR correlation_id IS NULL OR operation_id='';"))}
        assert all(v==0 for v in self.evidence['invariants'].values()),self.evidence['invariants']
        def audit_integrity():
            snapshot=self.audit_snapshot()
            records=snapshot['records']; checkpoint=snapshot['checkpoint']
            assert verify_audit(records,self.audit_key,checkpoint)
            assert len(records)==int(self.scalar('SELECT count(*) FROM audit_events;'))
            # Persist an external checkpoint outside both databases for later verification.
            (self.work/'audit-checkpoint.json').write_text(json.dumps(checkpoint))
            (self.work/'audit-snapshot.json').write_text(json.dumps(snapshot))
            for changed in (records[:-1],json.loads(json.dumps(records))):
                if len(changed)==len(records):
                    changed[0]['event']['principal']='forged'
                try:
                    verify_audit(changed,self.audit_key,checkpoint)
                except ValueError:
                    pass
                else:
                    raise AssertionError('tampered audit accepted')
            # Alter the application projection with its administrator: the independent
            # ledger remains valid and retains the authentic principal.
            first=records[0]['event']
            self.sql("UPDATE audit_events SET principal='forged' WHERE id='"+first['id']+"';")
            assert self.audit_snapshot()==snapshot
            assert self.scalar("SELECT principal FROM audit_events WHERE id='"+first['id']+"';")!=first['principal']
            self.sql("UPDATE audit_events SET principal='"+first['principal']+"' WHERE id='"+first['id']+"';")
            # SQL UPDATE/DELETE cannot remove retained records through the sink runtime.
            for sql in ('DELETE FROM ledger','UPDATE ledger SET record=record'):
                code="import sqlite3,os; c=sqlite3.connect(os.environ['AUDIT_PATH']); c.execute("+repr(sql)+"); c.commit()"
                assert docker('exec',self.prefix+'-audit','python','-c',code,check=False).returncode!=0
            docker('restart',self.prefix+'-audit')
            self.wait(lambda: self.audit_snapshot()==snapshot)
            # SQLite backup is restored into a separate file and independently verified.
            code="import sqlite3,os; src=sqlite3.connect(os.environ['AUDIT_PATH']); dst=sqlite3.connect('/audit/restore-check.sqlite'); src.backup(dst); print(dst.execute('PRAGMA integrity_check').fetchone()[0])"
            assert docker('exec',self.prefix+'-audit','python','-c',code).stdout.strip()=='ok'
            code="import sqlite3,json; c=sqlite3.connect('/audit/restore-check.sqlite'); print(json.dumps([json.loads(r[0]) for r in c.execute('SELECT record FROM ledger ORDER BY sequence')]))"
            restored=json.loads(docker('exec',self.prefix+'-audit','python','-c',code).stdout)
            assert restored==records and verify_audit(restored,self.audit_key,checkpoint)
            self.evidence['independent_audit']={'records':len(records),'checkpoint':checkpoint,
                'retention_days':90,'tamper_and_truncation_detected':True,'app_db_admin_cannot_change_ledger':True,
                'runtime_update_delete_denied':True,'restart_persisted':True,'backup_restored_and_verified':True}
        self.case('independent_signed_audit_retention_tamper_restart_restore',audit_integrity)
        self.evidence['audit_event_count']=int(self.scalar('SELECT count(*) FROM audit_events;'))
        self.evidence['result']='passed'

    def run_agent_tests(self):
        """Drive the real CLI in fresh processes against the same live PostgreSQL."""
        session = self.session_file()

        def cli(state, command, goal=None, answer='', subject='agent-a', expected=0):
            argv = [sys.executable, str(ROOT/'agent.py'), '--session', str(session),
                    '--state', str(state), '--subject', subject]
            if goal is not None:
                argv += ['--goal', goal]
            process = subprocess.run(argv+[command], input=answer, text=True, capture_output=True, timeout=30)
            assert process.returncode == expected, (command, process.returncode, process.stderr[-1500:], process.stdout[-1500:])
            return json.loads(process.stdout) if process.stdout.strip() else {'error': 'CLI rejected request'}

        def plan(name, goal):
            state = self.work/(name+'.json')
            cli(state, 'plan', goal)
            return state

        def approve(state):
            proposal = json.loads(state.read_text())
            cli(state, 'approve', answer='APROBAR '+proposal['plan_digest']+'\n')
            return proposal

        def no_write_before_approval():
            before = self.scalar('SELECT count(*) FROM operations;')
            state = plan('agent-rejected', 'create BOG-MDE 12500')
            cli(state, 'execute', expected=2)
            cli(state, 'approve', answer='no\n', expected=2)
            cli(state, 'execute', expected=2)
            assert self.scalar('SELECT count(*) FROM operations;') == before
        self.case('agent_cli_plan_unapproved_execute_and_rejection_have_no_writes', no_write_before_approval)

        def approved_create():
            state = plan('agent-create', 'create BOG-MDE 12500')
            proposal = approve(state)
            outcome = cli(state, 'execute')
            assert outcome['status'] == 'completed'
            oid = self.oid(proposal['plan']['request_key'])
            self.agent_booking_id = oid
            assert self.req('GET', '/bookings/'+oid, port=self.port_b)[1]['status'] == 'CONFIRMED'
            assert cli(state, 'execute')['status'] == 'completed'
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';") == '1'
            # Persisted controller state has no key or capability; it records the approval digest.
            raw = state.read_text()
            assert self.key not in raw and self.approval_key not in raw and 'X-Booking-Approval' not in raw
            assert (state.stat().st_mode & 0o777) == 0o600
            cli(state, 'inspect', subject='agent-b', expected=2)
        self.case('agent_cli_approved_create_observe_replay_and_subject_binding', approved_create)

        def simultaneous_cli():
            state = plan('agent-concurrent-cli', 'create BOG-MDE 12500')
            proposal = approve(state)
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(lambda _: cli(state, 'execute'), range(2)))
            assert all(outcome['status'] == 'completed' for outcome in outcomes)
            oid = self.oid(proposal['plan']['request_key'])
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';") == '1'
            assert json.loads(state.read_text())['attempts'] == 1
        self.case('agent_cli_two_processes_same_state_one_attempt_one_charge', simultaneous_cli)

        def state_tampering():
            state = plan('agent-tamper', 'create BOG-MDE 12500')
            approve(state)
            before = self.scalar('SELECT count(*) FROM operations;')
            contents = json.loads(state.read_text())
            contents['plan']['action']['amount'] += 1
            state.write_text(json.dumps(contents))
            cli(state, 'execute', expected=2)
            assert self.scalar('SELECT count(*) FROM operations;') == before
        self.case('agent_cli_modified_approved_plan_is_rejected', state_tampering)

        def list_subject():
            own = cli(self.work/'agent-list.json', 'run', 'list')
            assert any(b['id'] == self.agent_booking_id for b in own['result']['body']['bookings'])
            other = cli(self.work/'agent-list-other.json', 'run', 'list', subject='agent-b')
            assert all(b['id'] != self.agent_booking_id for b in other['result']['body']['bookings'])
        self.case('agent_cli_read_only_tool_lists_only_authenticated_subject', list_subject)

        def provider_recovery():
            state = plan('agent-provider-retry', 'create BOG-MDE 12500')
            proposal = approve(state)
            oid = self.oid(proposal['plan']['request_key'])
            docker('stop', self.prefix+'-payments')
            try:
                assert cli(state, 'execute', expected=3)['status'] == 'pending'
                assert self.scalar("SELECT status FROM operations WHERE id='"+oid+"';") == 'NEW'
            finally:
                docker('start', self.prefix+'-payments')
            self.wait(lambda: docker('exec', self.prefix+'-payments', 'python', '-c',
                "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/ready')", check=False).returncode == 0)
            assert cli(state, 'execute')['status'] == 'completed'
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';") == '1'
        self.case('agent_cli_provider_outage_and_resume_from_persisted_plan', provider_recovery)

        def withdraw_after_send():
            state = plan('agent-withdraw-pending', 'create BOG-MDE 12500')
            proposal = approve(state)
            oid = self.oid(proposal['plan']['request_key'])
            docker('stop', self.prefix+'-payments')
            try:
                cli(state, 'execute', expected=3)
                withdrawn = cli(state, 'reject', expected=2)
                assert withdrawn['status'] == 'needs_approval'
                assert withdrawn['result']['remote_operation_may_continue'] is True
                cli(state, 'execute', expected=2)
            finally:
                docker('start', self.prefix+'-payments')
            self.wait(lambda: self.scalar("SELECT status FROM operations WHERE id='"+oid+"';") == 'CONFIRMED')
            approve(state)
            outcome = cli(state, 'execute')
            assert outcome['status'] == 'completed' and outcome['result']['reconciled'] is True
            assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';") == '1'
        self.case('agent_cli_withdraw_after_send_preserves_remote_reconciliation', withdraw_after_send)

        def ambiguous_capture():
            docker('stop', self.prefix+'-worker')
            state = plan('agent-ambiguous-capture', 'create BOG-MDE 12500')
            proposal = approve(state)
            oid = self.oid(proposal['plan']['request_key'])
            self.fault('crash_after_charge', oid)
            try:
                assert cli(state, 'execute', expected=3)['status'] == 'pending'
                self.wait(lambda: docker('inspect', '-f', '{{.State.Running}}', self.prefix+'-api-a').stdout.strip() == 'false')
                assert self.scalar("SELECT state||':'||captures FROM charges WHERE operation_id='"+oid+"';") == 'CAPTURED:1'
                self.fault('crash_after_charge', oid, False)
                docker('start', self.prefix+'-api-a')
                self.wait(self.refresh_ports)
                self.session_file()
                self.wait(lambda: self.req('GET', '/health/ready', port=self.port_a)[0] == 200)
                assert cli(state, 'execute')['status'] == 'completed'
                assert self.scalar("SELECT captures FROM charges WHERE operation_id='"+oid+"';") == '1'
                assert self.scalar("SELECT status FROM operations WHERE id='"+oid+"';") == 'CONFIRMED'
            finally:
                self.fault('crash_after_charge', oid, False)
                docker('start', self.prefix+'-worker')
        self.case('agent_cli_api_crash_after_capture_resume_no_double_charge', ambiguous_capture)

        def cancel_with_new_approval():
            oid = self.agent_booking_id
            route = '/bookings/'+oid
            assert self.req('DELETE', route, port=self.port_a, approval=False)[0] == 403
            state = plan('agent-cancel', 'cancel '+oid)
            cli(state, 'execute', expected=2)
            assert self.req('GET', route, port=self.port_b)[1]['status'] == 'CONFIRMED'
            approve(state)
            assert cli(state, 'execute')['status'] == 'completed'
            assert cli(state, 'execute')['status'] == 'completed'
            assert self.req('GET', route, port=self.port_b)[1]['status'] == 'CANCELLED'
            assert self.scalar("SELECT refunds FROM charges WHERE operation_id='"+oid+"';") == '1'
        self.case('agent_cli_cancel_requires_new_approval_and_refunds_once', cancel_with_new_approval)
        self.evidence['agent'] = {'planner': 'rules', 'live_bedrock_invoked': False,
                                  'transport': 'real CLI subprocesses and HTTP against PostgreSQL',
                                  'approval': 'explicit test-operator confirmation bound to request; enforced by API',
                                  'state': 'atomic private files, no keys or bearer tokens',
                                  'test_confirmation_is_human_identity_proof': False}

    def finish(self):
        """Stop every owned container and retain evidence; unknown is not stopped.

        Return False on cleanup/retention failures so callers can fail the run
        without replacing an earlier workload exception or its evidence.
        """
        cleanup = {'result': 'in_progress', 'containers': {}, 'errors': [],
                   'retained_for_review': ['containers', 'volumes', 'networks', 'private_files']}
        self.evidence['cleanup'] = cleanup

        def failure(operation, container=None, *, returncode=None, error=None):
            detail = {'operation': operation}
            if container is not None:
                detail['container'] = container
            if returncode is not None:
                detail['returncode'] = returncode
            if error is not None:
                # Exception messages and Docker stderr can contain private paths
                # or environment details. Only their type enters public evidence.
                detail['error_type'] = type(error).__name__
            cleanup['errors'].append(detail)

        def set_result():
            cleanup['result'] = 'failed' if cleanup['errors'] else 'passed'
            if cleanup['errors'] and self.evidence.get('result') != 'failed':
                self.evidence['result_before_cleanup'] = self.evidence.get('result')
                self.evidence['result'] = 'failed'
                self.evidence['failure_type'] = 'CleanupError'
                self.evidence['failure_detail'] = 'Cleanup or evidence retention could not be completed and verified'

        for container in self.containers:
            observed = cleanup['containers'][container] = {'running': None}
            try:
                log = docker('logs', container, check=False)
                observed['logs_returncode'] = log.returncode
                (self.work/(container+'.log')).write_text(log.stdout+log.stderr)
                if log.returncode:
                    failure('logs', container, returncode=log.returncode)
            except Exception as error:
                failure('retain_logs', container, error=error)
            try:
                stopped = docker('stop', container, check=False)
                observed['stop_returncode'] = stopped.returncode
                if stopped.returncode:
                    failure('stop', container, returncode=stopped.returncode)
            except Exception as error:
                failure('stop', container, error=error)

        # Inspect only after all stop attempts. A failed or malformed inspection
        # remains unknown, even if the corresponding stop command succeeded.
        for container, observed in cleanup['containers'].items():
            try:
                inspected = docker('inspect', '-f', '{{.State.Running}}', container, check=False)
                observed['inspect_returncode'] = inspected.returncode
                state = inspected.stdout.strip()
                if inspected.returncode:
                    failure('inspect', container, returncode=inspected.returncode)
                elif state not in ('true', 'false'):
                    failure('inspect_malformed', container)
                else:
                    observed['running'] = state == 'true'
                    if observed['running']:
                        failure('still_running', container)
            except Exception as error:
                failure('inspect', container, error=error)

        # Retain volumes, containers, dump and envs for review. No global prune/removal.
        states = [item['running'] for item in cleanup['containers'].values()]
        cleanup['all_stopped_verified'] = all(state is False for state in states)
        cleanup['known_running_count'] = sum(state is True for state in states)
        cleanup['unknown_count'] = sum(state is None for state in states)
        self.evidence['test_containers_running'] = (None if cleanup['unknown_count']
                                                    else cleanup['known_running_count'])
        self.evidence['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        set_result()

        try:
            (self.work/'review.json').write_text(json.dumps(
                {'prefix': self.prefix, 'ports': getattr(self, 'ports', []),
                 'evidence': str(self.output), 'private_evidence': str(self.work/'finish-evidence.json')},
                indent=2)+'\n')
        except Exception as error:
            failure('retain_review', error=error)
            set_result()

        def write_evidence(path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.evidence, indent=2, ensure_ascii=False)+'\n')

        try:
            write_evidence(self.output)
        except Exception as error:
            failure('write_public_evidence', error=error)
            set_result()
        try:
            # Also retain a private receipt when the selected output is unwritable.
            write_evidence(self.work/'finish-evidence.json')
        except Exception as error:
            failure('write_private_evidence', error=error)
            set_result()
            # An earlier public receipt must not remain marked passed after a
            # retention failure. Best effort; the caller still exits nonzero.
            try:
                write_evidence(self.output)
            except Exception:
                pass
        print('Evidence: '+str(self.output),flush=True)
        print('Private review files retained in '+str(self.work),flush=True)
        return cleanup['result'] == 'passed'


def main():
    if not __debug__:
        raise SystemExit('Run without -O: E2E assertions must remain enabled')
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=['e2e','demo'])
    ap.add_argument('--output')
    args=ap.parse_args()
    lab=Lab(args.output or ('.local/demo.json' if args.command == 'demo' else '.local/db-e2e.json'))
    try:
        lab.setup()
        if args.command == 'e2e':
            lab.run_tests()
        else:
            lab.start('worker','worker','booking_app',audit=True)
            session=lab.session_file()
            lab.evidence['result']='demo_running'
            print('DEMO_READY session='+str(session),flush=True)
            print('Use client.py --session <path> list/create/cancel. Ctrl+C stops only this lab.',flush=True)
            def stop(*_):
                raise KeyboardInterrupt()
            signal.signal(signal.SIGTERM,stop)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                lab.evidence['result']='demo_stopped'

    except BaseException as e:
        lab.evidence['result']='failed'
        lab.evidence['failure_type']=type(e).__name__
        print('FAILED: '+str(e),file=sys.stderr,flush=True)
        raise
    finally:
        cleanup_ok = lab.finish()
        if not cleanup_ok and sys.exc_info()[0] is None:
            raise SystemExit(1)


if __name__=='__main__':
    main()
