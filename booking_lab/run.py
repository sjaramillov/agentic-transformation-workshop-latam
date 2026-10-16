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
import subprocess
import sys
import time
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from auth import encode

ROOT = Path(__file__).resolve().parent
IMAGES = json.loads((ROOT/'images.lock.json').read_text())
PG_IMAGE, PY_IMAGE = IMAGES['postgres'], IMAGES['python']


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
        self.tokens = {n: encode(self.key,n) for n in ('agent-a','agent-b')}
        self.containers = []
        self.passwords = {n:secrets.token_hex(24) for n in ('postgres','booking_app','payment_app','audit_writer','audit_reader')}
        self.pay_token = secrets.token_hex(32)
        self.tests = []
        self.resource_options = []
        self.evidence = {'schema_version':1, 'started_at_utc':datetime.now(timezone.utc).isoformat(),
                         'implementation':'original MIT booking_lab', 'environment':os.environ.get('LAB_EVIDENCE_ENV','local Docker'),
                         'payments':'synthetic HTTP provider backed by PostgreSQL; no money moved',
                         'aws_managed_ara_rerun':False,'cases':self.tests}

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
            values.update(JWT_KEY=self.key,LAB_FAULTS='1')
        if audit:
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

    def req(self, method, path='/bookings', payload=None, key=None, principal='agent-a', token=None, port=18881, correlation=None):
        headers={'Authorization':'Bearer '+(self.tokens[principal] if token is None else token)}
        if key is not None:
            headers['Idempotency-Key']=key
        if correlation:
            headers['X-Correlation-ID']=correlation
        raw=None
        if payload is not None:
            raw=json.dumps(payload).encode();headers['Content-Type']='application/json'
        req=Request(f'http://127.0.0.1:{port}'+path,data=raw,headers=headers,method=method)
        try:
            with urlopen(req,timeout=12) as r:
                return r.status,json.load(r)
        except HTTPError as e:
            return e.code,json.load(e)

    def case(self, name, fn):
        start=time.monotonic()
        fn()
        self.tests.append({'name':name,'result':'passed','duration_seconds':round(time.monotonic()-start,3)})
        print('PASS '+name,flush=True)

    def setup(self):
        info=json.loads(docker('info','--format','{{json .}}').stdout)
        self.evidence['resource_limits_available']=all(info.get(k,False) for k in ('MemoryLimit','CPUCfsQuota','PidsLimit'))
        if self.evidence['resource_limits_available']:
            self.resource_options=['--memory','256m','--cpus','1','--pids-limit','128']
        else:
            print('Host does not support cgroup limits; retaining network, filesystem and capability isolation',flush=True)
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
        self.start('payments','payments','payment_app')
        # Ephemeral host ports are discovered from Docker, avoiding collisions with user services.
        self.ports=[]
        for name in ('api-a','api-b'):
            self.start(name,'api','booking_app',port=0)
        self.wait(self.refresh_ports)
        self.wait(lambda: self.req('GET','/health/ready',port=self.port_a)[0]==200)
        self.wait(lambda: self.req('GET','/health/ready',port=self.port_b)[0]==200)
        self.tokens={n:encode(self.key,n) for n in ('agent-a','agent-b')}

    def run_tests(self):
        p={'itinerary':'BOG-MDE','amount':12500}
        def auth():
            for token in ('',encode(self.key,exp=0),encode(self.key,aud='wrong'),encode(self.key,iss='wrong'),encode(self.key,nbf=9999999999),encode('x'*64)):
                assert self.req('POST',payload=p,key='auth',token=token,port=self.port_a)[0]==401
            assert self.req('POST',payload=p,key='auth',token=encode(self.key,scope='bookings:read'),port=self.port_a)[0]==403
            assert self.scalar('SELECT count(*) FROM charges;')=='0'
        self.case('authentication_issuer_audience_expiry_signature_scope',auth)
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
        def dump_restore():
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
        self.case('actual_pg_dump_restore_into_separate_database',dump_restore)
        self.wait(lambda:self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;')=='0')
        self.evidence['invariants']={
          'captured_without_confirmed_booking':int(self.scalar("SELECT count(*) FROM charges c LEFT JOIN bookings b ON b.id=c.operation_id AND b.status='CONFIRMED' WHERE c.state='CAPTURED' AND b.id IS NULL;")),
          'confirmed_without_captured_payment':int(self.scalar("SELECT count(*) FROM bookings b LEFT JOIN charges c ON c.operation_id=b.id AND c.state='CAPTURED' WHERE b.status='CONFIRMED' AND c.operation_id IS NULL;")),
          'pending_operations':int(self.scalar("SELECT count(*) FROM operations WHERE status IN ('NEW','CHARGED','COMPENSATING','CANCELLING');")),
          'undelivered_audit_events':int(self.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;')),
          'audit_missing_attribution':int(self.scalar("SELECT count(*) FROM audit_events WHERE principal='' OR correlation_id IS NULL OR operation_id='';"))}
        assert all(v==0 for v in self.evidence['invariants'].values()),self.evidence['invariants']
        self.evidence['audit_event_count']=int(self.scalar('SELECT count(*) FROM audit_events;'))
        self.evidence['result']='passed'

    def finish(self):
        for container in self.containers:
            log=docker('logs',container,check=False)
            (self.work/(container+'.log')).write_text(log.stdout+log.stderr)
            docker('stop',container,check=False)
        # Retain volumes, containers, dump and envs for review. No global prune/removal.
        self.evidence['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        self.evidence['test_containers_running']=sum(docker('inspect','-f','{{.State.Running}}',c,check=False).stdout.strip()=='true' for c in self.containers)
        self.output.parent.mkdir(parents=True,exist_ok=True)
        self.output.write_text(json.dumps(self.evidence,indent=2,ensure_ascii=False)+'\n')
        (self.work/'review.json').write_text(json.dumps({'prefix':self.prefix,'ports':getattr(self,'ports',[]),'evidence':str(self.output)},indent=2)+'\n')
        print('Evidence: '+str(self.output),flush=True)
        print('Private review files retained in '+str(self.work),flush=True)


def main():
    if not __debug__:
        raise SystemExit('Run without -O: E2E assertions must remain enabled')
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=['e2e'])
    ap.add_argument('--output',default='.local/db-e2e.json')
    args=ap.parse_args()
    lab=Lab(args.output)
    try:
        lab.setup();lab.run_tests()
    except BaseException as e:
        lab.evidence['result']='failed'
        lab.evidence['failure_type']=type(e).__name__
        print('FAILED: '+str(e),file=sys.stderr,flush=True)
        raise
    finally:
        lab.finish()


if __name__=='__main__':
    main()
