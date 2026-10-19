"""Exercise the learner journey, persistence, browser API and analysis handoff."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

from scripts import discovery, facilitate, workshop

ROOT = Path(__file__).resolve().parents[1]


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.lesson = discovery.Lesson.local()

    def finish(self, directory, recommended=True):
        session = discovery.Session(directory, self.lesson)
        for index, step in enumerate(self.lesson.steps):
            answer = next(c for c in step['choices'] if c['recommended'] == recommended)
            session.answer(index, answer['id'])
            view = self.lesson.view(session.state)
            self.assertEqual(view['feedback']['response'], answer['response'])
            self.assertTrue(view['feedback']['feedback'])
            self.assertFalse(view['complete'])
            session.advance(index + 1)
        return session

    def test_complete_both_learning_paths_and_export_context(self):
        self.assertEqual([sum(s['phase'] == p for s in self.lesson.steps) for p in 'ABC'], [9, 6, 6])
        self.assertIn('atascaron', next(c['text'] for c in self.lesson.steps[0]['choices'] if c['recommended']))
        strong = self.finish(self.directory/'strong')
        weak = self.finish(self.directory/'weak', recommended=False)
        for session, expected in ((strong, 21), (weak, 0)):
            view = self.lesson.view(session.state)
            self.assertTrue(view['complete'])
            self.assertEqual(sum(p['recommended'] for p in view['phases']), expected)
            self.assertGreaterEqual(len(view['notes']), 21)
            self.assertEqual({n['phase'] for n in view['notes']}, {'A', 'B', 'C'})
            self.assertIn('Del dolor', view['title'])
            for kind in ('ara', 'moda'):
                context = (session.directory/f'contexts/{kind}.txt').read_text()
                self.assertIn('Resultado incierto', context)
                self.assertIn('Alcance acordado', context)
                self.assertIn('DELETE /bookings/{id}', context)
                self.assertIn('supuestos', context.lower())
            self.assertTrue((session.directory/'tablero.html').is_file())
        # The authored case converges; the facilitation transcript keeps the
        # participant's actual selections and their distinct coaching.
        self.assertEqual((strong.directory/'contexts/ara.txt').read_bytes(), (weak.directory/'contexts/ara.txt').read_bytes())
        self.assertNotEqual((strong.directory/'resumen.md').read_bytes(), (weak.directory/'resumen.md').read_bytes())

    def test_resume_pending_feedback_then_resume_next_phase(self):
        folder = self.directory/'resume'
        first = discovery.Session(folder, self.lesson)
        self.assertEqual(self.lesson.view(first.state)['notes'], [])
        self.assertFalse((folder/'contexts/ara.txt').exists())
        first.answer(0, 'shortcut')
        resumed = discovery.Session(folder, self.lesson)
        self.assertIsNotNone(self.lesson.view(resumed.state)['feedback'])
        self.assertEqual(len(resumed.state['answers']), 1)
        resumed.advance(1)
        self.assertEqual(self.lesson.view(resumed.state)['cursor'], 1)
        for i in range(1, 9):
            resumed.answer(i, 'explore')
            resumed.advance(i + 1)
        resumed = discovery.Session(folder, self.lesson)
        view = self.lesson.view(resumed.state)
        self.assertEqual(view['step']['phase'], 'B')
        self.assertEqual(view['phases'][0]['recommended'], 8)
        self.assertTrue(all(n['phase'] == 'A' for n in view['notes']))

    def test_boards_reveal_placement_quadrants_autonomy_and_swimlanes_in_order(self):
        state = self.lesson.initial()
        initial = self.lesson.boards(state)
        self.assertTrue(all(not b['items'] and not b['support'] for b in initial.values()))
        views = {}
        for i, step in enumerate(self.lesson.steps):
            state = self.lesson.answer(state, i, 'explore')
            views[step['id']] = self.lesson.boards(state)
            state = self.lesson.advance(state, i + 1)
        first = views['a1']['A']['items'][0]
        self.assertFalse(first['placed'])
        self.assertNotIn('column', first)
        self.assertFalse(views['a1']['B']['items'])
        moved = next(n for n in views['a4']['A']['items'] if n['id'] == 'uncertain')
        self.assertTrue(moved['placed'])
        self.assertEqual((moved['row'], moved['column']), ('pain', 'recover'))
        self.assertEqual([r['id'] for r in initial['A']['rows']], ['actor', 'command', 'data', 'event', 'policy', 'pain'])
        self.assertTrue(all(not n['placed'] for n in views['b2']['B']['items']))
        b3 = {n['id']: n for n in views['b3']['B']['items']}
        self.assertEqual((b3['form']['row'], b3['form']['column']), ('available', 'rules'))
        self.assertEqual((b3['exceptions']['row'], b3['exceptions']['column']), ('missing', 'judgment'))
        self.assertNotIn('badge', b3['bookingagent'])
        b5 = next(n for n in views['b5']['B']['items'] if n['id'] == 'bookingagent')
        self.assertTrue(b5['human'])
        self.assertFalse(b5['selected'])
        b6 = {n['id']: n for n in views['b6']['B']['items']}
        self.assertTrue(b6['bookingagent']['selected'])
        self.assertTrue(b6['bookingagent']['badge'].startswith('P ·'))
        self.assertTrue(b6['readhelper']['badge'].startswith('E ·'))
        self.assertFalse(views['c2']['C']['endpoints'])
        self.assertEqual(len(views['c3']['C']['endpoints']), 4)
        self.assertNotIn('human', [n['id'] for n in views['c3']['C']['items']])
        c4 = {n['id']: n for n in views['c4']['C']['items']}
        self.assertEqual((c4['human']['row'], c4['human']['column']), ('human', 'approve'))
        self.assertEqual((c4['write']['row'], c4['write']['column']), ('agent', 'execute'))
        self.assertNotIn('result', c4)
        self.assertIn('result', [n['id'] for n in views['c5']['C']['items']])
        snapshot = self.lesson.board(state).decode()
        self.assertIn('WorkshopBoards.render', snapshot)
        self.assertNotIn('src="/', snapshot)  # Entire board works offline.

    def test_board_rejects_unknown_positions_or_reveal_order(self):
        raw = json.loads((ROOT/'workshop/discovery.json').read_bytes())
        raw['boards']['A']['items'][0]['column'] = 'absent'
        with self.assertRaisesRegex(ValueError, 'carril'):
            discovery.Lesson(discovery.encoded(raw), discovery.encoded(self.lesson.scenario), self.lesson.contexts)
        raw['boards']['A']['items'][0]['column'] = 'recover'
        raw['boards']['A']['items'][0]['place_after'] = 'b1'
        with self.assertRaisesRegex(ValueError, 'Progresión'):
            discovery.Lesson(discovery.encoded(raw), discovery.encoded(self.lesson.scenario), self.lesson.contexts)

    def test_public_solved_example_matches_current_lesson_and_renderer(self):
        state = self.lesson.initial()
        for i, _ in enumerate(self.lesson.steps):
            state = self.lesson.answer(state, i, 'explore')
            state = self.lesson.advance(state, i + 1)
        example = ROOT/'examples/discovery'
        self.assertEqual((example/'tableros.html').read_bytes(), self.lesson.board(state))
        self.assertEqual((example/'conversacion.md').read_bytes(),
                         b'> Ejemplo resuelto: preguntas recomendadas del caso educativo.\n\n' + self.lesson.summary(state))

    def test_no_skips_duplicate_answers_or_unreviewed_final_export(self):
        session = discovery.Session(self.directory/'practice', self.lesson)
        for cursor, choice in ((1, 'explore'), (False, 'explore'), (0, 'unknown')):
            with self.assertRaises(ValueError):
                session.answer(cursor, choice)
        with self.assertRaises(ValueError):
            session.advance(0)
        session.answer(0, 'explore')
        with self.assertRaises(ValueError):
            session.answer(0, 'explore')
        with self.assertRaisesRegex(ValueError, 'Completa'):
            self.lesson.handoff(session.state)
        for i in range(1, 21):
            session.advance(i)
            session.answer(i, 'explore')
        self.assertFalse((session.directory/'contexts/ara.txt').exists())
        with self.assertRaisesRegex(ValueError, 'Completa'):
            self.lesson.handoff(session.state)
        session.advance(21)
        self.assertTrue((session.directory/'contexts/ara.txt').exists())

    def test_corrupt_or_mismatched_sessions_and_existing_files_preserved(self):
        path = self.directory/'session'
        path.mkdir()
        (path/'personal.txt').write_text('keep')
        with self.assertRaises(ValueError):
            discovery.Session(path, self.lesson)
        self.assertEqual((path/'personal.txt').read_text(), 'keep')
        state = self.lesson.initial()
        state['material_sha256']['lesson'] = 'changed'
        (path/'session.json').write_bytes(discovery.encoded(state))
        with self.assertRaisesRegex(ValueError, 'otros materiales'):
            discovery.Session(path, self.lesson)
        state = self.lesson.initial()
        state['answers'] = [{'step': 'a2', 'choice': 'explore'}]
        with self.assertRaisesRegex(ValueError, 'fuera de orden'):
            self.lesson.validate_state(state)

    def test_failed_save_preserves_in_memory_and_disk_answers(self):
        session = discovery.Session(self.directory/'write-failure', self.lesson)
        before = (session.directory/'session.json').read_bytes()
        with patch.object(discovery, 'atomic_write', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                session.answer(0, 'explore')
        self.assertEqual(session.state['answers'], [])
        self.assertEqual((session.directory/'session.json').read_bytes(), before)

    def test_session_lock_prevents_two_writers_and_releases(self):
        folder = self.directory/'locked'
        with facilitate.session_lock(folder):
            with self.assertRaisesRegex(ValueError, 'otra terminal'):
                with facilitate.session_lock(folder):
                    pass
        with facilitate.session_lock(folder):
            pass

    def test_http_journey_and_boundaries(self):
        session = discovery.Session(self.directory/'http', self.lesson)
        server = facilitate.make_server(session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        opener = build_opener(ProxyHandler({}))
        url = f'http://127.0.0.1:{server.server_port}'

        def request(path, data=None, token='', origin=None):
            headers = {'Content-Type': 'application/json', 'X-Workshop-Token': token}
            if origin:
                headers['Origin'] = origin
            req = Request(url+path, data=discovery.encoded(data) if data is not None else None, headers=headers)
            with opener.open(req, timeout=5) as response:
                return json.load(response)

        view = request('/api/session')
        token = view['token']
        self.assertFalse(any('recommended' in c for c in view['choices']))
        self.assertEqual(view['notes'], [])
        for path in ('/', '/app.js', '/boards.js', '/style.css', '/tablero.html'):
            with opener.open(url+path) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
                if path == '/tablero.html':
                    self.assertIn('attachment', response.headers['Content-Disposition'])
                    self.assertIn(b'WorkshopBoards.render', response.read())
        for path in ('/../../LICENSE', '/contexts/ara.txt', '/workshop/discovery.json'):
            with self.assertRaises(HTTPError) as error:
                request(path)
            self.assertEqual(error.exception.code, 404)
            error.exception.close()
        for supplied_token, origin in (('', None), (token, 'https://unrelated.example')):
            with self.assertRaises(HTTPError) as error:
                request('/api/answer', {'cursor': 0, 'choice': 'explore'}, supplied_token, origin)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
        for i in range(21):
            choice = 'shortcut' if i % 3 == 0 else 'explore'
            view = request('/api/answer', {'cursor': i, 'choice': choice}, token)
            self.assertEqual(view['count'], i + 1)
            self.assertIsNotNone(view['feedback'])
            self.assertTrue(view['notes'])
            if i == 0:
                with self.assertRaises(HTTPError) as error:
                    request('/api/answer', {'cursor': 0, 'choice': choice}, token)
                self.assertEqual(error.exception.code, 409)
                error.exception.close()
            view = request('/api/next', {'count': i + 1}, token)
        self.assertTrue(view['complete'])
        self.assertEqual(sum(p['recommended'] for p in view['phases']), 14)
        with opener.open(url+'/contexts/ara.txt') as response:
            self.assertIn('Resultado incierto', response.read().decode())

    def test_completed_discovery_reaches_pinned_analysis_sources(self):
        session = self.finish(self.directory/'discovery')
        repo = self.directory/'repo'
        repo.mkdir()
        shutil.copytree(ROOT/'workshop', repo/'workshop')
        (repo/'booking_lab').mkdir()
        (repo/'booking_lab/run.py').write_text('# pinned app fixture\n')
        (repo/'LICENSE').write_text('MIT')
        for args in (('init', '-q', '-b', 'main'), ('config', 'user.name', 'Test'),
                     ('config', 'user.email', 'test@example.invalid'), ('add', '.'), ('commit', '-qm', 'Fixture')):
            subprocess.run(['git', '-C', str(repo), *args], check=True)
        # Mutable exports are not trusted; the pinned lesson reconstructs them.
        (session.directory/'contexts/ara.txt').write_text('TAMPERED EXPORT')
        out = self.directory/'prepared'
        with patch.object(workshop, 'ROOT', repo):
            manifest = workshop.prepare(out, discovery_dir=session.directory)
        context = (out/'contexts/ara.txt').read_bytes()
        self.assertIn(b'Discovery guiado', context)
        self.assertNotIn(b'TAMPERED', context)
        self.assertEqual(manifest['context_sha256']['ara.txt'], hashlib.sha256(context).hexdigest())
        self.assertEqual(manifest['discovery_session_sha256'], hashlib.sha256((out/'discovery/session.json').read_bytes()).hexdigest())
        self.assertFalse(manifest['cloud_analysis_executed'])
        for kind in ('ara', 'moda'):
            self.assertEqual((out/f'sources/{kind}/booking-mit/booking_lab/run.py').read_text(), '# pinned app fixture\n')
        scenario = json.loads((repo/'workshop/scenario.json').read_text())
        scenario['selected'] = 'different-agent'
        (repo/'workshop/scenario.json').write_text(json.dumps(scenario))
        subprocess.run(['git', '-C', str(repo), 'commit', '-qam', 'Changed case'], check=True)
        with patch.object(workshop, 'ROOT', repo):
            with self.assertRaisesRegex(ValueError, 'otros materiales'):
                workshop.prepare(self.directory/'mismatch', discovery_dir=session.directory)
        self.assertFalse((self.directory/'mismatch').exists())


if __name__ == '__main__':
    unittest.main()
