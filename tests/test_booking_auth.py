"""Security boundary tests for the original local issuer; DB tests run in Docker."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('lab_auth',Path(__file__).resolve().parents[1]/'booking_lab/auth.py')
auth=importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class AuthenticationTests(unittest.TestCase):
    def test_signed_identity_and_scopes(self):
        key='k'*64
        self.assertEqual(auth.verify(auth.encode(key,'agent-b'),key,'bookings:write'),('agent-b',200))
        self.assertEqual(auth.verify(auth.encode(key,scope='bookings:read'),key,'bookings:write'),(None,403))

    def test_invalid_claims_and_signature_rejected(self):
        key='k'*64
        for overrides in ({'exp':0},{'nbf':9999999999},{'iat':9999999999},{'iss':'other'},{'aud':'other'},{'sub':'../escape'}):
            with self.subTest(overrides=overrides):
                self.assertEqual(auth.verify(auth.encode(key,**overrides),key,'bookings:write'),(None,401))
        self.assertEqual(auth.verify(auth.encode('x'*64),key,'bookings:write'),(None,401))
        for token in ('','a.b.c','a'*5000):
            self.assertEqual(auth.verify(token,key,'bookings:write'),(None,401))
