"""Original MIT lab issuer/verifier. Symmetric JWT is confined to this local lab."""
import base64
import hashlib
import hmac
import json
import math
import re
import time


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def encode(key, subject='agent-a', scope='bookings:read bookings:write bookings:cancel', **overrides):
    now = int(time.time())
    payload = dict(iss='booking-lab', aud='booking-api', sub=subject, scope=scope,
                   iat=now, nbf=now-1, exp=now+300)
    payload.update(overrides)
    head = b64(b'{"alg":"HS256","typ":"JWT"}')
    body = b64(json.dumps(payload, separators=(',', ':')).encode())
    sig = b64(hmac.new(key.encode(), (head+'.'+body).encode(), hashlib.sha256).digest())
    return head+'.'+body+'.'+sig


def verify(token, key, required):
    try:
        if not isinstance(key, str) or len(key) < 32 or len(token) > 4096:
            raise ValueError()
        head, body, signature = token.split('.')
        expected = b64(hmac.new(key.encode(), (head+'.'+body).encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        decode = lambda s: json.loads(base64.urlsafe_b64decode(s+'='*(-len(s) % 4)))
        if decode(head) != {'alg': 'HS256', 'typ': 'JWT'}:
            raise ValueError()
        p = decode(body)
        now = time.time()
        # JSON accepts NaN/Infinity in Python; reject non-finite and boolean dates.
        for claim in ('exp', 'nbf', 'iat'):
            value = p[claim]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError()
        if (p['iss'] != 'booking-lab' or p['aud'] != 'booking-api'
                or p['exp'] <= now or p['nbf'] > now or p['iat'] > now
                or p['exp'] <= p['iat'] or p['exp'] - p['iat'] > 300
                or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', p['sub'])):
            raise ValueError()
        if required not in p['scope'].split():
            return None, 403
        return p['sub'], 200
    except (ValueError, KeyError, TypeError, AttributeError):
        return None, 401
