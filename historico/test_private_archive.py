"""Optional historical capture test; excluded from the public workshop suite."""
import os
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import lab

@unittest.skipUnless(os.environ.get("WORKSHOP_ARCHIVE"), "E2E requiere la captura privada WORKSHOP_ARCHIVE")
class RealArchiveE2E(unittest.TestCase):
    def test_clean_restore_rehearse_and_collect(self):
        with tempfile.TemporaryDirectory(prefix="lab-e2e-") as temp:
            root = Path(temp)
            environment = root / "environment"
            lab.restore(os.environ["WORKSHOP_ARCHIVE"], environment)
            self.assertTrue(lab.doctor(environment)["ok"])
            captured_manifest = lab.digest(environment / "apps/travelcorp-portfolio/run-manifest.json")
            output = root / "practice"
            result = lab.rehearse(environment, output)
            self.assertEqual(result["candidate"], "rebooking")
            self.assertEqual(result["autonomy"], "P")
            self.assertEqual(len(result["generated"]), 8)
            self.assertFalse(result["cloud_analysis_executed"])
            self.assertEqual(captured_manifest, lab.digest(environment / "apps/travelcorp-portfolio/run-manifest.json"))
            with self.assertRaisesRegex(ValueError, "ya existe"):
                lab.rehearse(environment, output)
            for origin in ("captured", "precomputed"):
                result = lab.collect(environment, root / origin, origin)
                self.assertGreater(result["files"], 0)
                inventory = json.loads((root / origin / "inventory.json").read_text())
                for entry in inventory["reports"]:
                    self.assertEqual(lab.digest(root / origin / entry["path"]), entry["sha256"])
            # The archive's staging branch is evidence; never silently normalize it.
            repo = environment / "apps/travelcorp-portfolio/src/booking-service"
            branch = lab.run(["git", "-C", str(repo), "branch", "--show-current"])
            self.assertTrue(branch.stdout.strip().startswith("atx-result-staging-"))

