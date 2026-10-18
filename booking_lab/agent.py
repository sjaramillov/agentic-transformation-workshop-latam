#!/usr/bin/env python3
"""Bounded MIT booking workflow: propose, approve, act, observe and recover.

The default planner is deterministic and needs no model. Bedrock is optional:
it proposes a single allowlisted action; the controller owns all permissions,
approval, state, HTTP calls, and recovery. Never send session files to a model.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPRedirectHandler, ProxyHandler, build_opener

from auth import encode
from approval import HEADER, MAX_TTL, canonical, issue


class AgentError(ValueError):
    """Expected validation error, safe to show without private session content."""


def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise AgentError('Duplicate JSON field')
            out[key] = value
        return out

    def invalid(_):
        raise AgentError('Non-finite JSON value')

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise AgentError('Invalid JSON document') from exc


def read_private(path):
    path = Path(path)
    if path.is_symlink():
        raise AgentError('Private file must not be a symlink')
    try:
        with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)), 'rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise AgentError('Private document exceeds 64 KiB')
        return strict_json(raw)
    except OSError as exc:
        raise AgentError('Private document cannot be read') from exc


def session_from(path):
    session = read_private(path)
    if (not isinstance(session, dict)
            or not isinstance(session.get('prefix'), str)
            or not re.fullmatch(r'db-lab-[a-f0-9]{10}', session['prefix'])
            or type(session.get('port')) is not int or not 0 < session['port'] < 65536
            or any(not isinstance(session.get(k), str) or len(session[k]) < 32
                   for k in ('key', 'approval_key'))
            or session['key'] == session['approval_key']):
        raise AgentError('Invalid session or missing separate approval issuer key; start a new demo')
    return session


def validate_action(action):
    if not isinstance(action, dict):
        raise AgentError('Planner must return one action object')
    name = action.get('action')
    if name == 'list' and set(action) == {'action'}:
        return dict(action)
    if name == 'create' and set(action) == {'action', 'itinerary', 'amount'}:
        if (isinstance(action['itinerary'], str) and re.fullmatch(r'[A-Z]{3}-[A-Z]{3}', action['itinerary'])
                and type(action['amount']) is int and 0 < action['amount'] <= 10000000):
            return dict(action)
    if name == 'cancel' and set(action) == {'action', 'booking_id'}:
        if isinstance(action['booking_id'], str) and re.fullmatch(r'[a-f0-9]{64}', action['booking_id']):
            return dict(action)
    raise AgentError('Unsupported planner action or invalid arguments')


def rules_plan(goal):
    if not isinstance(goal, str) or len(goal) > 4096:
        raise AgentError('Goal must be text up to 4096 characters')
    words = goal.strip().split()
    if words in (['list'], ['listar']):
        return {'action': 'list'}
    if len(words) == 3 and words[0] in ('create', 'reservar') and re.fullmatch(r'[0-9]{1,8}', words[2]):
        return validate_action({'action': 'create', 'itinerary': words[1], 'amount': int(words[2])})
    if len(words) == 2 and words[0] in ('cancel', 'cancelar'):
        return validate_action({'action': 'cancel', 'booking_id': words[1]})
    raise AgentError('Use: list | create BOG-MDE 12500 | cancel <booking-id>; amount is synthetic minor units')


BEDROCK_SYSTEM = '''Propose one action for a synthetic booking workshop. Return only one JSON object:
{"action":"list"} OR {"action":"create","itinerary":"BOG-MDE","amount":12500}
OR {"action":"cancel","booking_id":"64 lowercase hexadecimal characters"}.
Amount is an explicit positive integer in synthetic minor units, maximum 10000000.
Never invent an amount, itinerary or booking ID. If required data are missing or
the user requests anything else, return {"action":"unsupported"}. Never return
code, URLs, headers, credentials, approval, subject, multiple actions or prose.
The controller will validate the proposal and require human approval for writes.'''


def bedrock_plan(goal, model_id, region=None, runner=subprocess.run):
    if not isinstance(goal, str) or not 0 < len(goal) <= 4096:
        raise AgentError('Goal must be text up to 4096 characters')
    if not isinstance(model_id, str) or not 0 < len(model_id) <= 2048 or model_id.startswith('-'):
        raise AgentError('Bedrock requires an explicit model or inference profile ID')
    if region is not None and not re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-[0-9]', region):
        raise AgentError('Invalid AWS region')
    # AWS CLI receives only the goal and fixed schema, never local state/secrets.
    command = ['aws', 'bedrock-runtime', 'converse', '--model-id', model_id,
               '--messages', json.dumps([{'role': 'user', 'content': [{'text': goal}]}]),
               '--system', json.dumps([{'text': BEDROCK_SYSTEM}]),
               '--inference-config', json.dumps({'maxTokens': 512}),
               '--output', 'json', '--no-cli-pager', '--no-cli-auto-prompt']
    if region:
        command += ['--region', region]
    try:
        completed = runner(command, capture_output=True, text=True, timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgentError('Bedrock request unavailable; verify AWS CLI, credentials and model access') from exc
    if completed.returncode:
        # CLI stderr can contain account/profile details; do not copy it into public evidence.
        raise AgentError('Bedrock request failed; verify credentials, region and model permission')
    if len(completed.stdout) > 32768:
        raise AgentError('Bedrock response too large')
    try:
        envelope = strict_json(completed.stdout)
        if not isinstance(envelope, dict):
            raise AgentError('Malformed Bedrock response envelope')
        if envelope.get('stopReason') != 'end_turn':
            raise AgentError('Bedrock did not finish a complete proposal')
        message = envelope['output']['message']
        blocks = message['content']
        if (message['role'] != 'assistant' or not isinstance(blocks, list) or len(blocks) != 1
                or not isinstance(blocks[0], dict) or set(blocks[0]) != {'text'}):
            raise AgentError('Bedrock must return one text proposal')
        return validate_action(strict_json(blocks[0]['text']))
    except (KeyError, TypeError) as exc:
        raise AgentError('Malformed Bedrock proposal') from exc


def binding(action, request_key):
    name = action['action']
    if name == 'create':
        return 'POST', '/bookings', {k: action[k] for k in ('itinerary', 'amount')}, request_key
    if name == 'cancel':
        return 'DELETE', '/bookings/' + action['booking_id'], None, ''
    return 'GET', '/bookings', None, ''


def digest(plan):
    return hashlib.sha256(canonical(plan)).hexdigest()


def seal(state, session):
    contents = {k: v for k, v in state.items() if k != 'integrity'}
    return hmac.new(session['approval_key'].encode(), b'booking-agent-state-v1\0' + canonical(contents),
                    hashlib.sha256).hexdigest()


def save_state(path, state, session):
    path = Path(path)
    if path.is_symlink():
        raise AgentError('State must not be a symlink')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    state['integrity'] = seal(state, session)
    raw = canonical(state) + b'\n'
    if len(raw) > 65536:
        raise AgentError('State exceeds 64 KiB')
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def state_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = path.with_name(path.name + '.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    except OSError as exc:
        raise AgentError('Cannot lock private state') from exc
    with os.fdopen(fd, 'w') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield


def load_state(path, session, subject):
    state = read_private(path)
    fields = {'schema_version', 'plan', 'plan_digest', 'status', 'approval', 'attempts',
              'observations', 'result', 'integrity'}
    if not isinstance(state, dict) or set(state) != fields or state['schema_version'] != 1:
        raise AgentError('Invalid agent state')
    signature = state['integrity']
    if (not isinstance(signature, str) or not re.fullmatch(r'[a-f0-9]{64}', signature)
            or not hmac.compare_digest(signature, seal(state, session))):
        raise AgentError('Agent state integrity check failed')
    plan = state['plan']
    expected = {'id', 'session', 'subject', 'action', 'request_key', 'correlation_id', 'planner', 'created_at'}
    if not isinstance(plan, dict) or set(plan) != expected:
        raise AgentError('Invalid saved plan')
    validate_action(plan['action'])
    if (plan['session'] != session['prefix'] or plan['subject'] != subject
            or subject not in ('agent-a', 'agent-b') or state['plan_digest'] != digest(plan)
            or not isinstance(plan['id'], str) or not re.fullmatch(r'[a-f0-9]{32}', plan['id'])
            or plan['request_key'] != 'agent-' + plan['id']
            or plan['correlation_id'] != str(uuid.UUID(hex=plan['id']))
            or type(plan['created_at']) is not int or plan['planner'] not in ('rules', 'bedrock')):
        raise AgentError('Saved plan binding mismatch')
    if state['status'] not in ('proposed', 'approved', 'rejected', 'pending', 'completed', 'failed', 'needs_approval'):
        raise AgentError('Invalid agent status')
    if type(state['attempts']) is not int or state['attempts'] < 0 or not isinstance(state['observations'], list):
        raise AgentError('Invalid agent execution state')
    decision = state['approval']
    if decision is not None:
        if (not isinstance(decision, dict) or set(decision) != {'plan_digest', 'approved_at', 'expires_at'}
                or decision['plan_digest'] != state['plan_digest']
                or type(decision['approved_at']) is not int or type(decision['expires_at']) is not int
                or not 0 < decision['expires_at'] - decision['approved_at'] <= MAX_TTL):
            raise AgentError('Invalid saved approval')
    return state


def propose(path, session, subject, goal, planner='rules', model_id=None, region=None, now=None):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise AgentError('State already exists; inspect/execute it or choose a new state path')
    if subject not in ('agent-a', 'agent-b'):
        raise AgentError('Unsupported workshop subject')
    if planner not in ('rules', 'bedrock') or now is not None and type(now) is not int:
        raise AgentError('Invalid planner or plan timestamp')
    action = rules_plan(goal) if planner == 'rules' else bedrock_plan(goal, model_id, region)
    identifier = uuid.uuid4().hex
    plan = {'id': identifier, 'session': session['prefix'], 'subject': subject,
            'action': action, 'request_key': 'agent-' + identifier,
            'correlation_id': str(uuid.UUID(hex=identifier)), 'planner': planner,
            'created_at': int(time.time()) if now is None else now}
    state = {'schema_version': 1, 'plan': plan, 'plan_digest': digest(plan), 'status': 'proposed',
             'approval': None, 'attempts': 0, 'observations': [], 'result': None}
    save_state(path, state, session)
    return state


def approve(path, session, subject, confirmation, now=None):
    state = load_state(path, session, subject)
    if state['status'] in ('completed', 'failed', 'rejected'):
        raise AgentError('A terminal plan cannot be approved again; use a new state for a new intention')
    if state['plan']['action']['action'] == 'list':
        raise AgentError('Read-only list does not need approval')
    if confirmation != 'APROBAR ' + state['plan_digest']:
        state['approval'] = None
        if state['attempts'] == 0:
            state['status'] = 'rejected'
        else:
            # Approval withdrawal stops further agent writes. It cannot undo a
            # request that may already be durably accepted by the remote worker.
            state['status'] = 'needs_approval'
            state['result'] = {**(state['result'] or {}), 'remote_operation_may_continue': True,
                               'approval_withdrawn': True}
            _observation(state, 'approval_withdrawn_after_attempt', remote_operation_may_continue=True)
        save_state(path, state, session)
        return state
    now = int(time.time()) if now is None else now
    if type(now) is not int:
        raise AgentError('Invalid approval timestamp')
    state['approval'] = {'plan_digest': state['plan_digest'], 'approved_at': now, 'expires_at': now + MAX_TTL}
    state['status'] = 'approved'
    save_state(path, state, session)
    return state


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


def request(session, subject, method, path, payload=None, request_key='', approval=None, correlation=None):
    scopes = {'GET': 'bookings:read', 'POST': 'bookings:write', 'DELETE': 'bookings:cancel'}
    headers = {'Authorization': 'Bearer ' + encode(session['key'], subject, scope=scopes[method]),
               'X-Correlation-ID': correlation or str(uuid.uuid4())}
    if request_key:
        headers['Idempotency-Key'] = request_key
    if approval is not None:
        headers[HEADER] = approval
    raw = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        raw = canonical(payload)
    req = Request('http://127.0.0.1:' + str(session['port']) + path, data=raw, headers=headers, method=method)
    try:
        # Local lab traffic never follows proxy environment variables or redirects.
        with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=15) as response:
            status, body = response.status, response.read(16385)
    except HTTPError as exc:
        status, body = exc.code, exc.read(16385)
    if len(body) > 16384:
        raise AgentError('HTTP tool response too large')
    return status, strict_json(body)


def _observation(state, event, **values):
    state['observations'].append({'at': int(time.time()), 'event': event, **values})
    state['observations'] = state['observations'][-30:]


def execute(path, session, subject, *, transport=request, now=None):
    """One bounded attempt. Pending operations resume with the same sealed plan/key."""
    state = load_state(path, session, subject)
    if state['status'] in ('completed', 'failed', 'rejected'):
        # Preserve the original observation time. A terminal replay has made no
        # fresh HTTP call and must not be presented as current server state.
        if state['result'] is not None:
            state['result']['observation_source'] = 'cached_receipt'
        return state
    plan = state['plan']
    method, route, payload, key = binding(plan['action'], plan['request_key'])
    now = int(time.time()) if now is None else now
    capability = None
    if method != 'GET':
        decision = state['approval']
        if (decision is None or not decision['approved_at'] <= now < decision['expires_at']):
            state['status'] = 'needs_approval'
            save_state(path, state, session)
            return state
        capability = issue(session['approval_key'], subject, method, route, payload, key,
                           now=decision['approved_at'], ttl=decision['expires_at'] - decision['approved_at'])
    state['attempts'] += 1
    state['status'] = 'pending'
    _observation(state, 'attempt_started', attempt=state['attempts'])
    # Persist before the external effect: a crash resumes this exact intention.
    save_state(path, state, session)

    def call(verb, target, data=None, idem='', receipt=None):
        code, response = transport(session, subject, verb, target, data, idem, receipt, plan['correlation_id'])
        _observation(state, 'tool_response', method=verb, path=target, http_status=code)
        return code, response

    def matches_observation(observed, target):
        if not isinstance(observed, dict) or observed.get('id') != target.rsplit('/', 1)[-1]:
            return False
        if method == 'POST' and any(observed.get(k) != v for k, v in payload.items()):
            return False
        return True

    try:
        target = route
        if method == 'POST':
            operation = hashlib.sha256(('POST /bookings\0' + subject + '\0' + key).encode()).hexdigest()
            target = '/bookings/' + operation
        if method != 'GET' and state['attempts'] > 1:
            code, observed = call('GET', target)
            if code == 200 and matches_observation(observed, target) and (
                    method == 'POST' and observed.get('status') in ('CONFIRMED', 'CANCELLED')
                    or method == 'DELETE' and observed.get('status') == 'CANCELLED'):
                state['status'], state['result'] = 'completed', {
                    'http_status': code, 'body': observed, 'reconciled': True,
                    'observed_at': int(time.time()), 'observation_source': 'http'}
                save_state(path, state, session)
                return state
            if code not in (200, 404):
                state['status'] = 'pending' if code >= 500 or code == 429 else 'failed'
                state['result'] = {'http_status': code, 'body': observed,
                                   'observed_at': int(time.time()), 'observation_source': 'http'}
                save_state(path, state, session)
                return state
        code, response = call(method, route, payload, key, capability)
        state['result'] = {'http_status': code, 'body': response, 'reconciled': False,
                           'observed_at': int(time.time()), 'observation_source': 'http'}
        if 200 <= code < 300:
            if method == 'GET':
                if code != 200 or not isinstance(response, dict) or not isinstance(response.get('bookings'), list):
                    raise AgentError('Unexpected list response')
                state['status'] = 'completed'
            else:
                observed_code, observed = call('GET', target)
                expected = ('CONFIRMED', 'CANCELLED') if method == 'POST' else ('CANCELLED',)
                if observed_code == 200 and matches_observation(observed, target) and observed.get('status') in expected:
                    state['result']['observed'] = observed
                    state['status'] = 'completed'
                else:
                    state['status'] = 'pending'
        elif code >= 500 or code == 429:
            state['status'] = 'pending'
        elif code == 403 and isinstance(response, dict) and response.get('error') in (
                'approval_required', 'approval_invalid', 'approval_required_or_invalid'):
            state['status'] = 'needs_approval'
        else:
            state['status'] = 'failed'
    except (OSError, URLError, TimeoutError):
        # Do not assume a timeout means failure; a remote commit may have happened.
        _observation(state, 'ambiguous_transport_failure')
        state['status'] = 'pending'
    except AgentError:
        _observation(state, 'invalid_tool_response')
        state['status'] = 'pending'
    save_state(path, state, session)
    return state


def public_state(state):
    return {key: value for key, value in state.items() if key != 'integrity'}


def exit_code(state):
    return 0 if state['status'] == 'completed' else 3 if state['status'] == 'pending' else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', required=True, type=Path)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--subject', choices=['agent-a', 'agent-b'], default='agent-a')
    parser.add_argument('--goal')
    parser.add_argument('--planner', choices=['rules', 'bedrock'], default='rules')
    parser.add_argument('--model-id')
    parser.add_argument('--region')
    parser.add_argument('command', choices=['plan', 'approve', 'reject', 'execute', 'run', 'inspect'], nargs='?', default='run')
    args = parser.parse_args(argv)
    try:
        session = session_from(args.session)
        if args.state.resolve() == args.session.resolve():
            raise AgentError('State and session paths must differ')
        with state_lock(args.state):
            if args.command in ('plan', 'run'):
                if not args.goal:
                    raise AgentError('--goal is required for plan/run')
                state = propose(args.state, session, args.subject, args.goal, args.planner, args.model_id, args.region)
                if args.command == 'plan':
                    print(json.dumps(public_state(state), indent=2, ensure_ascii=False))
                    return 0
            else:
                state = load_state(args.state, session, args.subject)
            if args.command == 'inspect':
                print(json.dumps(public_state(state), indent=2, ensure_ascii=False))
                return 0
            if args.command == 'reject':
                state = approve(args.state, session, args.subject, '')
            elif args.command == 'approve' or (args.command == 'run' and state['plan']['action']['action'] != 'list'):
                print(json.dumps(public_state(state), indent=2, ensure_ascii=False), file=sys.stderr)
                print('Revisa acción, sujeto y parámetros de la propuesta. Para cancelar, comprueba el ID con list.\n'
                      'Para autorizar durante 5 minutos escribe:\n'
                      'APROBAR ' + state['plan_digest'] + '\nCualquier otra respuesta rechaza la propuesta.', file=sys.stderr, flush=True)
                if state['attempts'] > 0:
                    print('Ya hubo un intento remoto: retirar autorización detiene nuevos envíos del agente,\n'
                          'pero el servidor puede continuar. Consulta con list; cancelar requiere otra propuesta aprobada.',
                          file=sys.stderr, flush=True)
                confirmation = sys.stdin.readline().rstrip('\r\n')
                state = approve(args.state, session, args.subject, confirmation)
                if args.command == 'approve':
                    print(json.dumps(public_state(state), indent=2, ensure_ascii=False))
                    return 0 if state['status'] == 'approved' else 2
            if args.command in ('execute', 'run') and state['status'] != 'rejected':
                state = execute(args.state, session, args.subject)
            print(json.dumps(public_state(state), indent=2, ensure_ascii=False))
            return exit_code(state)
    except (AgentError, OSError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
