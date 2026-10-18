"""Offline control-contract checks; PostgreSQL HTTP E2E runs in the lab runner."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from urllib.request import HTTPHandler, build_opener
from urllib.response import addinfourl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'booking_lab'))
import agent
import approval


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.key = 'approval-' + 'a' * 64
        self.payload = {'itinerary': 'BOG-MDE', 'amount': 12500}

    def issue(self, **kwargs):
        return approval.issue(self.key, 'agent-a', 'POST', '/bookings', self.payload, 'same-key', now=100, **kwargs)

    def test_valid_request_bound_capability_and_cancellation(self):
        token = self.issue()
        self.assertTrue(approval.verify(token, self.key, 'agent-a', 'POST', '/bookings',
                                        dict(reversed(list(self.payload.items()))), 'same-key', now=101))
        cancel = approval.issue(self.key, 'agent-a', 'DELETE', '/bookings/' + 'a' * 64, now=100)
        self.assertTrue(approval.verify(cancel, self.key, 'agent-a', 'DELETE', '/bookings/' + 'a' * 64, now=101))
        self.assertFalse(approval.verify(cancel, self.key, 'agent-a', 'DELETE', '/bookings/' + 'b' * 64, now=101))

    def test_expired_and_future_capabilities_rejected(self):
        token = self.issue()
        self.assertFalse(approval.verify(token, self.key, 'agent-a', 'POST', '/bookings', self.payload, 'same-key', now=99))
        self.assertTrue(approval.verify(token, self.key, 'agent-a', 'POST', '/bookings', self.payload, 'same-key', now=399))
        self.assertFalse(approval.verify(token, self.key, 'agent-a', 'POST', '/bookings', self.payload, 'same-key', now=400))
        for ttl in (0, -1, 301, True, 2.5):
            with self.subTest(ttl=ttl), self.assertRaises(ValueError):
                self.issue(ttl=ttl)

    def test_token_cannot_authorize_changed_request(self):
        token = self.issue()
        attempts = [('agent-b', 'POST', '/bookings', self.payload, 'same-key'),
                    ('agent-a', 'POST', '/bookings', {**self.payload, 'amount': 12501}, 'same-key'),
                    ('agent-a', 'POST', '/bookings', self.payload, 'different-key'),
                    ('agent-a', 'DELETE', '/bookings/' + 'a' * 64, None, '')]
        for args in attempts:
            with self.subTest(args=args):
                self.assertFalse(approval.verify(token, self.key, *args, now=101))
        for bad in ('', 'bad.token', token[:-1] + ('0' if token[-1] != '0' else '1'), 'a' * 5000):
            self.assertFalse(approval.verify(bad, self.key, 'agent-a', 'POST', '/bookings', self.payload, 'same-key', now=101))
        self.assertFalse(approval.verify(token, 'other-key-' * 5, 'agent-a', 'POST', '/bookings', self.payload, 'same-key', now=101))
        self.assertFalse(approval.verify(token, 'short', 'agent-a', 'POST', '/bookings', self.payload, 'same-key', now=101))

    def test_unknown_scope_and_invalid_payload_cannot_be_issued(self):
        for method, path, payload, key in [('GET', '/bookings', None, ''),
                                           ('POST', '/bookings', {**self.payload, 'amount': True}, 'x'),
                                           ('POST', '/bookings', {**self.payload, 'scope': '*'}, 'x'),
                                           ('DELETE', '/bookings/' + 'a' * 64, None, 'key')]:
            with self.subTest(method=method, payload=payload), self.assertRaises(ValueError):
                approval.issue(self.key, 'agent-a', method, path, payload, key, now=100)


class PlannerTests(unittest.TestCase):
    def test_exact_rule_grammar(self):
        self.assertEqual(agent.rules_plan('list'), {'action': 'list'})
        self.assertEqual(agent.rules_plan('reservar BOG-MDE 12500'), {'action': 'create', 'itinerary': 'BOG-MDE', 'amount': 12500})
        self.assertEqual(agent.rules_plan('cancelar ' + 'a' * 64), {'action': 'cancel', 'booking_id': 'a' * 64})
        for goal in ('', 'create BOG-MDE 0', 'create bog-mde 10', 'create BOG-MDE 1; rm -rf /',
                     'create BOG-MDE 10000001', 'create BOG-MDE 12.5', 'delete everything', 'cancel ../a', 'x' * 4097):
            with self.subTest(goal=goal), self.assertRaises(agent.AgentError):
                agent.rules_plan(goal)

    def response(self, text, **changes):
        envelope = {'stopReason': 'end_turn', 'output': {'message': {'role': 'assistant', 'content': [{'text': text}]}}}
        envelope.update(changes)
        return subprocess.CompletedProcess([], 0, json.dumps(envelope), '')

    def test_bedrock_proposes_allowlisted_action_without_session_secrets(self):
        runner = Mock(return_value=self.response('{"action":"create","itinerary":"BOG-MDE","amount":12500}'))
        self.assertEqual(agent.bedrock_plan('Reservar BOG-MDE por 12500', 'chosen-model', 'us-east-1', runner)['action'], 'create')
        args, kwargs = runner.call_args
        command = args[0]
        self.assertEqual(command[:3], ['aws', 'bedrock-runtime', 'converse'])
        self.assertNotIn('shell', kwargs)
        self.assertNotIn('session', ' '.join(command).lower())
        self.assertNotIn('Bearer', ' '.join(command))

    def test_model_output_cannot_choose_endpoint_authorization_or_many_actions(self):
        bad = ['{"action":"list","url":"https://attacker.test"}',
               '{"action":"create","itinerary":"BOG-MDE","amount":true}',
               '{"action":"create","itinerary":"BOG-MDE","amount":NaN}',
               '{"action":"list","approved":true}', '{"action":"unsupported"}',
               '[{"action":"list"}]', '```json\n{"action":"list"}\n```',
               '{"action":"list","action":"create"}']
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(agent.AgentError):
                agent.bedrock_plan('goal', 'model', runner=Mock(return_value=self.response(raw)))

    def test_bedrock_errors_fail_closed_without_rules_fallback(self):
        for runner in (Mock(return_value=subprocess.CompletedProcess([], 1, '', 'private account details')),
                       Mock(side_effect=subprocess.TimeoutExpired('aws', 90)),
                       Mock(return_value=self.response('{"action":"list"}', stopReason='max_tokens'))):
            with self.assertRaises(agent.AgentError):
                agent.bedrock_plan('list', 'model', runner=runner)
        with self.assertRaises(agent.AgentError):
            agent.bedrock_plan('list', None)
        for envelope in ('[]', 'null', 'true', '"text"'):
            with self.subTest(envelope=envelope), self.assertRaises(agent.AgentError):
                agent.bedrock_plan('list', 'model', runner=Mock(return_value=subprocess.CompletedProcess([], 0, envelope, '')))


class AgentStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'intent.json'
        self.session = {'prefix': 'db-lab-123456789a', 'port': 12345,
                        'key': 'jwt-' + 'j' * 64, 'approval_key': 'approval-' + 'a' * 64}

    def propose(self, goal='create BOG-MDE 12500'):
        return agent.propose(self.path, self.session, 'agent-a', goal, now=100)

    def approve(self, state):
        return agent.approve(self.path, self.session, 'agent-a', 'APROBAR ' + state['plan_digest'], now=100)

    def saved(self):
        return agent.load_state(self.path, self.session, 'agent-a')

    def observed(self, state, status='CONFIRMED'):
        key = state['plan']['request_key']
        oid = hashlib.sha256(('POST /bookings\0agent-a\0' + key).encode()).hexdigest()
        return {'id': oid, 'itinerary': 'BOG-MDE', 'amount': 12500, 'status': status}

    def test_plan_does_not_make_network_call_and_is_private_sealed_without_secrets(self):
        with patch.object(agent, 'request', side_effect=AssertionError('must not call')):
            state = self.propose()
        self.assertEqual(state['status'], 'proposed')
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        raw = self.path.read_text()
        self.assertNotIn(self.session['key'], raw)
        self.assertNotIn(self.session['approval_key'], raw)
        self.assertNotIn('Bearer', raw)
        self.assertEqual(self.saved()['plan_digest'], state['plan_digest'])
        with self.assertRaisesRegex(agent.AgentError, 'already exists'):
            self.propose()

    def test_no_approval_and_rejection_never_make_network_write(self):
        state = self.propose()
        transport = Mock(side_effect=AssertionError('must not call'))
        pending = agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)
        self.assertEqual(pending['status'], 'needs_approval')
        rejected = agent.approve(self.path, self.session, 'agent-a', 'yes', now=101)
        self.assertEqual(rejected['status'], 'rejected')
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=102)['status'], 'rejected')
        transport.assert_not_called()
        with self.assertRaises(agent.AgentError):
            self.approve(state)

    def test_expired_approval_requires_new_explicit_confirmation(self):
        state = self.approve(self.propose())
        transport = Mock(side_effect=AssertionError('must not call'))
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=400)['status'], 'needs_approval')
        self.assertEqual(self.saved()['approval']['expires_at'], 400)
        renewed = agent.approve(self.path, self.session, 'agent-a', 'APROBAR ' + state['plan_digest'], now=400)
        self.assertEqual(renewed['approval']['expires_at'], 700)
        transport.assert_not_called()

    def test_withdrawal_after_attempt_does_not_claim_remote_cancellation(self):
        state = self.approve(self.propose())
        unavailable = Mock(return_value=(503, {'error': 'temporarily_unavailable'}))
        agent.execute(self.path, self.session, 'agent-a', transport=unavailable, now=101)
        withdrawn = agent.approve(self.path, self.session, 'agent-a', 'no', now=401)
        self.assertEqual(withdrawn['status'], 'needs_approval')
        self.assertTrue(withdrawn['result']['remote_operation_may_continue'])
        self.assertEqual(withdrawn['observations'][-1]['event'], 'approval_withdrawn_after_attempt')
        self.assertIsNone(withdrawn['approval'])
        blocked = Mock(side_effect=AssertionError('must not call'))
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=blocked, now=402)['status'], 'needs_approval')
        blocked.assert_not_called()
        # The remote worker completes while the local agent has no permission
        # to send another write. A new approval allows read-first reconciliation.
        agent.approve(self.path, self.session, 'agent-a', 'APROBAR ' + state['plan_digest'], now=403)
        recovered = Mock(return_value=(200, self.observed(state)))
        resumed = agent.execute(self.path, self.session, 'agent-a', transport=recovered, now=404)
        self.assertEqual(resumed['status'], 'completed')
        self.assertTrue(resumed['result']['reconciled'])
        self.assertEqual(recovered.call_count, 1)
        self.assertEqual(recovered.call_args.args[2], 'GET')
        self.assertEqual(resumed['plan']['request_key'], state['plan']['request_key'])

    def test_create_observes_and_completed_replay_has_no_new_effect(self):
        state = self.approve(self.propose())
        observed = self.observed(state)
        calls = []
        def transport(session, subject, method, path, data, key, token, correlation):
            calls.append(method)
            if method == 'POST':
                self.assertTrue(approval.verify(token, session['approval_key'], subject, method, path, data, key, now=101))
                return 201, observed
            return 200, observed
        completed = agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)
        self.assertEqual(completed['status'], 'completed')
        self.assertEqual(completed['result']['observed']['status'], 'CONFIRMED')
        agent.execute(self.path, self.session, 'agent-a', transport=transport, now=102)
        self.assertEqual(calls, ['POST', 'GET'])

    def test_lost_write_response_recovers_by_observation_without_new_post(self):
        state = self.approve(self.propose())
        observed = self.observed(state)
        calls = []
        def transport(session, subject, method, path, data, key, token, correlation):
            calls.append((method, key))
            if method == 'POST':
                self.assertEqual(self.saved()['status'], 'pending')
                raise OSError('connection lost after commit')
            return 200, observed
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)['status'], 'pending')
        # Loading from disk is the same path used by a restarted process.
        resumed = agent.execute(self.path, {**self.session, 'port': 12346}, 'agent-a', transport=transport, now=102)
        self.assertEqual(resumed['status'], 'completed')
        self.assertTrue(resumed['result']['reconciled'])
        self.assertEqual(calls, [('POST', state['plan']['request_key']), ('GET', '')])

    def test_provider_unavailable_retries_identical_key_and_payload(self):
        state = self.approve(self.propose())
        observed = self.observed(state)
        calls = []
        def transport(session, subject, method, path, data, key, token, correlation):
            calls.append((method, data, key))
            if len(calls) == 1:
                return 503, {'error': 'temporarily_unavailable'}
            if len(calls) == 2:
                return 404, {'error': 'booking_not_found'}
            return (201 if method == 'POST' else 200), observed
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)['status'], 'pending')
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=102)['status'], 'completed')
        self.assertEqual(calls[0], calls[2])
        self.assertEqual(calls[0][2], state['plan']['request_key'])

    def test_create_recovery_reports_current_cancelled_state(self):
        state = self.approve(self.propose())
        agent.execute(self.path, self.session, 'agent-a', transport=Mock(side_effect=OSError()), now=101)
        observed = self.observed(state, 'CANCELLED')
        transport = Mock(return_value=(200, observed))
        result = agent.execute(self.path, self.session, 'agent-a', transport=transport, now=102)
        self.assertEqual(result['result']['body']['status'], 'CANCELLED')
        self.assertEqual(transport.call_args.args[2], 'GET')

    def test_cancel_requires_its_own_approval_and_observes_refund_state(self):
        oid = 'a' * 64
        state = self.propose('cancel ' + oid)
        transport = Mock()
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)['status'], 'needs_approval')
        transport.assert_not_called()
        self.approve(state)
        transport.side_effect = [(200, {'id': oid, 'status': 'CANCELLED'}), (200, {'id': oid, 'status': 'CANCELLED'})]
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)['status'], 'completed')
        self.assertEqual([c.args[2] for c in transport.call_args_list], ['DELETE', 'GET'])

    def test_read_only_list_does_not_need_approval(self):
        self.propose('list')
        transport = Mock(return_value=(200, {'bookings': []}))
        self.assertEqual(agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)['status'], 'completed')
        self.assertEqual(transport.call_args.args[2], 'GET')
        self.assertIsNone(transport.call_args.args[6])

    def test_wrong_subject_session_and_tampered_payload_cannot_execute(self):
        self.approve(self.propose())
        for session, subject in ((self.session, 'agent-b'), ({**self.session, 'prefix': 'db-lab-aaaaaaaaaa'}, 'agent-a'),
                                 ({**self.session, 'approval_key': 'different-key' * 5}, 'agent-a')):
            with self.subTest(subject=subject, session=session['prefix']), self.assertRaises(agent.AgentError):
                agent.execute(self.path, session, subject, transport=Mock(), now=101)
        raw = json.loads(self.path.read_text())
        raw['plan']['action']['amount'] = 99999
        self.path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(agent.AgentError, 'integrity'):
            self.saved()

    def test_malformed_state_and_symlink_rejected(self):
        self.path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(agent.AgentError):
            self.saved()
        self.path.unlink()
        target = self.path.with_name('other.json')
        target.write_text('{}')
        self.path.symlink_to(target)
        with self.assertRaises(agent.AgentError):
            self.saved()
        with self.assertRaises(agent.AgentError):
            self.propose()

    def test_failed_http_outcome_not_reported_as_success(self):
        self.approve(self.propose())
        result = agent.execute(self.path, self.session, 'agent-a', transport=Mock(return_value=(402, {'error': 'payment_declined'})), now=101)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(agent.exit_code(result), 2)

    def test_mismatched_observation_remains_pending(self):
        state = self.approve(self.propose())
        observed = self.observed(state)
        transport = Mock(side_effect=[(201, observed), (200, {**observed, 'id': 'f' * 64})])
        result = agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)
        self.assertEqual(result['status'], 'pending')

    def test_completed_replay_identifies_cached_receipt(self):
        state = self.approve(self.propose())
        transport = Mock(return_value=(200, self.observed(state)))
        first = agent.execute(self.path, self.session, 'agent-a', transport=transport, now=101)
        second = agent.execute(self.path, self.session, 'agent-a', transport=transport, now=102)
        self.assertEqual(second['result']['observation_source'], 'cached_receipt')
        self.assertEqual(first['result']['observed_at'], second['result']['observed_at'])
        self.assertEqual(transport.call_count, 2)

    def test_session_requires_distinct_key_and_valid_loopback_port(self):
        path = self.path.with_name('session.json')
        for values in ({**self.session, 'approval_key': self.session['key']},
                       {**self.session, 'port': True}, {**self.session, 'port': 65536},
                       {**self.session, 'key': 'short'}, {**self.session, 'prefix': 'https://attacker.test'}):
            path.write_text(json.dumps(values))
            with self.subTest(values=values), self.assertRaises(agent.AgentError):
                agent.session_from(path)

    def test_http_proxy_environment_cannot_receive_local_credentials(self):
        seen = []
        class CaptureHTTP(HTTPHandler):
            def http_open(self, req):
                seen.append(req)
                result = addinfourl(io.BytesIO(b'{"bookings":[]}'), {}, req.full_url, 200)
                result.msg = 'OK'
                return result
        def intercepted_opener(*handlers):
            return build_opener(*handlers, CaptureHTTP())
        with patch.dict(os.environ, {'http_proxy': 'http://attacker.invalid:54321',
                                     'HTTP_PROXY': 'http://attacker.invalid:54321', 'no_proxy': '', 'NO_PROXY': ''}), \
                patch.object(agent, 'build_opener', side_effect=intercepted_opener):
            code, body = agent.request(self.session, 'agent-a', 'GET', '/bookings')
        self.assertEqual((code, body), (200, {'bookings': []}))
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].host, '127.0.0.1:12345')
        self.assertEqual(seen[0].selector, '/bookings')
        self.assertTrue(seen[0].get_header('Authorization').startswith('Bearer '))

    def test_cli_plan_inspect_and_eof_reject_without_network(self):
        session_path = self.path.with_name('session.json')
        session_path.write_text(json.dumps(self.session))
        command = [sys.executable, str(ROOT / 'booking_lab/agent.py'), '--session', str(session_path), '--state', str(self.path)]
        planned = subprocess.run(command + ['--goal', 'create BOG-MDE 12500', 'plan'], capture_output=True, text=True)
        self.assertEqual(planned.returncode, 0, planned.stderr)
        state = json.loads(planned.stdout)
        inspected = subprocess.run(command + ['inspect'], capture_output=True, text=True)
        self.assertEqual(json.loads(inspected.stdout)['plan_digest'], state['plan_digest'])
        rejected = subprocess.run(command + ['approve'], input='', capture_output=True, text=True)
        self.assertEqual(rejected.returncode, 2, rejected.stderr)
        self.assertEqual(json.loads(rejected.stdout)['status'], 'rejected')
        executed = subprocess.run(command + ['execute'], capture_output=True, text=True)
        self.assertEqual(executed.returncode, 2)
        self.assertEqual(json.loads(executed.stdout)['attempts'], 0)

    def test_concurrent_cli_execute_serializes_same_state_and_writes_once(self):
        state = self.propose()
        agent.approve(self.path, self.session, 'agent-a', 'APROBAR ' + state['plan_digest'])
        session_path = self.path.with_name('session.json')
        session_path.write_text(json.dumps(self.session))
        marker = self.path.with_name('writes.log')
        start = self.path.with_name('start')
        # Exercise the actual CLI/controller/state lock in independent processes.
        # The HTTP adapter is replaced by a deterministic fixture; DB concurrency
        # is covered separately by the runner's PostgreSQL E2E.
        script = r'''
import hashlib, json, pathlib, sys, time
sys.path.insert(0, sys.argv[1])
import agent
session_path, state_path, marker, start, ready = map(pathlib.Path, sys.argv[2:])
def transport(session, subject, method, path, payload, key, approval, correlation):
    if method == 'POST':
        with marker.open('a') as stream:
            stream.write(key+'\n')
        time.sleep(0.2)
    saved = agent.load_state(state_path, session, subject)
    intent = saved['plan']['request_key']
    oid = hashlib.sha256(('POST /bookings\0'+subject+'\0'+intent).encode()).hexdigest()
    return (201 if method == 'POST' else 200), {'id': oid, 'status':'CONFIRMED', 'itinerary':'BOG-MDE', 'amount':12500}
agent.execute.__kwdefaults__['transport'] = transport
ready.write_text('ready')
deadline = time.monotonic()+5
while not start.exists():
    if time.monotonic()>deadline:
        raise SystemExit(99)
    time.sleep(0.01)
raise SystemExit(agent.main(['--session',str(session_path),'--state',str(state_path),'execute']))
'''
        processes = []
        for index in range(2):
            ready = self.path.with_name('ready-' + str(index))
            processes.append(subprocess.Popen([sys.executable, '-c', script, str(ROOT / 'booking_lab'),
                                               str(session_path), str(self.path), str(marker), str(start), str(ready)],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        try:
            deadline = time.monotonic() + 5
            while not all(self.path.with_name('ready-' + str(index)).exists() for index in range(2)):
                if time.monotonic() > deadline:
                    self.fail('CLI fixtures did not become ready')
                time.sleep(0.01)
            start.write_text('go')
            results = []
            for process in processes:
                stdout, stderr = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, stderr)
                results.append(json.loads(stdout))
            self.assertEqual(marker.read_text().splitlines(), [state['plan']['request_key']])
            self.assertEqual({result['result']['observation_source'] for result in results}, {'http', 'cached_receipt'})
            self.assertEqual(self.saved()['attempts'], 1)
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                process.communicate()


if __name__ == '__main__':
    unittest.main()
