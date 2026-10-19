'use strict';
let session;
let filter = null;
let busy = false;
const $ = (id) => document.getElementById(id);
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function link(text, href) {
  const element = node('a', text);
  element.href = href;
  element.target = '_blank';
  element.rel = 'noopener';
  return element;
}
function button(text, className, action) {
  const element = node('button', text, className);
  element.type = 'button';
  element.addEventListener('click', action);
  return element;
}
function renderBoard() {
  WorkshopBoards.render($('notes'), session.boards[filter], session.kinds);
  const total = Object.values(session.boards).reduce((sum, board) => sum + board.items.length + board.support.length, 0);
  $('note-count').textContent = `${total} ${total === 1 ? 'nota' : 'notas'}`;
  $('board-empty').hidden = total > 0;
  const filters = document.querySelector('.board-filters');
  filters.replaceChildren();
  for (const phase of session.phases) {
    const b = button(`${phase.id} · ${phase.title}`, 'filter', () => { filter = phase.id; renderBoard(); });
    b.setAttribute('aria-pressed', String(filter === phase.id));
    filters.append(b);
  }
}
function render(focus = false) {
  $('error').hidden = true;
  $('reload').hidden = true;
  $('save-status').textContent = 'Avance guardado en este equipo';
  $('intro').textContent = session.intro;
  $('progress').max = session.total;
  $('progress').value = session.count;
  $('progress-label').textContent = `${session.count} de ${session.total} situaciones respondidas`;
  $('phases').replaceChildren();
  for (const p of session.phases) {
    const li = node('li', undefined, 'phase');
    if (session.step?.phase === p.id) { li.classList.add('current'); li.setAttribute('aria-current', 'step'); }
    li.append(node('b', `${p.id}. ${p.title}`), node('span', `${p.answered}/${p.total} situaciones`));
    $('phases').append(li);
  }
  $('question').replaceChildren();
  $('feedback').replaceChildren();
  $('completion').hidden = !session.complete;
  if (session.complete) {
    renderCompletion();
  } else {
    const step = session.step;
    $('question').append(node('span', `${step.phase} · Situación ${session.cursor + 1} de ${session.total}`, 'step-label'), node('h2', step.title), node('p', step.scene));
    if (session.feedback) {
      const feedback = session.feedback;
      $('question').append(node('p', `Tu pregunta: ${feedback.text}`, 'selected-question'));
      const customer = node('section', undefined, 'dialogue');
      customer.append(node('h3', feedback.speaker), node('p', feedback.response));
      const coach = node('section', undefined, 'coach');
      coach.append(node('h3', feedback.recommended ? 'Coach · pregunta bien orientada' : 'Coach · prueba otro enfoque'), node('p', feedback.feedback));
      if (!feedback.recommended) {
        coach.append(node('p', `Una pregunta que abre más información: «${feedback.suggested_question}»`, 'followup'), node('p', `Para completar el caso: ${feedback.takeaway}`, 'followup'));
      }
      const nextPhase = session.phases.find(p => p.id > step.phase && p.answered === 0);
      const atBoundary = session.phases.find(p => p.id === step.phase).answered === session.phases.find(p => p.id === step.phase).total;
      const label = session.count === session.total ? 'Ver síntesis y continuar a ARA/MODA' : atBoundary && nextPhase ? `Continuar a ${nextPhase.id} · ${nextPhase.title}` : 'Siguiente situación';
      $('feedback').append(customer, coach, button(label, 'primary', () => mutate('/api/next', {count: session.count})));
    } else {
      const choices = node('div', undefined, 'options');
      session.choices.forEach((choice, i) => {
        const b = button('', 'option', () => mutate('/api/answer', {cursor: session.cursor, choice: choice.id}));
        b.append(node('span', String.fromCharCode(65 + i), 'letter'), node('span', choice.text));
        choices.append(b);
      });
      $('question').append(choices, node('p', 'Elige la pregunta que harías ahora. El coach te ayudará a interpretar la respuesta.', 'hint'));
    }
  }
  renderBoard();
  if (focus) $('exercise').focus();
}
function renderCompletion() {
  const target = $('completion');
  target.replaceChildren(node('p', 'DISCOVERY COMPLETADO', 'eyebrow'), node('h2', 'Del proceso a una evaluación con contexto.'), node('p', 'Ya tienes los dolores, la oportunidad, los límites y el flujo del agente de reservas. Revisa el tablero y usa esta síntesis para ARA/MODA.'));
  const scores = node('ul', undefined, 'score-list');
  for (const phase of session.phases) scores.append(node('li', `${phase.id}. ${phase.title}: ${phase.recommended}/${phase.total} preguntas recomendadas elegidas.`));
  target.append(scores, node('p', 'Esta evaluación describe tu facilitación. Los controles del código se comprueban con ARA/MODA y las pruebas del laboratorio.', 'hint'));
  const steps = node('ol', undefined, 'next-steps');
  let li = node('li');
  li.append(link('Revisa tu conversación y el feedback', '/resumen.md'), document.createTextNode(' · '), link('Descarga tus tableros', '/tablero.html'), node('p', 'Abre tablero.html para consultarlos sin conexión. Tu progreso queda guardado en la carpeta de la sesión.'));
  steps.append(li);
  li = node('li');
  li.append(link('Sigue la lectura guiada de ARA/MODA', 'https://github.com/sjaramillov/agentic-transformation-workshop-latam/blob/main/GUIA_REPLICACION.md#4-lee-ara-con-el-caso-en-mente-d'), node('p', 'La guía incluye informes reales de referencia y una comparación antes/después.'));
  steps.append(li);
  li = node('li', 'Para un análisis nuevo en tu cuenta, prepara los materiales desde la raíz del repo:');
  const pre = node('pre');
  pre.append(node('code', session.prepare_command));
  li.append(pre, link('Contexto ARA generado', '/contexts/ara.txt'), document.createTextNode(' · '), link('Contexto MODA generado', '/contexts/moda.txt'));
  steps.append(li);
  target.append(steps, node('p', 'Puedes cerrar esta página y pausar la terminal con Ctrl+C. El mismo comando vuelve a abrir tu sesión.', 'hint'));
}
async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'No se pudo completar la acción');
  return data;
}
function showError(error) {
  $('error').textContent = `${error.message}. Si cerraste la terminal, vuelve a ejecutar el comando del workshop.`;
  $('error').hidden = false;
  $('reload').hidden = false;
  $('save-status').textContent = 'Comprueba la conexión con la sesión';
}
async function load() {
  try {
    session = await request('/api/session');
    filter = session.step?.phase || 'C';
    render();
  } catch (error) { showError(error); }
}
async function mutate(path, body) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('#exercise button').forEach(b => { b.disabled = true; });
  $('save-status').textContent = 'Guardando…';
  try {
    const previousPhase = session.step?.phase;
    session = await request(path, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Workshop-Token': session.token}, body: JSON.stringify(body)});
    if (session.step?.phase !== previousPhase) filter = session.step?.phase || 'C';
    render(true);
  } catch (error) { showError(error); }
  finally { busy = false; }
}
$('expand-board').addEventListener('click', () => {
  const expanded = document.querySelector('.workspace').classList.toggle('board-expanded');
  $('expand-board').textContent = expanded ? 'Volver a la reunión' : 'Ampliar tablero';
  $('expand-board').setAttribute('aria-expanded', String(expanded));
  document.querySelector('.board').scrollIntoView({block: 'start'});
});
$('reload').addEventListener('click', load);
load();
