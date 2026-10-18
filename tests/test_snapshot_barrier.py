"""Exercise the real restore helper with controlled Docker/SQL transport."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'booking_lab'))
spec = importlib.util.spec_from_file_location('snapshot_lab_runner', ROOT / 'booking_lab/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DockerFixture:
    def __init__(self, queues, ignored_stop=None, restart_ingress=False, corrupt_restore=False):
        self.queues = list(queues)
        self.running = dict.fromkeys(('api-a', 'api-b', 'worker', 'payments', 'db', 'audit'), True)
        self.ignored_stop = ignored_stop
        self.restart_ingress = restart_ingress
        self.corrupt_restore = corrupt_restore
        self.events = []
        self.prefix = 'db-lab-123456789a-'

    def __call__(self, *args, data=None, check=True):
        stdout = ''
        if args[0] == 'stop':
            for container in args[1:]:
                role = container.removeprefix(self.prefix)
                self.events.append(('stop', role))
                if role != self.ignored_stop:
                    self.running[role] = False
                if role == 'payments' and self.restart_ingress:
                    self.running['api-a'] = True
        elif args[0] == 'inspect':
            role = args[-1].removeprefix(self.prefix)
            self.events.append(('inspect', role))
            stdout = str(self.running[role]).lower()
        elif args[0] == 'exec' and 'pg_dump' in args:
            self.events.append(('dump', dict(self.running)))
            stdout = '-- fixture snapshot\n'
        elif args[0] == 'exec' and 'psql' in args:
            query = data if data is not None else args[-1]
            if 'SELECT (SELECT count(*) FROM operations WHERE status IN' in query:
                counts = self.queues[0]
                if len(self.queues) > 1:
                    self.queues.pop(0)
                self.events.append(('queue', counts, dict(self.running)))
                stdout = '|'.join(map(str, counts))
            elif query.startswith('SELECT (SELECT count(*) FROM bookings)'):
                stdout = '12|15|50' if self.corrupt_restore and 'restore_check' in args else '12|15|52'
            elif query.startswith('SELECT md5('):
                stdout = hashlib.md5(query.encode()).hexdigest()
            else:
                self.events.append(('sql', query))
        else:
            raise AssertionError(('Unexpected fixture call', args))
        return SimpleNamespace(returncode=0, stdout=stdout, stderr='')


class SnapshotBarrierTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.lab = object.__new__(runner.Lab)
        self.lab.prefix = 'db-lab-123456789a'
        self.lab.containers = [self.lab.prefix+'-'+role for role in ('api-a', 'api-b', 'worker', 'payments', 'db', 'audit')]
        self.lab.work = Path(temporary.name)
        self.lab.evidence = {}
        # Bound the test clock without replacing the predicate or restore helper.
        def fast_wait(predicate, timeout):
            self.assertEqual(timeout, 60)
            for _ in range(4):
                if predicate():
                    return
            raise AssertionError('fixture drain timeout')
        self.lab.wait = fast_wait

    def test_delayed_queue_drains_before_background_stop_and_dump(self):
        fixture = DockerFixture([(1, 2), (0, 2), (0, 0), (0, 0)])
        with patch.object(runner, 'docker', side_effect=fixture):
            self.lab.verify_database_restore()
        stop_roles = [event[1] for event in fixture.events if event[0] == 'stop']
        self.assertEqual(stop_roles, ['api-a', 'api-b', 'worker', 'payments'])
        reads = [event for event in fixture.events if event[0] == 'queue']
        self.assertEqual([event[1] for event in reads], [(1, 2), (0, 2), (0, 0), (0, 0)])
        for _, _, active in reads[:3]:
            self.assertFalse(active['api-a'])
            self.assertFalse(active['api-b'])
            self.assertTrue(active['worker'])
            self.assertTrue(active['payments'])
        dump = next(event for event in fixture.events if event[0] == 'dump')
        self.assertFalse(any(dump[1][role] for role in ('api-a', 'api-b', 'worker', 'payments')))
        self.assertTrue(dump[1]['db'])
        self.assertTrue(dump[1]['audit'])
        barrier = self.lab.evidence['snapshot_barrier']
        self.assertEqual(barrier['result'], 'passed')
        self.assertEqual(barrier['drain_polls'], 3)
        self.assertEqual(barrier['final_queue_counts'], {'pending_operations': 0, 'undelivered_audit_events': 0})
        self.assertEqual(self.lab.evidence['restore_counts_bookings_charges_audit'], '12|15|52')
        self.assertEqual(len(self.lab.evidence['restored_table_row_hashes']), 6)

    def test_persistent_queue_blocks_dump_and_keeps_recovery_available(self):
        fixture = DockerFixture([(0, 2)])
        with patch.object(runner, 'docker', side_effect=fixture), self.assertRaisesRegex(AssertionError, 'timeout'):
            self.lab.verify_database_restore()
        self.assertEqual(self.lab.evidence['snapshot_barrier']['result'], 'failed')
        self.assertEqual(self.lab.evidence['snapshot_barrier']['phase'], 'drain_recovery_and_audit')
        self.assertTrue(fixture.running['worker'])
        self.assertTrue(fixture.running['payments'])
        self.assertFalse(any(event[0] == 'dump' for event in fixture.events))

    def test_writer_that_does_not_stop_blocks_dump(self):
        for role in ('api-a', 'api-b', 'worker', 'payments'):
            with self.subTest(role=role):
                fixture = DockerFixture([(0, 0)], ignored_stop=role)
                with patch.object(runner, 'docker', side_effect=fixture), self.assertRaisesRegex(AssertionError, 'still running'):
                    self.lab.verify_database_restore()
                self.assertEqual(self.lab.evidence['snapshot_barrier']['result'], 'failed')
                self.assertFalse(any(event[0] == 'dump' for event in fixture.events))

    def test_queue_reappearing_after_stop_blocks_dump(self):
        fixture = DockerFixture([(0, 0), (0, 1)])
        with patch.object(runner, 'docker', side_effect=fixture), self.assertRaisesRegex(AssertionError, 'not quiescent'):
            self.lab.verify_database_restore()
        self.assertEqual(self.lab.evidence['snapshot_barrier']['final_queue_counts']['undelivered_audit_events'], 1)
        self.assertFalse(any(event[0] == 'dump' for event in fixture.events))

    def test_ingress_restarted_during_worker_stop_blocks_dump(self):
        fixture = DockerFixture([(0, 0)], restart_ingress=True)
        with patch.object(runner, 'docker', side_effect=fixture), self.assertRaisesRegex(AssertionError, 'restarted'):
            self.lab.verify_database_restore()
        self.assertTrue(self.lab.evidence['snapshot_barrier']['writers_running_before_dump']['api-a'])
        self.assertFalse(any(event[0] == 'dump' for event in fixture.events))

    def test_unregistered_container_is_not_stopped(self):
        fixture = DockerFixture([(0, 0)])
        self.lab.containers.remove(self.lab.prefix+'-payments')
        with patch.object(runner, 'docker', side_effect=fixture), self.assertRaisesRegex(AssertionError, 'registered'):
            self.lab.verify_database_restore()
        self.assertEqual(fixture.events, [])

    def test_restore_row_mismatch_still_fails_after_valid_barrier(self):
        fixture = DockerFixture([(0, 0)], corrupt_restore=True)
        with patch.object(runner, 'docker', side_effect=fixture), self.assertRaises(AssertionError):
            self.lab.verify_database_restore()
        self.assertEqual(self.lab.evidence['snapshot_barrier']['result'], 'passed')
        self.assertNotIn('restored_table_row_hashes', self.lab.evidence)


if __name__ == '__main__':
    unittest.main()
