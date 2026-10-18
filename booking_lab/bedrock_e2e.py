#!/usr/bin/env python3
"""Explicit opt-in: four live Bedrock plans and PostgreSQL/HTTP agent validation.

This script is never selected by the normal CI runner. An authorized operator
must choose the model/region and explicitly enable the synthetic test approver.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from agent import AgentError, strict_json
from run import Lab, ROOT, docker
from audit import verify as verify_audit


CALL_BUDGET = 4
NEGATIVE_GOAL = ('Prepara una reserva BOG-MDE. No he proporcionado el importe; '
                 'no lo inventes ni ejecutes ninguna operación.')
CREATE_GOAL = ('Propón crear una reserva BOG-MDE por exactamente 12500 unidades '
               'menores sintéticas. La ejecución requiere mi aprobación.')
LIST_GOAL = 'Consulta y muestra mis reservas actuales sin modificarlas.'


class LiveBedrockScenario:
    def __init__(self, lab, model_id, region, process_runner=subprocess.run):
        self.lab, self.model_id, self.region = lab, model_id, region
        self.process_runner = process_runner
        self.session = lab.session_file()
        self.calls = []
        self.attempted = 0
        self.lab.evidence['evaluation_kind'] = 'live_bedrock_database_e2e'
        self.lab.evidence['bedrock'] = {
            'model_id': re.sub(r'(?<=:)\d{12}(?=:)', '<account>', model_id),
            'model_id_sha256': hashlib.sha256(model_id.encode()).hexdigest(),
            'region': region, 'call_budget': CALL_BUDGET, 'model_calls_attempted': 0,
            'calls': self.calls, 'rules_fallback_used': False,
            'aws_max_attempts_per_call': 1, 'raw_cli_debug_used': False,
            'test_operator_confirmation': 'explicit opt-in, exact fixture matching before approval',
            'test_confirmation_is_human_identity_proof': False}

    def cli(self, state, command, *, goal=None, receipt=None, answer='', expected=0):
        argv = [sys.executable, str(ROOT/'agent.py'), '--session', str(self.session),
                '--state', str(state), '--subject', 'agent-a']
        if goal is not None:
            argv += ['--goal', goal, '--planner', 'bedrock', '--model-id', self.model_id,
                     '--region', self.region, '--planner-evidence', str(receipt)]
        process = self.process_runner(argv+[command], input=answer, capture_output=True, text=True,
                                      timeout=110, env={**os.environ, 'AWS_MAX_ATTEMPTS': '1', 'AWS_RETRY_MODE': 'standard'})
        if process.returncode != expected:
            # No raw AWS stderr or session content is copied into public evidence.
            raise AssertionError('Agent CLI '+command+' returned '+str(process.returncode)+'; expected '+str(expected))
        return strict_json(process.stdout) if process.stdout.strip() else {}

    def plan(self, name, goal, expected_action=None):
        if self.attempted >= CALL_BUDGET:
            raise AssertionError('Live Bedrock inference budget exhausted')
        self.attempted += 1
        self.lab.evidence['bedrock']['model_calls_attempted'] = self.attempted
        state, receipt = self.lab.work/(name+'.json'), self.lab.work/(name+'-planner.json')
        event = {'sequence': self.attempted, 'case': name, 'goal': goal,
                 'goal_sha256': hashlib.sha256(goal.encode()).hexdigest(), 'receipt': None}
        self.calls.append(event)
        try:
            proposal = self.cli(state, 'plan', goal=goal, receipt=receipt,
                                expected=2 if expected_action is None else 0)
        finally:
            if receipt.exists():
                data = receipt.read_bytes()
                event['receipt'] = strict_json(data)
                event['receipt_sha256'] = hashlib.sha256(data).hexdigest()
        observed = event['receipt']
        if not isinstance(observed, dict):
            raise AssertionError('Bedrock CLI produced no planner evidence')
        if (observed.get('model_id_sha256') != hashlib.sha256(self.model_id.encode()).hexdigest()
                or observed.get('region') != self.region or observed.get('goal_sha256') != event['goal_sha256']
                or observed.get('aws_max_attempts') != 1 or observed.get('stop_reason') != 'end_turn'
                or not re.fullmatch(r'[a-f0-9]{64}', observed.get('response_sha256', ''))):
            raise AssertionError('Bedrock evidence does not match this model/region/goal or a completed response')
        if expected_action is None:
            if (observed.get('status') != 'proposal_rejected'
                    or observed.get('semantic_refusal_exact') is not True or state.exists()):
                raise AssertionError('Missing-amount goal was not rejected before a plan was created')
            event['acceptance'] = 'expected_semantic_rejection_without_plan'
            return None
        if observed.get('status') != 'proposal_validated':
            raise AssertionError('Bedrock did not produce a validated proposal')
        if proposal.get('plan', {}).get('planner') != 'bedrock':
            raise AssertionError('Expected a live Bedrock plan; no rules fallback allowed')
        action = proposal.get('plan', {}).get('action')
        event['proposed_action'], event['expected_action'] = action, expected_action
        if action != expected_action:
            raise AssertionError('Bedrock proposal differs from the authorized synthetic fixture; nothing approved')
        event['acceptance'] = 'exact_fixture_match'
        event['plan_digest'] = proposal['plan_digest']
        return state

    def approve(self, state):
        proposal = strict_json(state.read_bytes())
        response = self.cli(state, 'approve', answer='APROBAR '+proposal['plan_digest']+'\n')
        if response.get('status') != 'approved':
            raise AssertionError('Test operator did not authorize the exact plan')
        return proposal

    def run(self):
        lab = self.lab

        def missing_amount():
            before = lab.scalar('SELECT count(*) FROM operations;')
            try:
                self.plan('bedrock-missing-amount', NEGATIVE_GOAL)
            finally:
                if lab.scalar('SELECT count(*) FROM operations;') != before:
                    raise AssertionError('Rejected proposal changed the database')
            assert lab.scalar('SELECT count(*) FROM charges;') == '0'
        lab.case('bedrock_missing_amount_rejected_without_plan_or_writes', missing_amount)

        def propose_create():
            self.create_state = self.plan('bedrock-create', CREATE_GOAL,
                                         {'action': 'create', 'itinerary': 'BOG-MDE', 'amount': 12500})
            proposal = strict_json(self.create_state.read_bytes())
            self.oid = lab.oid(proposal['plan']['request_key'])
            assert self.cli(self.create_state, 'execute', expected=2)['status'] == 'needs_approval'
            assert lab.scalar('SELECT count(*) FROM operations;') == '0'
            assert lab.scalar('SELECT count(*) FROM charges;') == '0'
        lab.case('bedrock_create_plan_requires_explicit_approval_before_writes', propose_create)

        def create_with_recovery():
            self.approve(self.create_state)
            calls_before = self.attempted
            docker('stop', lab.prefix+'-payments')
            try:
                assert self.cli(self.create_state, 'execute', expected=3)['status'] == 'pending'
                assert lab.scalar("SELECT status FROM operations WHERE id='"+self.oid+"';") == 'NEW'
                assert lab.scalar('SELECT count(*) FROM charges;') == '0'
            finally:
                docker('start', lab.prefix+'-payments')
            lab.wait(lambda: lab.scalar("SELECT status FROM operations WHERE id='"+self.oid+"';") == 'CONFIRMED')
            outcome = self.cli(self.create_state, 'execute')
            assert outcome['status'] == 'completed' and outcome['result']['reconciled'] is True
            assert self.attempted == calls_before
            assert lab.scalar("SELECT state||':'||captures FROM charges WHERE operation_id='"+self.oid+"';") == 'CAPTURED:1'
            cached = self.cli(self.create_state, 'execute')
            assert cached['result']['observation_source'] == 'cached_receipt'
            lab.evidence['bedrock_recovery'] = {'operation_id': self.oid, 'provider_outage_observed': True,
                                               'model_calls_before_resume': calls_before,
                                               'model_calls_after_resume': self.attempted,
                                               'captures': 1, 'state_reused': True}
        lab.case('bedrock_approved_plan_provider_outage_resume_without_new_inference_or_double_charge', create_with_recovery)

        def list_created():
            state = self.plan('bedrock-list', LIST_GOAL, {'action': 'list'})
            outcome = self.cli(state, 'execute')
            assert outcome['status'] == 'completed'
            expected = {'id': self.oid, 'itinerary': 'BOG-MDE', 'amount': 12500, 'status': 'CONFIRMED'}
            assert outcome['result']['body']['bookings'] == [expected]
            assert lab.req('GET', '/bookings/'+self.oid, principal='agent-b', port=lab.port_b)[0] == 404
            assert strict_json(state.read_bytes())['approval'] is None
        lab.case('bedrock_read_only_plan_lists_created_booking_with_subject_isolation', list_created)

        def cancel_created():
            goal = 'Propón cancelar únicamente mi reserva con ID '+self.oid+'. Espera mi aprobación para ejecutarlo.'
            state = self.plan('bedrock-cancel', goal, {'action': 'cancel', 'booking_id': self.oid})
            assert self.cli(state, 'execute', expected=2)['status'] == 'needs_approval'
            assert lab.scalar("SELECT status FROM bookings WHERE id='"+self.oid+"';") == 'CONFIRMED'
            self.approve(state)
            outcome = self.cli(state, 'execute')
            assert outcome['status'] == 'completed'
            assert outcome['result']['observed']['status'] == 'CANCELLED'
            assert self.cli(state, 'execute')['result']['observation_source'] == 'cached_receipt'
            assert lab.scalar("SELECT state||':'||captures||':'||refunds FROM charges WHERE operation_id='"+self.oid+"';") == 'REFUNDED:1:1'
        lab.case('bedrock_cancel_plan_requires_new_approval_and_refunds_once', cancel_created)

        lab.case('bedrock_postgresql_quiescent_snapshot_and_exact_restore', lab.verify_database_restore)

        def audit_and_invariants():
            snapshot = lab.audit_snapshot()
            assert verify_audit(snapshot['records'], lab.audit_key, snapshot['checkpoint'])
            assert len(snapshot['records']) == int(lab.scalar('SELECT count(*) FROM audit_events;'))
            assert lab.scalar('SELECT count(*) FROM outbox WHERE delivered_at IS NULL;') == '0'
            assert lab.scalar("SELECT count(*) FROM operations WHERE status IN ('NEW','CHARGED','COMPENSATING','CANCELLING');") == '0'
            assert lab.scalar("SELECT count(*) FROM charges WHERE captures>1 OR refunds>1;") == '0'
            assert lab.scalar('SELECT count(*) FROM bookings;') == '1'
            lab.evidence['live_workflow_invariants'] = {'pending_operations': 0, 'undelivered_audit_events': 0,
                                                       'duplicate_captures_or_refunds': 0, 'bookings': 1,
                                                       'terminal_booking': 'CANCELLED', 'terminal_payment': 'REFUNDED',
                                                       'signed_audit_records': len(snapshot['records'])}
        lab.case('bedrock_workflow_signed_audit_and_terminal_database_invariants', audit_and_invariants)
        assert self.attempted == CALL_BUDGET
        lab.evidence['bedrock']['completed_model_responses'] = sum(
            isinstance(call['receipt'], dict) and call['receipt'].get('cli_exit_code') == 0 for call in self.calls)
        lab.evidence['bedrock']['accepted_positive_plans'] = 3
        lab.evidence['bedrock']['expected_negative_rejections'] = 1
        lab.evidence['result'] = 'passed'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-bedrock', action='store_true', help='Explicitly allow up to four real model calls')
    parser.add_argument('--confirm-test-operator', action='store_true', help='Approve only exact synthetic test fixtures')
    parser.add_argument('--model-id', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--output', type=Path, default=Path('.local/bedrock-e2e.json'))
    args = parser.parse_args(argv)
    if not __debug__:
        parser.error('Run without -O: live E2E assertions must remain enabled')
    if not args.live_bedrock or not args.confirm_test_operator:
        parser.error('Both --live-bedrock and --confirm-test-operator are required; no implicit cloud execution')
    if not re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-[0-9]', args.region):
        parser.error('Invalid region')
    if not 0 < len(args.model_id) <= 2048 or args.model_id.startswith('-'):
        parser.error('Invalid explicit model ID')
    if args.output.exists() or args.output.is_symlink():
        parser.error('Output already exists; preserve previous evidence and choose a new file')
    lab = Lab(args.output)
    lab.evidence['evaluation_kind'] = 'live_bedrock_database_e2e'
    lab.evidence['live_bedrock_opt_in'] = True
    try:
        lab.setup()
        lab.start('worker', 'worker', 'booking_app', audit=True)
        scenario = LiveBedrockScenario(lab, args.model_id, args.region)
        scenario.run()
        return 0
    except BaseException as error:
        lab.evidence['result'] = 'failed'
        lab.evidence['failure_type'] = type(error).__name__
        # Assertion messages are controller-owned and never contain AWS stderr.
        if isinstance(error, (AssertionError, AgentError)):
            lab.evidence['failure_detail'] = str(error)
        print('LIVE BEDROCK E2E FAILED: '+type(error).__name__, file=sys.stderr, flush=True)
        return 1
    finally:
        lab.finish()


if __name__ == '__main__':
    raise SystemExit(main())
