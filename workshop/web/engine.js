'use strict';
// The browser uses the same lesson, state format and progression as discovery.py.
// A parity test compares every view and export against that reference engine.
const DiscoveryEngine = (() => {
  const copy = value => JSON.parse(JSON.stringify(value));
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  function create(course) {
    const lesson = course.lesson;
    const steps = lesson.steps;
    function initial() {
      return {schema_version: 1, lesson_id: lesson.id, material_sha256: copy(course.hashes), answers: [], feedback: false};
    }
    function validate(state, requireComplete = false) {
      if (!object(state) || state.schema_version !== 1 || state.lesson_id !== lesson.id ||
          !object(state.material_sha256) || Object.keys(state.material_sha256).length !== Object.keys(course.hashes).length ||
          Object.entries(course.hashes).some(([key, value]) => state.material_sha256[key] !== value)) {
        throw new Error('Este avance pertenece a otra versión. Guarda una copia y comienza una nueva práctica');
      }
      if (!Array.isArray(state.answers) || state.answers.length > steps.length ||
          typeof state.feedback !== 'boolean' || (state.feedback && !state.answers.length)) {
        throw new Error('El archivo de avance no tiene un estado válido');
      }
      state.answers.forEach((answer, i) => {
        if (!object(answer) || Object.keys(answer).sort().join(',') !== 'choice,step' ||
            answer.step !== steps[i].id || !steps[i].choices.some(c => c.id === answer.choice)) {
          throw new Error('El avance contiene respuestas desconocidas o fuera de orden');
        }
      });
      if (requireComplete && !complete(state)) throw new Error('Completa las 21 situaciones y revisa el último feedback');
      return {...initial(), answers: state.answers.map(a => ({step: a.step, choice: a.choice})), feedback: state.feedback};
    }
    function complete(state) { return state.answers.length === steps.length && !state.feedback; }
    function selection(index, answer) { return steps[index].choices.find(c => c.id === answer.choice); }
    function notes(state) {
      return steps.slice(0, state.answers.length).flatMap(step => step.notes.map(note => ({...note, phase: step.phase, step: step.id})));
    }
    function boards(state) {
      const answered = new Set(state.answers.map(a => a.step));
      return Object.fromEntries(Object.entries(lesson.boards).map(([phase, source]) => {
        const board = Object.fromEntries(Object.entries(source).filter(([key]) => !['items', 'support', 'endpoints'].includes(key)));
        for (const group of ['items', 'support', 'endpoints']) {
          board[group] = (source[group] || []).filter(item => answered.has(item.after)).map(item => {
            const shown = Object.fromEntries(Object.entries(item).filter(([key]) => !key.endsWith('after') && key !== 'badge'));
            shown.placed = answered.has(item.place_after || item.after);
            if (!shown.placed) { delete shown.row; delete shown.column; }
            if (answered.has(item.badge_after)) shown.badge = item.badge;
            shown.human = answered.has(item.human_after);
            shown.selected = answered.has(item.selected_after);
            return shown;
          });
        }
        return [phase, board];
      }));
    }
    function view(state) {
      validate(state);
      const count = state.answers.length;
      const finished = complete(state);
      const cursor = state.feedback ? count - 1 : count;
      const step = finished ? null : steps[cursor];
      const review = state.feedback ? {...selection(cursor, state.answers[count - 1]), speaker: step.speaker,
        takeaway: step.takeaway, suggested_question: step.choices.find(c => c.recommended).text} : null;
      const phases = lesson.phases.map(phase => {
        const answered = state.answers.map((answer, i) => ({answer, i})).filter(({i}) => steps[i].phase === phase.id);
        return {...phase, answered: answered.length, total: steps.filter(s => s.phase === phase.id).length,
          recommended: answered.filter(({i, answer}) => selection(i, answer).recommended).length};
      });
      return {title: lesson.title, intro: lesson.intro, count, total: steps.length, cursor, complete: finished,
        feedback: review, phases, step: step ? {id: step.id, phase: step.phase, title: step.title, scene: step.scene} : null,
        choices: step && !review ? step.choices.map(c => ({id: c.id, text: c.text})) : [], notes: notes(state), boards: boards(state), kinds: course.kinds};
    }
    function answer(state, cursor, choice) {
      state = validate(state);
      if (!Number.isInteger(cursor) || state.feedback || complete(state) || cursor !== state.answers.length) {
        throw new Error('La sesión avanzó. Recupera la sesión para continuar');
      }
      if (!steps[cursor].choices.some(c => c.id === choice)) throw new Error('Elige una pregunta de esta situación');
      return {...state, answers: [...state.answers, {step: steps[cursor].id, choice}], feedback: true};
    }
    function advance(state, count) {
      state = validate(state);
      if (!Number.isInteger(count) || !state.feedback || count !== state.answers.length) {
        throw new Error('Revisa la respuesta del cliente y del coach antes de continuar');
      }
      return {...state, feedback: false};
    }
    function summary(state) {
      const current = view(state);
      const lines = ['# Discovery de Booking MIT', '', 'Práctica guiada con cliente y coach. Las cifras son supuestos del caso.', '',
        `Situaciones respondidas: ${current.count}/${current.total}.`, '',
        'La puntuación describe elecciones de facilitación. La evaluación de código se realiza con ARA/MODA.', ''];
      for (const phase of current.phases) {
        lines.push(`## ${phase.id}. ${phase.title}`, '', `Preguntas recomendadas elegidas: ${phase.recommended}/${phase.answered}.`, '');
        state.answers.forEach((answer, i) => {
          const step = steps[i];
          if (step.phase !== phase.id) return;
          const choice = selection(i, answer);
          lines.push(`### ${step.title}`, '', `**Pregunta elegida:** ${choice.text}`, '', `**Cliente:** ${choice.response}`, '',
            `**Coach:** ${choice.feedback}`, '', `**Síntesis para el tablero:** ${step.takeaway}`, '');
        });
      }
      return lines.join('\n');
    }
    function context(state, kind) {
      validate(state, true);
      if (!['ara', 'moda'].includes(kind)) throw new Error('Contexto desconocido');
      return course.contexts[kind].trimEnd() + '\n\nDiscovery guiado Booking MIT (requisitos a verificar; cifras ilustrativas):\n' +
        notes(state).map(n => `- ${n.title}: ${n.text}`).join('\n') + '\n';
    }
    return {initial, validate, complete, view, answer, advance, summary, context};
  }
  return {create};
})();
if (typeof module !== 'undefined') module.exports = DiscoveryEngine;
