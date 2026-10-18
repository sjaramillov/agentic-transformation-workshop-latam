"""Offline receipt/budget/admission checks. These tests never call AWS or Docker."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'booking_lab'))
import agent
import bedrock_e2e


class PlannerReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name)/'receipt.json'

    def response(self, text='{"action":"list"}', **extra):
        response = {'stopReason': 'end_turn', 'output': {'message': {'role': 'assistant', 'content': [{'text': text}]}},
                    'usage': {'inputTokens': 101, 'outputTokens': 12, 'totalTokens': 113},
                    'metrics': {'latencyMs': 345}}
        response.update(extra)
        return subprocess.CompletedProcess([], 0, json.dumps(response), '')

    def test_receipt_records_response_usage_and_hashes_without_account_or_headers(self):
        model = 'arn:aws:bedrock:us-east-1:123456789012:inference-profile/chosen-profile'
        response = self.response(ResponseMetadata={'RequestId': 'abcd-1234', 'HTTPHeaders': {'sensitive': 'secret'}})
        runner = Mock(return_value=response)
        self.assertEqual(agent.bedrock_plan('list', model, 'us-east-1', runner, evidence_path=self.path), {'action': 'list'})
        receipt = json.loads(self.path.read_text())
        self.assertEqual(receipt['status'], 'proposal_validated')
        self.assertEqual(receipt['usage'], {'inputTokens': 101, 'outputTokens': 12, 'totalTokens': 113})
        self.assertEqual(receipt['metrics'], {'latencyMs': 345})
        self.assertEqual(receipt['request_id'], 'abcd-1234')
        self.assertEqual(receipt['model_id_sha256'], hashlib.sha256(model.encode()).hexdigest())
        self.assertEqual(receipt['response_sha256'], hashlib.sha256(response.stdout.encode()).hexdigest())
        self.assertEqual(receipt['goal_sha256'], hashlib.sha256(b'list').hexdigest())
        self.assertEqual(receipt['system_sha256'], hashlib.sha256(agent.BEDROCK_SYSTEM.encode()).hexdigest())
        self.assertNotIn('123456789012', self.path.read_text())
        self.assertNotIn('secret', self.path.read_text())
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(runner.call_args.kwargs['env']['AWS_MAX_ATTEMPTS'], '1')
        self.assertNotIn('--debug', runner.call_args.args[0])

    def test_cli_metadata_absence_is_explicit_and_invalid_fields_are_not_published(self):
        response = self.response(usage={'inputTokens': True, 'outputTokens': -1, 'totalTokens': 'ten', 'secret': 'private'},
                                 metrics={'latencyMs': float('inf')},
                                 ResponseMetadata={'RequestId': 'bad value containing private details'})
        # Non-finite response JSON is rejected before it can enter the receipt.
        with self.assertRaises(agent.AgentError):
            agent.bedrock_plan('list', 'model', 'us-east-1', Mock(return_value=response), evidence_path=self.path)
        receipt = json.loads(self.path.read_text())
        self.assertEqual(receipt['status'], 'proposal_rejected')
        self.assertEqual(receipt['request_id_exposure'], 'not_exposed_by_aws_cli')
        self.assertIsNone(receipt['request_id'])
        self.assertNotIn('private', self.path.read_text())

    def test_rejected_model_proposal_is_distinct_from_failed_request(self):
        with self.assertRaises(agent.AgentError):
            agent.bedrock_plan('missing amount', 'model', 'us-east-1',
                               Mock(return_value=self.response('{"action":"unsupported"}')), evidence_path=self.path)
        receipt = json.loads(self.path.read_text())
        self.assertEqual(receipt['status'], 'proposal_rejected')
        self.assertEqual(receipt['cli_exit_code'], 0)
        self.assertEqual(receipt['stop_reason'], 'end_turn')
        self.assertIs(receipt['semantic_refusal_exact'], True)
        self.path.unlink()
        with self.assertRaises(agent.AgentError):
            agent.bedrock_plan('list', 'model', 'us-east-1',
                               Mock(return_value=subprocess.CompletedProcess([], 254, '', 'account secrets')), evidence_path=self.path)
        receipt = json.loads(self.path.read_text())
        self.assertEqual(receipt['status'], 'request_failed')
        self.assertEqual(receipt['cli_exit_code'], 254)
        self.assertNotIn('response_sha256', receipt)
        self.assertNotIn('account secrets', self.path.read_text())

    def test_malformed_proposal_does_not_count_as_semantic_refusal(self):
        with self.assertRaises(agent.AgentError):
            agent.bedrock_plan('missing amount', 'model', 'us-east-1',
                               Mock(return_value=self.response('not JSON')), evidence_path=self.path)
        receipt = json.loads(self.path.read_text())
        self.assertEqual(receipt['status'], 'proposal_rejected')
        self.assertIs(receipt['semantic_refusal_exact'], False)

    def test_timeout_and_existing_receipt_fail_closed(self):
        runner = Mock(side_effect=subprocess.TimeoutExpired('aws', 90))
        with self.assertRaises(agent.AgentError):
            agent.bedrock_plan('list', 'model', 'us-east-1', runner, evidence_path=self.path)
        self.assertEqual(json.loads(self.path.read_text())['status'], 'request_failed')
        runner.reset_mock()
        with self.assertRaisesRegex(agent.AgentError, 'already exists'):
            agent.bedrock_plan('list', 'model', 'us-east-1', runner, evidence_path=self.path)
        runner.assert_not_called()


class LiveScenarioAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.lab = SimpleNamespace(work=self.work, evidence={})
        self.lab.session_file = lambda: self.work/'session.json'
        self.model, self.region = 'chosen-model', 'us-east-1'

    def fake_cli(self, action=None, request_failure=False, response_region=None):
        def run(argv, **kwargs):
            self.assertEqual(argv[-1], 'plan')
            self.assertEqual(argv[argv.index('--planner')+1], 'bedrock')
            self.assertEqual(kwargs['env']['AWS_MAX_ATTEMPTS'], '1')
            goal = argv[argv.index('--goal')+1]
            receipt_path = Path(argv[argv.index('--planner-evidence')+1])
            state_path = Path(argv[argv.index('--state')+1])
            receipt = {'model_id_sha256': hashlib.sha256(self.model.encode()).hexdigest(),
                       'region': response_region or self.region, 'goal_sha256': hashlib.sha256(goal.encode()).hexdigest(),
                       'aws_max_attempts': 1, 'stop_reason': 'end_turn', 'response_sha256': 'a'*64,
                       'status': 'proposal_validated' if action else 'proposal_rejected', 'cli_exit_code': 0,
                       'semantic_refusal_exact': action is None}
            if request_failure:
                receipt.update(status='request_failed', cli_exit_code=254)
                receipt.pop('response_sha256')
            receipt_path.write_text(json.dumps(receipt))
            proposal = {'plan': {'planner': 'bedrock', 'action': action}, 'plan_digest': 'b'*64}
            if action:
                state_path.write_text(json.dumps(proposal))
            return subprocess.CompletedProcess(argv, 0 if action else 2, json.dumps(proposal) if action else '', '')
        return Mock(side_effect=run)

    def test_four_call_budget_and_no_rules_fallback(self):
        runner = self.fake_cli({'action': 'list'})
        scenario = bedrock_e2e.LiveBedrockScenario(self.lab, self.model, self.region, runner)
        for index in range(4):
            scenario.plan('case-'+str(index), 'list', {'action': 'list'})
        with self.assertRaisesRegex(AssertionError, 'budget'):
            scenario.plan('fifth', 'list', {'action': 'list'})
        self.assertEqual(runner.call_count, 4)
        self.assertEqual(self.lab.evidence['bedrock']['model_calls_attempted'], 4)
        self.assertFalse(self.lab.evidence['bedrock']['rules_fallback_used'])

    def test_unexpected_valid_action_is_never_approved(self):
        runner = self.fake_cli({'action': 'create', 'itinerary': 'BOG-MDE', 'amount': 999})
        scenario = bedrock_e2e.LiveBedrockScenario(self.lab, self.model, self.region, runner)
        with self.assertRaisesRegex(AssertionError, 'differs'):
            scenario.plan('create', 'create', {'action': 'create', 'itinerary': 'BOG-MDE', 'amount': 12500})
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(runner.call_args.args[0][-1], 'plan')

    def test_request_failure_is_not_accepted_as_semantic_rejection(self):
        runner = self.fake_cli(request_failure=True)
        scenario = bedrock_e2e.LiveBedrockScenario(self.lab, self.model, self.region, runner)
        with self.assertRaisesRegex(AssertionError, 'completed response'):
            scenario.plan('negative', bedrock_e2e.NEGATIVE_GOAL)
        self.assertEqual(scenario.calls[0]['receipt']['status'], 'request_failed')

    def test_negative_response_requires_no_created_state(self):
        runner = self.fake_cli()
        scenario = bedrock_e2e.LiveBedrockScenario(self.lab, self.model, self.region, runner)
        self.assertIsNone(scenario.plan('negative', bedrock_e2e.NEGATIVE_GOAL))
        self.assertEqual(scenario.calls[0]['acceptance'], 'expected_semantic_rejection_without_plan')
        self.assertFalse((self.work/'negative.json').exists())

    def test_wrong_region_receipt_is_rejected(self):
        scenario = bedrock_e2e.LiveBedrockScenario(self.lab, self.model, self.region,
                                                  self.fake_cli({'action': 'list'}, response_region='us-west-2'))
        with self.assertRaises(AssertionError):
            scenario.plan('list', 'list', {'action': 'list'})

    def test_live_runner_requires_both_explicit_opt_ins_before_setup(self):
        base = ['--model-id', self.model, '--region', self.region]
        for flags in ([], ['--live-bedrock'], ['--confirm-test-operator']):
            with self.subTest(flags=flags), patch.object(bedrock_e2e, 'Lab') as lab, \
                    patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit) as error:
                bedrock_e2e.main(base+flags)
            self.assertEqual(error.exception.code, 2)
            lab.assert_not_called()

    def test_failed_live_scenario_preserves_failure_and_finishes_own_lab(self):
        lab = Mock()
        lab.evidence = {}
        scenario = Mock()
        scenario.run.side_effect = AssertionError('model response fixture mismatch')
        with patch.object(bedrock_e2e, 'Lab', return_value=lab), \
                patch.object(bedrock_e2e, 'LiveBedrockScenario', return_value=scenario), \
                patch('sys.stderr', new_callable=io.StringIO):
            code = bedrock_e2e.main(['--live-bedrock', '--confirm-test-operator', '--model-id', self.model,
                                    '--region', self.region, '--output', str(self.work/'result.json')])
        self.assertEqual(code, 1)
        self.assertEqual(lab.evidence['result'], 'failed')
        self.assertEqual(lab.evidence['failure_detail'], 'model response fixture mismatch')
        lab.finish.assert_called_once()


if __name__ == '__main__':
    unittest.main()
