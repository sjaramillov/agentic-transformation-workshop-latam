import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "runtime_files", Path(__file__).resolve().parents[1] / "scripts/container_runtime_files.py")
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)


class RuntimeFilesTests(unittest.TestCase):
    def test_creates_files_without_changing_application(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.php").write_text("<?php echo 'fixture';")
            original = (root / "index.php").read_bytes()
            self.assertEqual(set(RUNTIME.install(root)), set(RUNTIME.FILES))
            self.assertEqual((root / "index.php").read_bytes(), original)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                RUNTIME.install(root)

    def test_requires_php_and_refuses_conflicts_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "index.php"):
                RUNTIME.install(root)
            (root / "index.php").touch()
            (root / "health-live.php").symlink_to(root / "absent")
            with self.assertRaisesRegex(ValueError, "overwrite"):
                RUNTIME.install(root)
            self.assertFalse((root / ".dockerignore").exists())
