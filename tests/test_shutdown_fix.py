import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    'shutdown_fix', Path(__file__).resolve().parents[1] / 'scripts/fix_shutdown_order.py')
FIX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIX)


class ShutdownFixTests(unittest.TestCase):
    def test_replaces_only_observed_tail_and_repeats_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.php'
            path.write_text('<?php\nregister_shutdown_function(function() { /* UPDATE idempotency_keys */ });\n' + FIX.OLD)
            result = FIX.fix(path)
            self.assertTrue(result['changed'])
            self.assertNotEqual(result['before_sha256'], result['after_sha256'])
            self.assertFalse(FIX.fix(path)['changed'])

    def test_unknown_source_and_symlinks_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.php'
            path.write_text('<?php\n' + FIX.OLD)
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                FIX.fix(path)
            self.assertEqual(path.read_bytes(), before)
            link = Path(directory) / 'link.php'
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                FIX.fix(link)
