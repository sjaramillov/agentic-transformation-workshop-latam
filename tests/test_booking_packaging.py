"""Every local API import must reach the explicitly allowlisted container build."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'booking_lab'


class BookingPackagingTests(unittest.TestCase):
    def test_service_imports_are_copied_and_not_dockerignored(self):
        dockerfile = (ROOT / 'Dockerfile').read_text()
        allowed = {line[1:] for line in (ROOT / '.dockerignore').read_text().splitlines() if line.startswith('!')}
        pending = ['service.py', 'audit.py']
        checked = set()
        while pending:
            name = pending.pop()
            if name in checked:
                continue
            checked.add(name)
            self.assertIn(name, allowed)
            self.assertTrue(any(line.startswith('COPY ') and name in line.split()
                                for line in dockerfile.splitlines()), name)
            for node in ast.walk(ast.parse((ROOT / name).read_text())):
                if isinstance(node, ast.ImportFrom) and node.module:
                    local = node.module.split('.')[0] + '.py'
                    if (ROOT / local).exists():
                        pending.append(local)
        self.assertIn('approval.py', checked)


if __name__ == '__main__':
    unittest.main()
