import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lab", ROOT / "scripts/lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "capture.tar.gz"
        self.dest = self.root / "restored"

    def bundle(self, extra=()):
        entries = [("apps/travelcorp-portfolio/exercises/agentstorming/facilitate.py", b"# fixture\n", None)]
        with tarfile.open(self.archive, "w:gz") as archive:
            for name, body, kind in entries + list(extra):
                info = tarfile.TarInfo(name)
                info.size = len(body)
                if kind:
                    info.type = kind
                    info.linkname = "../../outside"
                archive.addfile(info, io.BytesIO(body))
        return lab.digest(self.archive)

    def test_restore_preserves_bytes(self):
        expected = self.bundle()
        result = lab.restore(self.archive, self.dest, expected)
        self.assertEqual(result["entries"], 1)
        self.assertEqual((self.dest / "apps/travelcorp-portfolio/exercises/agentstorming/facilitate.py").read_bytes(), b"# fixture\n")

    def test_wrong_hash_creates_no_destination(self):
        self.bundle()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            lab.restore(self.archive, self.dest, "0" * 64)
        self.assertFalse(self.dest.exists())

    def test_refuses_existing_destination(self):
        expected = self.bundle()
        self.dest.mkdir()
        (self.dest / "keep").write_text("preserve")
        with self.assertRaisesRegex(ValueError, "ya existe"):
            lab.restore(self.archive, self.dest, expected)
        self.assertEqual((self.dest / "keep").read_text(), "preserve")

    def test_rejects_unsafe_members(self):
        cases = [("../escape", None), ("/absolute", None),
                 ("apps/travelcorp-portfolio/../../escape", None),
                 ("unrelated/file", None), ("reports/link", tarfile.SYMTYPE),
                 ("reports/hardlink", tarfile.LNKTYPE), ("reports/fifo", tarfile.FIFOTYPE),
                 ("apps/travelcorp-portfolio/exercises/agentstorming/facilitate.py", None)]
        for name, kind in cases:
            with self.subTest(name=name):
                expected = self.bundle([(name, b"", kind)])
                with self.assertRaises(ValueError):
                    lab.restore(self.archive, self.dest, expected)
                self.assertFalse(self.dest.exists())

    def test_rejects_oversized_archive(self):
        expected = self.bundle()
        previous = lab.MAX_BYTES
        lab.MAX_BYTES = 1
        try:
            with self.assertRaisesRegex(ValueError, "límite"):
                lab.restore(self.archive, self.dest, expected)
        finally:
            lab.MAX_BYTES = previous


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.environment = self.root / "environment"
        self.base = self.environment / "apps/travelcorp-portfolio"
        facilitator = self.base / "exercises/agentstorming/facilitate.py"
        facilitator.parent.mkdir(parents=True)
        facilitator.write_text("# fixture")

    def report(self, path, tier):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"classification": {"tier": tier}}))

    def test_sources_remain_separate_and_no_overwrite(self):
        first = self.environment / "reports/ara/booking-ara-report.json"
        second = self.base / "src/booking-service/services/booking-ara-report.json"
        baseline = self.base / "precomputed-reports/ara/booking-ara-report.json"
        for path, tier in [(first, "captured-1"), (second, "captured-2"), (baseline, "baseline")]:
            self.report(path, tier)
        before = {p: lab.digest(p) for p in (first, second, baseline)}
        out = self.root / "results"
        result = lab.collect(self.environment, out, "captured")
        self.assertEqual(result["files"], 2)
        inventory = json.loads((out / "inventory.json").read_text())
        self.assertEqual({r["classification"]["tier"] for r in inventory["reports"]}, {"captured-1", "captured-2"})
        self.assertFalse(inventory["fresh_analysis"])
        with self.assertRaisesRegex(ValueError, "ya existe"):
            lab.collect(self.environment, out, "captured")
        self.assertEqual(before, {p: lab.digest(p) for p in before})
        self.assertEqual(lab.collect(self.environment, self.root / "baseline", "precomputed")["files"], 1)

    def test_missing_live_reports_never_falls_back(self):
        self.report(self.base / "precomputed-reports/ara/booking-ara-report.json", "baseline")
        with self.assertRaisesRegex(ValueError, "No hay informes"):
            lab.collect(self.environment, self.root / "results", "captured")

    def test_rejects_invalid_json_before_creating_output(self):
        path = self.environment / "reports/ara/booking-ara-report.json"
        self.report(path, "x")
        path.write_text("{broken")
        with self.assertRaises(ValueError):
            lab.collect(self.environment, self.root / "results", "captured")
        self.assertFalse((self.root / "results").exists())

    def test_rejects_non_object_json(self):
        path = self.environment / "reports/ara/booking-ara-report.json"
        self.report(path, "x")
        path.write_text("[]")
        with self.assertRaisesRegex(ValueError, "no es un objeto"):
            lab.collect(self.environment, self.root / "results", "captured")

    def test_rejects_external_symlink(self):
        outside = self.root / "external.json"
        self.report(outside, "private")
        link = self.environment / "reports/ara/booking-ara-report.json"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "fuera del entorno"):
            lab.collect(self.environment, self.root / "results", "captured")




if __name__ == "__main__":
    unittest.main()
