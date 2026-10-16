"""Independent ledger integrity/retention checks using real SQLite."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('audit',Path(__file__).resolve().parents[1]/'booking_lab/audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'AUDIT_PATH':self.temp.name+'/ledger.sqlite','AUDIT_SIGNING_KEY':'k'*64,'AUDIT_WRITE_TOKEN':'w'*64,'AUDIT_READ_TOKEN':'r'*64})
        self.env.start();audit.initialize()
        self.event=dict(id='event-1',operation_id='operation-1',principal='agent-a',correlation_id='correlation-1',event_type='booking.confirmed',created_at='2026-10-16T00:00:00+00:00')

    def tearDown(self):
        self.env.stop();self.temp.cleanup()

    def test_replay_conflict_and_retention(self):
        r=audit.append(self.event)
        self.assertEqual(audit.append(self.event),r)
        self.assertGreater(r['retain_until'],audit.time.time()+89*86400)
        with self.assertRaises(ValueError):audit.append({**self.event,'principal':'forged'})
        self.assertEqual((Path(self.temp.name)/'ledger.sqlite').stat().st_mode & 0o777,0o600)

    def test_chain_signature_and_external_checkpoint(self):
        records=[audit.append(self.event),audit.append({**self.event,'id':'event-2'})]
        anchor={'sequence':2,'digest':records[-1]['digest']}
        self.assertTrue(audit.verify(records,'k'*64,anchor))
        for tampered in (records[:-1],list(reversed(records)),json.loads(json.dumps(records))):
            if tampered==records:tampered[0]['event']['principal']='forged'
            with self.assertRaises(ValueError):audit.verify(tampered,'k'*64,anchor)
        with self.assertRaises(ValueError):audit.verify(records,'x'*64,anchor)

    def test_updates_and_deletes_denied(self):
        audit.append(self.event)
        for sql in ('DELETE FROM ledger','UPDATE ledger SET record=record'):
            with self.assertRaises(sqlite3.IntegrityError),audit.connect() as c:c.execute(sql)

    def test_invalid_event_is_rejected(self):
        for event in ({},None,{**self.event,'principal':42},{**self.event,'id':''}):
            with self.assertRaises(ValueError):audit.append(event)

    def test_runtime_build_includes_ledger_module(self):
        root=Path(__file__).resolve().parents[1]/'booking_lab'
        allowed={line[1:] for line in (root/'.dockerignore').read_text().splitlines() if line.startswith('!')}
        for line in (root/'Dockerfile').read_text().splitlines():
            if line.startswith('COPY '):
                for source in line.split()[1:-1]:
                    self.assertIn(source,allowed)
                    self.assertTrue((root/source).is_file())
