import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('cleanup_lab',Path(__file__).resolve().parents[1]/'scripts/cleanup_lab.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


class CleanupTests(unittest.TestCase):
    def test_only_named_stopped_containers_and_never_volumes(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'db-lab-0123456789';p.mkdir();review=p/'review.json';review.write_text(json.dumps({'prefix':p.name}))
            def command(args,**kwargs):
                return subprocess.CompletedProcess(args,0,'false\n' if args[1]=='inspect' else 'log\n','')
            with patch.object(mod.subprocess,'run',side_effect=command) as run:
                self.assertFalse(mod.cleanup(review)['removed'])
                self.assertTrue(all(c.args[0][1]=='inspect' for c in run.call_args_list))
                run.reset_mock();result=mod.cleanup(review,True)
                self.assertEqual(len(result['containers']),6)
                for call in run.call_args_list:
                    args=call.args[0]
                    self.assertNotIn('-f',args if args[1]!='inspect' else [])
                    self.assertNotIn('-v',args)
                    self.assertTrue(args[-1].startswith(p.name+'-'))
                self.assertTrue(result['volumes_preserved'])

    def test_running_or_invalid_lab_never_removed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'db-lab-0123456789';p.mkdir();review=p/'review.json';review.write_text(json.dumps({'prefix':p.name}))
            with patch.object(mod.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'true\n','')) as run:
                with self.assertRaises(ValueError):mod.cleanup(review,True)
                self.assertEqual(run.call_count,1)
            review.write_text(json.dumps({'prefix':'some-user-container'}))
            with self.assertRaises(ValueError):mod.cleanup(review,True)
