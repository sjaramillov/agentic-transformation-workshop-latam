import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_reports import compare, questions


class ComparisonTests(unittest.TestCase):
    def test_pass_is_not_missing_and_duplicate_is_rejected(self):
        d={'findings': [], 'evaluations': [{'question_id':'Q1','status':'pass'}]}
        self.assertEqual(questions(d,'ara')['Q1']['status'],'pass')
        d['evaluations'].append(d['evaluations'][0])
        with self.assertRaises(ValueError): questions(d,'ara')

    def test_real_ara_comparison_preserves_safety_qualifier(self):
        root=Path(__file__).resolve().parents[1]/'evidence/mit'
        result=compare(root/'before/ara/booking-mit-ara-report.json',
                       root/'after/ara/booking-mit-ara-report.json','ara',43)
        self.assertTrue(result['same_question_set'])
        changes={r['question_id']:(r['before'],r['after']) for r in result['questions'] if r['changed']}
        self.assertEqual(changes,{'AUTH-Q3':('RISK-SAFETY','pass'),'AUTH-Q6':('BLOCKER','pass'),
                                  'API-Q6':('not_evaluated_extended','pass'),
                                  'STATE-Q7':('not_evaluated_extended','pass')})
        self.assertEqual(result['after_classification']['sub_qualifier'],'Pilot-Ready (Safety Concerns)')

    def test_missing_bundle_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'report.json';p.write_text(json.dumps({}))
            with self.assertRaises(ValueError): compare(p,p,'mod')
