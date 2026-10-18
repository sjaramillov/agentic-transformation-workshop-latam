"""Service tokens stay at explicit endpoints even under hostile proxy/redirect input."""
import ast
from email.message import Message
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPHandler, Request, build_opener
from urllib.response import addinfourl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'booking_lab'))
import http_safety


class SafeServiceTransportTests(unittest.TestCase):
    def intercepted(self, seen, code=200, location=None):
        class CaptureHTTP(HTTPHandler):
            def http_open(self, request):
                seen.append(request)
                headers = Message()
                headers['Content-Type'] = 'application/json'
                if location:
                    headers['Location'] = location
                response = addinfourl(io.BytesIO(b'{}'), headers, request.full_url, code)
                response.msg = 'Test response'
                return response
        return lambda *handlers: build_opener(*handlers, CaptureHTTP())

    def test_hostile_proxy_cannot_receive_payment_or_audit_tokens(self):
        for service in ('payments', 'audit'):
            with self.subTest(service=service):
                seen = []
                request = Request('http://db-lab-123456789a-' + service + ':8080/events',
                                  data=b'{}', headers={'Authorization': 'Bearer fixture-secret'})
                with patch.dict(os.environ, {'http_proxy': 'http://attacker.invalid:54321',
                                             'HTTP_PROXY': 'http://attacker.invalid:54321',
                                             'no_proxy': '', 'NO_PROXY': ''}), \
                        patch.object(http_safety, 'build_opener', side_effect=self.intercepted(seen)):
                    with http_safety.direct_open(request) as response:
                        self.assertEqual(response.status, 200)
                self.assertEqual(len(seen), 1)
                self.assertEqual(seen[0].host, 'db-lab-123456789a-' + service + ':8080')
                self.assertEqual(seen[0].selector, '/events')

    def test_redirects_never_forward_service_credentials(self):
        for status in (301, 302, 303, 307, 308):
            for method in ('GET', 'POST'):
                with self.subTest(status=status, method=method):
                    seen = []
                    request = Request('http://db-lab-123456789a-payments:8080/charge',
                                      data=b'{}' if method == 'POST' else None,
                                      headers={'Authorization': 'Bearer fixture-secret'}, method=method)
                    with patch.object(http_safety, 'build_opener', side_effect=self.intercepted(
                            seen, status, 'http://attacker.invalid/collect')):
                        with self.assertRaises(HTTPError) as caught:
                            http_safety.direct_open(request)
                    self.assertEqual(caught.exception.code, status)
                    caught.exception.close()
                    self.assertEqual(len(seen), 1)
                    self.assertEqual(seen[0].host, 'db-lab-123456789a-payments:8080')

    def test_payment_and_audit_call_sites_use_explicit_safe_transport(self):
        tree = ast.parse((ROOT / 'booking_lab/service.py').read_text())
        self.assertTrue(any(isinstance(node, ast.ImportFrom) and node.module == 'http_safety'
                            and any(name.name == 'direct_open' for name in node.names) for node in tree.body))
        for name in ('payment', 'deliver'):
            function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
            names = [node.func.id for node in ast.walk(function)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
            self.assertIn('direct_open', names)
            self.assertNotIn('urlopen', names)


if __name__ == '__main__':
    unittest.main()
