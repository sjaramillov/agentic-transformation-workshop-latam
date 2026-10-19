"""The browser and local lesson must agree at every step, including exports."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from build_site import browser_course
from discovery import Lesson, Session, encoded


@unittest.skipUnless(shutil.which('node'), 'Node is required for browser-engine parity (mandatory in web CI)')
class WebEngineTests(unittest.TestCase):
    def node(self, source, payload):
        result = subprocess.run(['node', '-e', source], input=json.dumps(payload), text=True,
                                cwd=ROOT, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_every_view_transition_and_export_matches_python(self):
        lesson = Lesson.local()
        paths = []
        for mode in ('recommended', 'alternative', 'mixed'):
            state = lesson.initial()
            snapshots = []
            for i, step in enumerate(lesson.steps):
                snapshots.append({'state': state, 'view': lesson.view(state), 'summary': lesson.summary(state).decode()})
                wanted = mode == 'recommended' or (mode == 'mixed' and i % 2 == 0)
                choice = next(c for c in step['choices'] if c['recommended'] == wanted)
                state = lesson.answer(state, i, choice['id'])
                snapshots.append({'state': state, 'view': lesson.view(state), 'summary': lesson.summary(state).decode()})
                state = lesson.advance(state, i + 1)
            snapshots.append({'state': state, 'view': lesson.view(state), 'summary': lesson.summary(state).decode()})
            paths.append(snapshots)
        result = self.node("""
const fs=require('node:fs'), assert=require('node:assert/strict');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const engine=require('./workshop/web/engine.js').create(input.course);
let count=0, final;
for(const path of input.paths){
  let state=engine.initial();
  for(let i=0;i<path.length;i++){
    const expected=path[i];
    assert.deepEqual(state,expected.state);
    assert.deepEqual(engine.view(state),expected.view);
    assert.equal(engine.summary(state),expected.summary);
    count++;
    if(i+1<path.length){
      const next=path[i+1].state;
      if(state.feedback) state=engine.advance(state,state.answers.length);
      else state=engine.answer(state,state.answers.length,next.answers.at(-1).choice);
    }
  }
  final=state;
}
process.stdout.write(JSON.stringify({count,state:final,ara:engine.context(final,'ara'),moda:engine.context(final,'moda')}));
""", {'course': browser_course(), 'paths': paths})
        self.assertEqual(result['count'], 129)
        handoff = lesson.handoff(result['state'])
        for kind in ('ara', 'moda'):
            self.assertEqual(result[kind], handoff[f'contexts/{kind}.txt'].decode())
        # A web export alone can resume the original local facilitator.
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory/'session.json').write_bytes(encoded(result['state']))
            session = Session(directory, lesson)
            self.assertTrue(lesson.complete(session.state))
            self.assertEqual((directory/'contexts/ara.txt').read_text(), result['ara'])

    def test_invalid_states_and_out_of_order_actions_are_rejected(self):
        lesson = Lesson.local()
        initial = lesson.initial()
        invalid = [None, [], {}, {**initial, 'feedback': True}, {**initial, 'feedback': 1},
                   {**initial, 'answers': [{'step':'a2','choice':'explore'}]},
                   {**initial, 'answers': [{'step':'a1','choice':'unknown'}]},
                   {**initial, 'material_sha256': {**initial['material_sha256'], 'extra': 'x'}}]
        for key in initial['material_sha256']:
            state = copy.deepcopy(initial)
            state['material_sha256'][key] = 'different'
            invalid.append(state)
        result = self.node("""
const fs=require('node:fs'), assert=require('node:assert/strict');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const engine=require('./workshop/web/engine.js').create(input.course), initial=engine.initial();
for(const state of input.invalid) assert.throws(()=>engine.validate(state));
assert.throws(()=>engine.answer(initial,true,'explore'));
assert.throws(()=>engine.answer(initial,1,'explore'));
assert.throws(()=>engine.answer(initial,0,'unknown'));
assert.throws(()=>engine.advance(initial,0));
assert.throws(()=>engine.context(initial,'ara'));
let state=initial;
for(const [i,step] of input.course.lesson.steps.entries()){
 state=engine.answer(state,i,step.choices[0].id);
 assert.throws(()=>engine.answer(state,i,step.choices[0].id));
 assert.throws(()=>engine.advance(state,i));
 if(i===20) assert.throws(()=>engine.context(state,'ara'));
 state=engine.advance(state,i+1);
}
assert.throws(()=>engine.answer(state,21,'explore'));
assert.throws(()=>engine.advance(state,21));
process.stdout.write(JSON.stringify({complete:engine.complete(state)}));
""", {'course': browser_course(), 'invalid': invalid})
        self.assertTrue(result['complete'])


if __name__ == '__main__': unittest.main()
