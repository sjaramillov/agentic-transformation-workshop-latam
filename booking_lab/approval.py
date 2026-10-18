"""Short-lived, request-bound approval for the original MIT workshop.

The local operator is the issuer. This is an educational capability boundary,
not an identity provider or independent attestation of a human's identity.
"""
import base64
import hashlib
import hmac
import json
import re
import time


HEADER = 'X-Booking-Approval'
MAX_TTL = 300


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def _key(key):
    if not isinstance(key, str) or len(key) < 32:
        raise ValueError('Approval key must contain at least 32 characters')
    return key.encode()


def _binding(principal, method, path, payload, request_key):
    if not isinstance(principal, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', principal):
        raise ValueError('Invalid approval subject')
    if method == 'POST':
        if (path != '/bookings' or not isinstance(request_key, str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', request_key)
                or not isinstance(payload, dict) or set(payload) != {'itinerary', 'amount'}
                or type(payload['amount']) is not int or not 0 < payload['amount'] <= 10000000
                or not isinstance(payload['itinerary'], str)
                or not re.fullmatch(r'[A-Z]{3}-[A-Z]{3}', payload['itinerary'])):
            raise ValueError('Invalid approved create request')
    elif method == 'DELETE':
        if (not isinstance(path, str) or not re.fullmatch(r'/bookings/[a-f0-9]{64}', path)
                or payload is not None or request_key != ''):
            raise ValueError('Invalid approved cancellation')
    else:
        raise ValueError('Only create and cancel need approval')
    return {'v': 1, 'subject': principal, 'method': method, 'path': path,
            'payload_sha256': hashlib.sha256(canonical(payload)).hexdigest(),
            'request_key': request_key}


def issue(key, principal, method, path, payload=None, request_key='', *, now=None, ttl=300):
    """Issue a capability bound to exactly one subject/action/payload/key."""
    now = int(time.time()) if now is None else now
    if type(now) is not int or type(ttl) is not int or not 0 < ttl <= MAX_TTL:
        raise ValueError('Invalid approval lifetime')
    claims = {**_binding(principal, method, path, payload, request_key),
              'issued_at': now, 'expires_at': now + ttl}
    encoded = base64.urlsafe_b64encode(canonical(claims)).rstrip(b'=')
    signature = hmac.new(_key(key), b'booking-approval-v1.' + encoded, hashlib.sha256).hexdigest()
    return encoded.decode() + '.' + signature


def verify(token, key, principal, method, path, payload=None, request_key='', *, now=None):
    """Return False on missing, expired, malformed, or differently bound approval."""
    try:
        now = int(time.time()) if now is None else now
        if type(now) is not int or not isinstance(token, str) or len(token) > 4096:
            return False
        encoded, signature = token.split('.')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', encoded) or not re.fullmatch(r'[a-f0-9]{64}', signature):
            return False
        expected = hmac.new(_key(key), b'booking-approval-v1.' + encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        claims = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))
        binding = _binding(principal, method, path, payload, request_key)
        if set(claims) != set(binding) | {'issued_at', 'expires_at'}:
            return False
        if any(claims[k] != v for k, v in binding.items()):
            return False
        issued, expires = claims['issued_at'], claims['expires_at']
        return (type(issued) is int and type(expires) is int
                and issued <= now < expires and 0 < expires - issued <= MAX_TTL)
    except (ValueError, TypeError, KeyError, UnicodeError):
        return False
