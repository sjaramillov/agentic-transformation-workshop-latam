"""Public preparation works from a clean tracked source, without event archives."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_workshop',ROOT/'scripts/workshop.py')
workshop=importlib.util.module_from_spec(spec)
spec.loader.exec_module(workshop)


class WorkshopTests(unittest.TestCase):
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

    def test_main_docs_use_public_resources(self):
        for name in ('README.md','INICIO_RAPIDO.md','GUIA_REPLICACION.md','EJECUCION_AWS.md','CLOUDSHELL.md','RECURSOS.md'):
            text=(ROOT/name).read_text()
            self.assertNotIn('WORKSHOP_ARCHIVE',text,name)
            self.assertNotIn('apps/travelcorp-portfolio',text,name)
            self.assertNotIn('agentic-workshop-materials-',text,name)
