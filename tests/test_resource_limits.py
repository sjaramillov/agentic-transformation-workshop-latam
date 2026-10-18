"""Docker info capability spelling and strict boolean admission."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'booking_lab'))
spec = importlib.util.spec_from_file_location('limits_lab_runner', ROOT / 'booking_lab/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ResourceLimitTests(unittest.TestCase):
    def test_correct_docker_capabilities_enable_limits(self):
        info = {'MemoryLimit': True, 'CpuCfsQuota': True, 'PidsLimit': True,
                'HttpProxy': 'private-value-must-not-enter-evidence'}
        capabilities, options = runner.resource_limits(info)
        self.assertEqual(capabilities, {'MemoryLimit': True, 'CpuCfsQuota': True, 'PidsLimit': True})
        self.assertEqual(options, ['--memory', '256m', '--cpus', '1', '--pids-limit', '128'])
        self.assertNotIn('HttpProxy', capabilities)

    def test_false_or_missing_capability_does_not_enable_limits(self):
        complete = {'MemoryLimit': True, 'CpuCfsQuota': True, 'PidsLimit': True}
        for name in complete:
            with self.subTest(name=name):
                capabilities, options = runner.resource_limits({**complete, name: False})
                self.assertFalse(capabilities[name])
                self.assertEqual(options, [])
                capabilities, options = runner.resource_limits({key: value for key, value in complete.items() if key != name})
                self.assertIsNone(capabilities[name])
                self.assertEqual(options, [])
        capabilities, options = runner.resource_limits({'MemoryLimit': True, 'CPUCfsQuota': True, 'PidsLimit': True})
        self.assertIsNone(capabilities['CpuCfsQuota'])
        self.assertEqual(options, [])

    def test_truthy_non_boolean_values_are_unknown_not_support(self):
        complete = {'MemoryLimit': True, 'CpuCfsQuota': True, 'PidsLimit': True}
        for name in complete:
            for value in ('true', 'false', 1, 0, [], {}):
                with self.subTest(name=name, value=value):
                    capabilities, options = runner.resource_limits({**complete, name: value})
                    self.assertIsNone(capabilities[name])
                    self.assertEqual(options, [])


if __name__ == '__main__':
    unittest.main()
