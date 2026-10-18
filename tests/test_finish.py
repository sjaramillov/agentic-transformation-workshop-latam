"""Cleanup failures cannot turn into a successful E2E receipt or exit status."""
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'booking_lab'))
import run as runner
import bedrock_e2e


class DockerFinishFixture:
    def __init__(self, containers, *, stop_failure=None, inspect_failure=None,
                 malformed=None, exception=None):
        self.running = dict.fromkeys(containers, True)
        self.stop_failure, self.inspect_failure = stop_failure, inspect_failure
        self.malformed, self.exception = malformed, exception
        self.events = []

    def __call__(self, *args, **kwargs):
        operation, container = args[0], args[-1]
        self.events.append((operation, container))
        if self.exception == (operation, container):
            raise OSError('private transport detail')
        code, output, error = 0, '', ''
        if operation == 'logs':
            output, error = 'private stdout\n', 'private stderr\n'
        elif operation == 'stop':
            if container == self.stop_failure:
                code, error = 1, 'private stop detail'
            else:
                self.running[container] = False
        elif operation == 'inspect':
            output = str(self.running[container]).lower()
            if container == self.inspect_failure:
                code, output = 1, 'false'  # Even plausible stdout is not proof.
            elif container == self.malformed:
                output = '<no value>'
        else:
            raise AssertionError(operation)
        return SimpleNamespace(returncode=code, stdout=output, stderr=error)


class FinishTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.lab = object.__new__(runner.Lab)
        self.lab.prefix = 'db-lab-123456789a'
        self.lab.containers = [self.lab.prefix+'-'+role for role in ('api-a', 'worker', 'db')]
        self.lab.work = Path(temporary.name)/'private'
        self.lab.work.mkdir(mode=0o700)
        self.lab.output = Path(temporary.name)/'public'/'evidence.json'
        self.lab.evidence = {'result': 'passed', 'cases': [{'name': 'fixture', 'result': 'passed'}]}

    def finish(self, fixture):
        with patch.object(runner, 'docker', side_effect=fixture), patch('sys.stdout', new_callable=io.StringIO):
            return self.lab.finish()

    def assert_all_stops_attempted(self, fixture):
        self.assertEqual([container for op, container in fixture.events if op == 'stop'], self.lab.containers)

    def test_success_requires_every_container_inspected_after_all_stops(self):
        fixture = DockerFinishFixture(self.lab.containers)
        self.assertTrue(self.finish(fixture))
        self.assert_all_stops_attempted(fixture)
        first_inspect = next(i for i, event in enumerate(fixture.events) if event[0] == 'inspect')
        self.assertTrue(all(op != 'stop' for op, _ in fixture.events[first_inspect:]))
        self.assertEqual(self.lab.evidence['test_containers_running'], 0)
        self.assertTrue(self.lab.evidence['cleanup']['all_stopped_verified'])
        self.assertEqual(self.lab.evidence['cleanup']['unknown_count'], 0)
        self.assertEqual(self.lab.evidence['result'], 'passed')
        self.assertEqual(json.loads(self.lab.output.read_text()),
                         json.loads((self.lab.work/'finish-evidence.json').read_text()))
        for container in self.lab.containers:
            self.assertEqual((self.lab.work/(container+'.log')).read_text(), 'private stdout\nprivate stderr\n')
        self.assertNotIn('private stderr', self.lab.output.read_text())

    def test_failed_stop_is_recorded_and_remaining_containers_are_stopped(self):
        fixture = DockerFinishFixture(self.lab.containers, stop_failure=self.lab.containers[0])
        self.assertFalse(self.finish(fixture))
        self.assert_all_stops_attempted(fixture)
        self.assertEqual(self.lab.evidence['test_containers_running'], 1)
        self.assertFalse(self.lab.evidence['cleanup']['all_stopped_verified'])
        self.assertEqual(self.lab.evidence['result'], 'failed')
        self.assertEqual(self.lab.evidence['result_before_cleanup'], 'passed')
        self.assertEqual(self.lab.evidence['failure_type'], 'CleanupError')
        self.assertNotIn('private stop detail', self.lab.output.read_text())

    def test_failed_inspection_is_unknown_even_when_stdout_says_false(self):
        fixture = DockerFinishFixture(self.lab.containers, inspect_failure=self.lab.containers[1])
        self.assertFalse(self.finish(fixture))
        self.assertIsNone(self.lab.evidence['test_containers_running'])
        self.assertEqual(self.lab.evidence['cleanup']['unknown_count'], 1)
        self.assertFalse(self.lab.evidence['cleanup']['all_stopped_verified'])
        self.assertIsNone(self.lab.evidence['cleanup']['containers'][self.lab.containers[1]]['running'])

    def test_malformed_inspection_is_unknown(self):
        fixture = DockerFinishFixture(self.lab.containers, malformed=self.lab.containers[2])
        self.assertFalse(self.finish(fixture))
        self.assertIsNone(self.lab.evidence['test_containers_running'])
        self.assertEqual(self.lab.evidence['cleanup']['errors'][0]['operation'], 'inspect_malformed')

    def test_transport_exceptions_do_not_skip_later_stop_attempts_or_expose_details(self):
        for operation in ('logs', 'stop', 'inspect'):
            with self.subTest(operation=operation):
                fixture = DockerFinishFixture(self.lab.containers, exception=(operation, self.lab.containers[0]))
                self.assertFalse(self.finish(fixture))
                self.assert_all_stops_attempted(fixture)
                self.assertFalse(fixture.running[self.lab.containers[-1]])
                self.assertNotIn('private transport detail', self.lab.output.read_text())

    def test_log_file_failure_still_stops_and_inspects_every_container(self):
        original = Path.write_text
        def write(path, *args, **kwargs):
            if path.suffix == '.log':
                raise OSError('private disk detail')
            return original(path, *args, **kwargs)
        fixture = DockerFinishFixture(self.lab.containers)
        with patch.object(Path, 'write_text', new=write):
            self.assertFalse(self.finish(fixture))
        self.assert_all_stops_attempted(fixture)
        self.assertTrue(self.lab.evidence['cleanup']['all_stopped_verified'])
        self.assertEqual(self.lab.evidence['result'], 'failed')
        self.assertNotIn('private disk detail', self.lab.output.read_text())

    def test_existing_workload_failure_survives_cleanup_failure(self):
        self.lab.evidence.update(result='failed', failure_type='AssertionError', failure_detail='fixture mismatch')
        fixture = DockerFinishFixture(self.lab.containers, inspect_failure=self.lab.containers[0])
        self.assertFalse(self.finish(fixture))
        saved = json.loads(self.lab.output.read_text())
        self.assertEqual(saved['failure_type'], 'AssertionError')
        self.assertEqual(saved['failure_detail'], 'fixture mismatch')
        self.assertEqual(saved['cleanup']['result'], 'failed')

    def test_unwritable_output_preserves_failed_receipt_in_private_directory(self):
        self.lab.output.mkdir(parents=True)
        self.assertFalse(self.finish(DockerFinishFixture(self.lab.containers)))
        saved = json.loads((self.lab.work/'finish-evidence.json').read_text())
        self.assertEqual(saved['result'], 'failed')
        self.assertEqual(saved['cleanup']['errors'][-1]['operation'], 'write_public_evidence')

    def test_private_receipt_failure_updates_public_receipt_to_failed(self):
        original = Path.write_text
        def write(path, *args, **kwargs):
            if path.name == 'finish-evidence.json':
                raise OSError('private disk detail')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'write_text', new=write):
            self.assertFalse(self.finish(DockerFinishFixture(self.lab.containers)))
        saved = json.loads(self.lab.output.read_text())
        self.assertEqual(saved['result'], 'failed')
        self.assertEqual(saved['cleanup']['errors'][-1]['operation'], 'write_private_evidence')

    def test_no_registered_containers_is_verified_without_docker_actions(self):
        self.lab.containers = []
        fixture = DockerFinishFixture([])
        self.assertTrue(self.finish(fixture))
        self.assertEqual(fixture.events, [])
        self.assertEqual(self.lab.evidence['test_containers_running'], 0)

    def test_standard_runner_exits_nonzero_after_workload_passes_but_cleanup_fails(self):
        self.lab.setup, self.lab.run_tests = Mock(), Mock()
        fixture = DockerFinishFixture(self.lab.containers, inspect_failure=self.lab.containers[0])
        with patch.object(runner, 'Lab', return_value=self.lab), patch.object(runner, 'docker', side_effect=fixture), \
                patch.object(sys, 'argv', ['run.py', 'e2e']), patch('sys.stdout', new_callable=io.StringIO), \
                self.assertRaises(SystemExit) as error:
            runner.main()
        self.assertEqual(error.exception.code, 1)
        self.assertEqual(json.loads(self.lab.output.read_text())['result'], 'failed')

    def test_standard_runner_preserves_original_exception_when_cleanup_also_fails(self):
        failure = AssertionError('primary workload failure')
        self.lab.setup, self.lab.run_tests = Mock(), Mock(side_effect=failure)
        fixture = DockerFinishFixture(self.lab.containers, stop_failure=self.lab.containers[0])
        with patch.object(runner, 'Lab', return_value=self.lab), patch.object(runner, 'docker', side_effect=fixture), \
                patch.object(sys, 'argv', ['run.py', 'e2e']), patch('sys.stdout', new_callable=io.StringIO), \
                patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(AssertionError) as error:
            runner.main()
        self.assertIs(error.exception, failure)
        self.assertEqual(self.lab.evidence['failure_type'], 'AssertionError')

    def test_live_runner_exits_nonzero_for_cleanup_failure_and_preserves_primary_failure(self):
        for primary_failure in (None, AssertionError('model fixture mismatch')):
            with self.subTest(primary_failure=primary_failure):
                self.lab.evidence = {'result': 'passed'}
                self.lab.setup, self.lab.start = Mock(), Mock()
                scenario = Mock()
                scenario.run.side_effect = primary_failure
                fixture = DockerFinishFixture(self.lab.containers, inspect_failure=self.lab.containers[0])
                chosen_output = self.lab.work/'unused-output.json'
                with patch.object(bedrock_e2e, 'Lab', return_value=self.lab), \
                        patch.object(bedrock_e2e, 'LiveBedrockScenario', return_value=scenario), \
                        patch.object(runner, 'docker', side_effect=fixture), \
                        patch('sys.stdout', new_callable=io.StringIO), patch('sys.stderr', new_callable=io.StringIO):
                    code = bedrock_e2e.main(['--live-bedrock', '--confirm-test-operator', '--model-id', 'fixture-model',
                                             '--region', 'us-east-1', '--output', str(chosen_output)])
                self.assertEqual(code, 1)
                self.assertEqual(self.lab.evidence['result'], 'failed')
                if primary_failure:
                    self.assertEqual(self.lab.evidence['failure_type'], 'AssertionError')
                    self.assertEqual(self.lab.evidence['failure_detail'], 'model fixture mismatch')
                else:
                    self.assertEqual(self.lab.evidence['failure_type'], 'CleanupError')


if __name__ == '__main__':
    unittest.main()
