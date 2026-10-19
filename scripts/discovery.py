"""Original, deterministic discovery lesson and persisted learner session."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = {'pain': 'Dolor', 'event': 'Evento', 'actor': 'Persona', 'data': 'Datos', 'command': 'Comando', 'policy': 'Regla',
         'decision': 'Decisión', 'opportunity': 'Oportunidad', 'value': 'Valor',
         'workflow': 'Flujo', 'handoff': 'Evaluación'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def atomic_write(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)


class Lesson:
    def __init__(self, lesson_raw, scenario_raw, contexts):
        self.data = json.loads(lesson_raw)
        self.scenario = json.loads(scenario_raw)
        self.contexts = contexts
        self.hashes = {'lesson': digest(lesson_raw), 'scenario': digest(scenario_raw),
                       **{kind: digest(raw) for kind, raw in contexts.items()}}
        self.steps = self.data['steps']
        self.validate()

    @classmethod
    def local(cls, root=ROOT):
        return cls((root/'workshop/discovery.json').read_bytes(),
                   (root/'workshop/scenario.json').read_bytes(),
                   {k: (root/f'workshop/contexts/{k}.txt').read_bytes() for k in ('ara', 'moda')})

    def validate(self):
        if self.data.get('schema_version') != 1 or not self.steps:
            raise ValueError('Formato de lección no compatible')
        phase_ids = [p['id'] for p in self.data['phases']]
        if phase_ids != ['A', 'B', 'C']:
            raise ValueError('La lección debe conservar las fases A, B y C')
        seen, previous = set(), 0
        for step in self.steps:
            index = phase_ids.index(step['phase'])
            choices = step['choices']
            if (step['id'] in seen or index < previous or
                    len(choices) not in (2, 3) or
                    len({c['id'] for c in choices}) != len(choices) or
                    sum(c['recommended'] is True for c in choices) != 1):
                raise ValueError('Situaciones u opciones no válidas')
            for choice in choices:
                if any(not isinstance(choice.get(k), str) or not choice[k].strip()
                       for k in ('id', 'text', 'response', 'feedback')):
                    raise ValueError('La opción necesita respuesta y feedback')
            for note in step['notes']:
                if note['kind'] not in KINDS or not note['title'] or not note['text']:
                    raise ValueError('Nota de tablero no válida')
            previous = index
            seen.add(step['id'])
        order = {s['id']: i for i, s in enumerate(self.steps)}
        if set(self.data.get('boards', {})) != set(phase_ids):
            raise ValueError('Se requiere un tablero para cada fase')
        for phase, board in self.data['boards'].items():
            if phase not in phase_ids or board['type'] not in ('timeline', 'quadrant', 'swimlanes'):
                raise ValueError('Tipo de tablero no válido')
            rows, columns = [r['id'] for r in board['rows']], [c['id'] for c in board['columns']]
            if len(set(rows)) != len(rows) or len(set(columns)) != len(columns):
                raise ValueError('Coordenadas de tablero duplicadas')
            ids = set()
            for note in [*board['items'], *board['support'], *board.get('endpoints', [])]:
                for key in ('after', 'place_after', 'badge_after', 'human_after', 'selected_after'):
                    if key in note and (note[key] not in order or
                            self.steps[order[note[key]]]['phase'] != phase or order[note[key]] < order[note['after']]):
                        raise ValueError('Progresión del tablero no válida')
                if 'id' not in note:
                    continue  # Endpoint table rows use method rather than sticky IDs.
                if note['id'] in ids or note['kind'] not in KINDS:
                    raise ValueError('Nota de tablero duplicada o desconocida')
                ids.add(note['id'])
                if note in board['items'] and (note['row'] not in rows or note['column'] not in columns):
                    raise ValueError('La nota debe pertenecer a un carril y columna')

    def initial(self):
        return {'schema_version': 1, 'lesson_id': self.data['id'],
                'material_sha256': dict(self.hashes), 'answers': [], 'feedback': False}

    def validate_state(self, state, require_complete=False):
        if (not isinstance(state, dict) or state.get('schema_version') != 1 or
                state.get('lesson_id') != self.data['id'] or
                state.get('material_sha256') != self.hashes):
            raise ValueError('La sesión pertenece a otros materiales; usa su versión o inicia otra sesión')
        answers = state.get('answers')
        if (not isinstance(answers, list) or len(answers) > len(self.steps) or
                type(state.get('feedback')) is not bool or
                state['feedback'] and not answers):
            raise ValueError('Estado de sesión no válido')
        for step, answer in zip(self.steps, answers):
            if not isinstance(answer, dict) or set(answer) != {'step', 'choice'}:
                raise ValueError('Respuesta no válida')
            if (answer['step'] != step['id'] or
                    answer['choice'] not in [c['id'] for c in step['choices']]):
                raise ValueError('Respuestas fuera de orden o desconocidas')
        if require_complete and not self.complete(state):
            raise ValueError('Completa las tres fases y revisa el último feedback antes de preparar ARA/MODA')

    def complete(self, state):
        return len(state['answers']) == len(self.steps) and not state['feedback']

    def selection(self, index, answer):
        return next(c for c in self.steps[index]['choices'] if c['id'] == answer['choice'])

    def notes(self, state):
        return [{**note, 'phase': step['phase'], 'step': step['id']}
                for step in self.steps[:len(state['answers'])] for note in step['notes']]

    def boards(self, state):
        """Reveal notes, placement and badges only after the corresponding beat."""
        answered = {a['step'] for a in state['answers']}
        boards = {}
        for phase, source in self.data['boards'].items():
            board = {k: v for k, v in source.items() if k not in ('items', 'support', 'endpoints')}
            for group in ('items', 'support', 'endpoints'):
                board[group] = []
                for item in source.get(group, []):
                    if item['after'] not in answered:
                        continue
                    shown = {k: v for k, v in item.items() if not k.endswith('after') and k != 'badge'}
                    shown['placed'] = item.get('place_after', item['after']) in answered
                    if not shown['placed']:
                        shown.pop('row', None)
                        shown.pop('column', None)
                    if item.get('badge_after') in answered:
                        shown['badge'] = item['badge']
                    shown['human'] = item.get('human_after') in answered
                    shown['selected'] = item.get('selected_after') in answered
                    board[group].append(shown)
            boards[phase] = board
        return boards

    def view(self, state):
        self.validate_state(state)
        count = len(state['answers'])
        finished = self.complete(state)
        cursor = count - 1 if state['feedback'] else count
        step = self.steps[cursor] if not finished else None
        review = None
        if state['feedback']:
            choice = self.selection(cursor, state['answers'][-1])
            recommended = next(c for c in step['choices'] if c['recommended'])
            review = {**choice, 'speaker': step['speaker'], 'takeaway': step['takeaway'],
                      'suggested_question': recommended['text']}
        phase_scores = []
        for phase in self.data['phases']:
            answered = [(i, a) for i, a in enumerate(state['answers']) if self.steps[i]['phase'] == phase['id']]
            phase_scores.append({**phase, 'answered': len(answered),
                                 'total': sum(s['phase'] == phase['id'] for s in self.steps),
                                 'recommended': sum(self.selection(i, a)['recommended'] for i, a in answered)})
        return {'title': self.data['title'], 'intro': self.data['intro'],
                'count': count, 'total': len(self.steps), 'cursor': cursor,
                'complete': finished, 'feedback': review, 'phases': phase_scores,
                'step': {k: step[k] for k in ('id', 'phase', 'title', 'scene')} if step else None,
                'choices': [{k: c[k] for k in ('id', 'text')} for c in step['choices']] if step and not review else [],
                'notes': self.notes(state), 'boards': self.boards(state), 'kinds': KINDS}

    def answer(self, state, cursor, choice_id):
        self.validate_state(state)
        if (type(cursor) is not int or state['feedback'] or self.complete(state)
                or cursor != len(state['answers'])):
            raise ValueError('La sesión avanzó; actualiza la página para continuar')
        step = self.steps[cursor]
        if choice_id not in [c['id'] for c in step['choices']]:
            raise ValueError('Elige una de las opciones de esta situación')
        return {**state, 'answers': [*state['answers'], {'step': step['id'], 'choice': choice_id}], 'feedback': True}

    def advance(self, state, count):
        self.validate_state(state)
        if type(count) is not int or not state['feedback'] or count != len(state['answers']):
            raise ValueError('Revisa la respuesta del cliente y del coach antes de continuar')
        return {**state, 'feedback': False}

    def summary(self, state):
        view = self.view(state)
        lines = ['# Discovery de Booking MIT', '',
                 'Práctica guiada con cliente y coach. Las cifras son supuestos del caso.', '',
                 f"Situaciones respondidas: {view['count']}/{view['total']}.", '',
                 'La puntuación describe elecciones de facilitación. La evaluación de código se realiza con ARA/MODA.', '']
        for phase in view['phases']:
            lines += [f"## {phase['id']}. {phase['title']}", '',
                      f"Preguntas recomendadas elegidas: {phase['recommended']}/{phase['answered']}.", '']
            for i, answer in enumerate(state['answers']):
                step = self.steps[i]
                if step['phase'] != phase['id']:
                    continue
                choice = self.selection(i, answer)
                lines += [f"### {step['title']}", '', f"**Pregunta elegida:** {choice['text']}", '',
                          f"**Cliente:** {choice['response']}", '', f"**Coach:** {choice['feedback']}", '',
                          f"**Síntesis para el tablero:** {step['takeaway']}", '']
        return '\n'.join(lines).encode('utf-8')

    def board(self, state):
        css = (ROOT/'workshop/coach/style.css').read_text(encoding='utf-8')
        script = (ROOT/'workshop/coach/boards.js').read_text(encoding='utf-8')
        data = json.dumps({'boards': self.boards(state), 'kinds': KINDS}, ensure_ascii=False).replace('<', '\\u003c')
        return ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Tablero de discovery</title><link rel="icon" href="data:,"><style>'+css+'</style><main class="snapshot"><h1>Tablero de discovery</h1>'
                '<p>Booking MIT · '+str(len(state['answers']))+'/'+str(len(self.steps))+' situaciones</p>'
                '<div id="saved-boards"></div><noscript>Activa JavaScript para ver los tableros. La conversación está en resumen.md.</noscript></main>'
                '<script>'+script+'</script><script type="application/json" id="board-data">'+data+'</script>'
                '<script>const saved=JSON.parse(document.getElementById("board-data").textContent);'
                'for(const board of Object.values(saved.boards)){const section=document.createElement("section");'
                'section.className="saved-board";document.getElementById("saved-boards").append(section);'
                'WorkshopBoards.render(section,board,saved.kinds);}</script></html>').encode('utf-8')

    def handoff(self, state):
        self.validate_state(state, require_complete=True)
        result = {'discovery/session.json': encoded(state), 'discovery/resumen.md': self.summary(state)}
        # The synthesis is authored, just like the fixed exercise. Reconstruct it
        # from the pinned lesson, never from editable exported context files.
        synthesis = '\n\nDiscovery guiado Booking MIT (requisitos a verificar; cifras ilustrativas):\n'
        synthesis += '\n'.join(f"- {n['title']}: {n['text']}" for n in self.notes(state))
        for kind, raw in self.contexts.items():
            result[f'contexts/{kind}.txt'] = raw.rstrip() + synthesis.encode('utf-8') + b'\n'
        return result


class Session:
    def __init__(self, directory, lesson):
        self.directory = Path(directory)
        self.lesson = lesson
        path = self.directory/'session.json'
        if path.exists():
            self.state = json.loads(path.read_text(encoding='utf-8'))
            lesson.validate_state(self.state)
        else:
            if self.directory.exists() and any(p.name != '.lock' for p in self.directory.iterdir()):
                raise ValueError('El destino contiene otros archivos; elige otra carpeta')
            self.state = lesson.initial()
        self.persist(self.state)

    def persist(self, state):
        # session.json is the commit point; derived views are rebuilt on resume.
        self.lesson.validate_state(state)
        atomic_write(self.directory/'session.json', encoded(state))
        self.state = state
        atomic_write(self.directory/'tablero.html', self.lesson.board(state))
        atomic_write(self.directory/'resumen.md', self.lesson.summary(state))
        if self.lesson.complete(state):
            for name, raw in self.lesson.handoff(state).items():
                if name.startswith('contexts/'):
                    atomic_write(self.directory/name, raw)

    def answer(self, cursor, choice):
        self.persist(self.lesson.answer(self.state, cursor, choice))

    def advance(self, count):
        self.persist(self.lesson.advance(self.state, count))
