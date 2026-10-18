"""Public preparation works from a clean tracked source, without event archives."""
import importlib.util
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_workshop',ROOT/'scripts/workshop.py')
workshop=importlib.util.module_from_spec(spec)
spec.loader.exec_module(workshop)


class WorkshopTests(unittest.TestCase):
    def repository_fixture(self, root):
        """Commit current public inputs to an isolated repository before preparing."""
        root.mkdir()
        subprocess.run(['git','init','-q','-b','main',str(root)],check=True)
        for key,value in [('user.name','Workshop tests'),('user.email','tests@example.invalid')]:
            subprocess.run(['git','-C',str(root),'config',key,value],check=True)
        for folder in ('workshop/contexts','workshop/templates'):
            shutil.copytree(ROOT/folder,root/folder)
        shutil.copyfile(ROOT/'workshop/scenario.json',root/'workshop/scenario.json')
        (root/'booking_lab').mkdir()
        (root/'booking_lab/run.py').write_text('# public fixture v1\n')
        (root/'LICENSE').write_text('MIT fixture\n')
        return self.commit_fixture(root)

    @staticmethod
    def commit_fixture(root):
        subprocess.run(['git','-C',str(root),'add','.'],check=True)
        subprocess.run(['git','-C',str(root),'commit','-qm','Public fixture'],check=True)
        return subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()

    def test_public_materials_and_isolated_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'practice'
            result=workshop.prepare(out)
            self.assertFalse(result['cloud_analysis_executed'])
            for kind in ('ara','moda'):
                source=out/'sources'/kind/'booking-mit'
                sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
                self.assertEqual(sha,result['analysis_commit'])
                self.assertTrue((source/'booking_lab/run.py').is_file())
                self.assertTrue((source/'LICENSE').is_file())
                self.assertFalse((source/'resources').exists())
                self.assertEqual(subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True),'')
            for step in ('A-eventstorming','B-opportunities','C-workflow'):
                self.assertTrue(json.loads((out/(step+'.json')).read_text()))
            with self.assertRaisesRegex(ValueError,'ya existe'):
                workshop.prepare(out)

    def test_value_traceability_and_ai_dlc_handoffs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            sha=self.repository_fixture(root)
            out=Path(temp)/'practice'
            with patch.object(workshop,'ROOT',root):
                manifest=workshop.prepare(out)
            self.assertEqual(manifest['public_commit'],sha)
            self.assertEqual(manifest['preparer_sha256'],hashlib.sha256((ROOT/'scripts/workshop.py').read_bytes()).hexdigest())
            self.assertTrue(manifest['value_and_ai_dlc_available'])
            self.assertFalse(manifest['human_decisions_approved'])
            value=json.loads((out/'0-value.json').read_text())
            self.assertEqual(value['status'],'illustrative_not_measured')
            self.assertEqual(value['decision'],'requires_human_review')
            self.assertIn('deterministic-form',[a['id'] for a in value['alternatives']])
            with (out/'G-traceability.csv').open(newline='') as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual([r['requirement_id'] for r in rows],['R1','R2','R3','R4','R5'])
            self.assertTrue(all(r['business_metric'] and r['business_measurement'] and r['acceptance_test'] for r in rows))
            for phase in ('inception','construction','operations'):
                handoff=json.loads((out/'ai-dlc'/f'{phase}.json').read_text())
                self.assertEqual(handoff['public_commit'],sha)
                self.assertEqual(handoff['phase'],phase)
                self.assertEqual(handoff['status'],'requires_human_review')
                self.assertTrue(handoff['owners'])
                self.assertTrue(handoff['exit_evidence'])
                for name in handoff['inputs']:
                    self.assertTrue((out/name).is_file(),name)
            self.assertIn('Pendiente',(out/'ai-dlc/decisions.md').read_text())
            for name,digest in manifest['artifact_sha256'].items():
                self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),digest,name)
            for name,digest in manifest['input_sha256'].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest,name)

    def test_revision_pins_scenario_context_templates_and_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            first=self.repository_fixture(root)
            original=json.loads((root/'workshop/scenario.json').read_text())
            original_context=(root/'workshop/contexts/ara.txt').read_bytes()
            original_template=(root/'workshop/templates/value.md').read_bytes()
            changed=json.loads(json.dumps(original))
            changed['actors']=['later actor']
            changed['value_case']['hypothesis']='Later committed value hypothesis'
            changed['ai_dlc']['inception']['owners']=['later product owner']
            (root/'workshop/scenario.json').write_text(json.dumps(changed))
            (root/'workshop/contexts/ara.txt').write_text('later committed context\n')
            (root/'workshop/templates/value.md').write_text('later committed template\n')
            (root/'booking_lab/run.py').write_text('# public fixture v2\n')
            second=self.commit_fixture(root)
            # Malformed worktree copies must have no influence on either revision.
            (root/'workshop/scenario.json').write_text('not JSON, not committed')
            (root/'workshop/contexts/ara.txt').write_text('uncommitted context')
            (root/'workshop/templates/value.md').write_text('uncommitted template')
            out=Path(temp)/'first'
            later=Path(temp)/'second'
            with patch.object(workshop,'ROOT',root):
                manifest=workshop.prepare(out,first)
                later_manifest=workshop.prepare(later,second)
            self.assertEqual(json.loads((out/'A-eventstorming.json').read_text())['actors'],original['actors'])
            self.assertEqual((out/'contexts/ara.txt').read_bytes(),original_context)
            self.assertEqual((out/'0-value-worksheet.md').read_bytes(),original_template)
            self.assertEqual(json.loads((out/'0-value.json').read_text())['hypothesis'],original['value_case']['hypothesis'])
            self.assertEqual(json.loads((out/'ai-dlc/inception.json').read_text())['owners'],original['ai_dlc']['inception']['owners'])
            self.assertEqual((out/'sources/ara/booking-mit/booking_lab/run.py').read_text(),'# public fixture v1\n')
            self.assertEqual(json.loads((later/'A-eventstorming.json').read_text())['actors'],['later actor'])
            self.assertEqual((later/'contexts/ara.txt').read_text(),'later committed context\n')
            self.assertEqual((later/'0-value-worksheet.md').read_text(),'later committed template\n')
            self.assertEqual(json.loads((later/'0-value.json').read_text())['hypothesis'],'Later committed value hypothesis')
            self.assertEqual(json.loads((later/'ai-dlc/inception.json').read_text())['owners'],['later product owner'])
            self.assertNotEqual(manifest['input_sha256'],later_manifest['input_sha256'])

    def test_historical_revision_does_not_borrow_new_value_material(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            self.repository_fixture(root)
            scenario=json.loads((root/'workshop/scenario.json').read_text())
            for name in ('value_case','traceability','ai_dlc'):
                del scenario[name]
            (root/'workshop/scenario.json').write_text(json.dumps(scenario))
            sha=self.commit_fixture(root)
            out=Path(temp)/'practice'
            with patch.object(workshop,'ROOT',root):
                manifest=workshop.prepare(out,sha)
            self.assertFalse(manifest['value_and_ai_dlc_available'])
            self.assertFalse((out/'0-value.json').exists())
            self.assertFalse((out/'ai-dlc').exists())
            self.assertTrue((out/'A-eventstorming.json').is_file())

    def test_missing_committed_template_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            self.repository_fixture(root)
            (root/'workshop/templates/value.md').unlink()
            sha=self.commit_fixture(root)
            out=Path(temp)/'practice'
            with patch.object(workshop,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'faltan sus plantillas'):
                    workshop.prepare(out,sha)
            self.assertFalse(out.exists())

    def test_business_estimate_is_consistent_and_labeled_illustrative(self):
        scenario=json.loads((ROOT/'workshop/scenario.json').read_text())
        measurement=scenario['value_case']['measurement']
        expected=measurement['monthly_cases']['value']*(measurement['baseline']['value']-measurement['target']['value'])
        self.assertEqual(measurement['illustrative_gross_time_saved']['value'],expected)
        self.assertEqual(measurement['illustrative_gross_time_saved']['status'],'illustrative_not_measured')
        self.assertIsNone(scenario['value_case']['effort_and_cost']['model_and_runtime_cost'])
        runtime=(ROOT/'booking_lab/run.py').read_text()
        for row in scenario['traceability']:
            for test in row['acceptance_test'].split('; '):
                self.assertIn(test,runtime,test)

    def test_main_docs_use_public_resources(self):
        for name in ('README.md','INICIO_RAPIDO.md','GUIA_REPLICACION.md','EJECUCION_AWS.md','CLOUDSHELL.md','RECURSOS.md'):
            text=(ROOT/name).read_text()
            self.assertNotIn('WORKSHOP_ARCHIVE',text,name)
            self.assertNotIn('apps/travelcorp-portfolio',text,name)
            self.assertNotIn('agentic-workshop-materials-',text,name)
