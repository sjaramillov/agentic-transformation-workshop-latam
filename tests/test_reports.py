import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "verify_reports", Path(__file__).resolve().parents[1] / "scripts/verify_reports.py")
REPORTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORTS)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "example-report.json"
        self.data = {
            "classification": {"tier": "Example", "high_count": 1, "medium_count": 0,
                               "low_count": 0, "blocker_count": 1, "risk_safety_count": 0,
                               "risk_quality_count": 0, "info_count": 0,
                               "classification_consistency_check": "consistent"},
            "findings": [{"question_id": "A1", "severity": "High",
                          "ara_metadata": {"native_severity": "BLOCKER"}}],
            "evaluations": [{"question_id": "A2", "status": "pass"}],
        }
        for suffix, content in [(".md", "Example"), (".html", "<p>Example</p>"),
                                (".metadata.json", "{}")]:
            self.path.with_suffix(suffix).write_text(content)

    def check(self, data=None, kind="ara", questions=2):
        self.path.write_text(json.dumps(self.data if data is None else data))
        return REPORTS.verify(self.path, kind, questions)

    def test_valid_bundle_does_not_claim_runtime(self):
        result = self.check()
        self.assertTrue(result["valid_bundle_and_counts"], result)
        self.assertEqual(len(result["artifact_sha256"]), 4)
        self.assertFalse(result["runtime_validated"])
        self.assertFalse(result["rubric_judgments_independently_verified"])
        self.assertTrue(self.check(kind="mod")["valid_bundle_and_counts"])

    def test_invalid_counts_and_declared_consistency(self):
        for key, value in [("high_count", 9), ("high_count", True),
                           ("blocker_count", 0), ("classification_consistency_check", "inconsistent")]:
            with self.subTest(key=key, value=value):
                data = copy.deepcopy(self.data)
                data["classification"][key] = value
                self.assertFalse(self.check(data)["valid_bundle_and_counts"])
        data = copy.deepcopy(self.data)
        data["counts"] = {"high": 1, "medium": 0, "low": 0, "total": 9}
        self.assertFalse(self.check(data)["valid_bundle_and_counts"])

    def test_malformed_fields_rejected_without_crash(self):
        for key in ("severity", "question_id", "ara_metadata"):
            for value in ([], {}, None, 42):
                with self.subTest(key=key, value=value):
                    data = copy.deepcopy(self.data)
                    data["findings"][0][key] = value
                    self.assertFalse(self.check(data)["valid_bundle_and_counts"])
        data = copy.deepcopy(self.data)
        data["findings"][0]["ara_metadata"]["native_severity"] = []
        self.assertFalse(self.check(data)["valid_bundle_and_counts"])

    def test_coverage_and_duplicates(self):
        self.assertFalse(self.check(questions=3)["valid_bundle_and_counts"])
        data = copy.deepcopy(self.data)
        data["evaluations"][0]["question_id"] = "A1"
        self.assertFalse(self.check(data)["valid_bundle_and_counts"])
        data["findings"].append(copy.deepcopy(data["findings"][0]))
        self.assertFalse(self.check(data)["valid_bundle_and_counts"])

    def test_missing_empty_invalid_and_symlink_artifacts(self):
        artifact = self.path.with_suffix(".md")
        artifact.unlink()
        self.assertFalse(self.check()["valid_bundle_and_counts"])
        artifact.write_text("")
        self.assertFalse(self.check()["valid_bundle_and_counts"])
        artifact.unlink()
        artifact.symlink_to(self.path)
        self.assertFalse(self.check()["valid_bundle_and_counts"])
        artifact.unlink()
        artifact.write_text("Example")
        self.path.with_suffix(".metadata.json").write_text("[]")
        self.assertFalse(self.check()["valid_bundle_and_counts"])


if __name__ == "__main__":
    unittest.main()
