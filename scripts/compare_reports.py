#!/usr/bin/env python3
"""Compare verified ARA/MODA reports by question without rewriting evaluator judgments."""
import argparse
import csv
import json
from pathlib import Path
from verify_reports import verify


def questions(document, kind):
    result = {}
    for group in ('findings', 'evaluations'):
        for item in document.get(group, []):
            ident = item['question_id']
            if ident in result:
                raise ValueError('Duplicate question: '+ident)
            state = (item.get('ara_metadata', {}).get('native_severity', item.get('severity'))
                     if group == 'findings' else item.get('status', 'unspecified'))
            result[ident] = {'status': state, 'title': item.get('title', ''),
                             'score': item.get('mod_metadata', {}).get('internal_score')}
    return result


def compare(before, after, kind, expect_questions=None):
    paths = [Path(before), Path(after)]
    checks = [verify(p, kind, expect_questions) for p in paths]
    if not all(c['valid_bundle_and_counts'] for c in checks):
        raise ValueError(json.dumps(checks, ensure_ascii=False))
    documents = [json.loads(p.read_text()) for p in paths]
    a, b = [questions(d, kind) for d in documents]
    rows = []
    for ident in sorted(a.keys() | b.keys()):
        previous, current = a.get(ident, {}), b.get(ident, {})
        old, new = previous.get('status', 'not_reported'), current.get('status', 'not_reported')
        rows.append({'question_id': ident, 'title': current.get('title', previous.get('title', '')),
                     'before': old, 'after': new, 'changed': old != new,
                     'score_before': previous.get('score'), 'score_after': current.get('score')})
    return {'kind': kind, 'before_classification': documents[0]['classification'],
            'after_classification': documents[1]['classification'],
            'overall_score_before': documents[0].get('overall_score'),
            'overall_score_after': documents[1].get('overall_score'),
            'same_question_set': a.keys() == b.keys(), 'questions': rows,
            'report_bundle_verification': checks,
            'interpretation': 'Evaluator judgments; scope, source changes and runtime proof require separate review.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('before', type=Path)
    p.add_argument('after', type=Path)
    p.add_argument('--kind', choices=('ara', 'mod'), required=True)
    p.add_argument('--expect-questions', type=int)
    p.add_argument('--output', type=Path, required=True, help='New directory; existing evidence is preserved')
    args = p.parse_args()
    result = compare(args.before, args.after, args.kind, args.expect_questions)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'comparison.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    with (args.output/'comparison.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=('question_id','title','before','after','changed','score_before','score_after'))
        writer.writeheader()
        writer.writerows(result['questions'])
    print(json.dumps({'same_question_set': result['same_question_set'],
                      'questions': len(result['questions']),
                      'changed': sum(r['changed'] for r in result['questions'])}))


if __name__ == '__main__':
    main()
