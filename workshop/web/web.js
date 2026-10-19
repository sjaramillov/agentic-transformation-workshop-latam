'use strict';
// Browser persistence and downloads; app.js remains the shared learning UI.
window.WorkshopWeb = (() => {
  const KEY = 'agentic-transformation-workshop-latam:discovery:v1';
  const LIMIT = 128 * 1024;
  const course = window.WorkshopCourse;
  const engine = course ? DiscoveryEngine.create(course) : null;
  let record = null;
  let memoryOnly = false;
  let unreadable = null;
  let pending = null;
  let importTicket = 0;
  const listeners = [];
  const byId = id => document.getElementById(id);
  const notify = focus => listeners.forEach(listener => listener(focus));
  const revision = () => crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  async function lock(task) {
    if (!navigator.locks || memoryOnly) return task();
    let started = false;
    try { return await navigator.locks.request(KEY, () => { started = true; return task(); }); }
    catch (error) {
      if (started || error.name !== 'SecurityError') throw error;
      memoryOnly = true;
      notice();
      return task();
    }
  }

  function notice() {
    byId('storage-notice').hidden = !memoryOnly;
    byId('storage-notice').textContent = 'Este navegador no permite guardar el avance. Puedes seguir practicando; descarga tu avance antes de cerrar esta pestaña.';
  }
  function rawStorage() {
    if (memoryOnly) return record ? JSON.stringify(record) : null;
    try { return localStorage.getItem(KEY); }
    catch { memoryOnly = true; notice(); return record ? JSON.stringify(record) : null; }
  }
  function persist(state) {
    record = {revision: revision(), session: engine.validate(state)};
    unreadable = null;
    if (!memoryOnly) {
      try { localStorage.setItem(KEY, JSON.stringify(record)); }
      catch { memoryOnly = true; }
    }
    notice();
    return record;
  }
  function read() {
    if (!engine) throw new Error('No se pudieron cargar los materiales. Recarga esta página con conexión a internet');
    const raw = rawStorage();
    if (memoryOnly && record) return record;
    if (raw === null) return persist(engine.initial());
    try {
      if (raw.length > LIMIT) throw new Error('El avance guardado es demasiado grande');
      const saved = JSON.parse(raw);
      if (!saved || typeof saved.revision !== 'string') throw new Error('El avance guardado no se puede leer');
      record = {revision: saved.revision, session: engine.validate(saved.session)};
      unreadable = null;
      return record;
    } catch (error) {
      unreadable = raw;
      byId('session-tools').open = true;
      throw new Error(error instanceof SyntaxError ? 'El avance guardado no se puede leer. Descarga una copia o inicia una nueva práctica' : error.message);
    }
  }
  function currentView() { return {...engine.view(record.session), token: record.revision}; }
  async function request(path, options) {
    return lock(() => {
      const fresh = read();
      if (path === '/api/session') return currentView();
      if (!options || options.headers['X-Workshop-Token'] !== fresh.revision) {
        throw new Error('El avance cambió en otra pestaña. Pulsa Recuperar sesión');
      }
      const body = JSON.parse(options.body);
      if (path === '/api/answer') persist(engine.answer(fresh.session, body.cursor, body.choice));
      else if (path === '/api/next') persist(engine.advance(fresh.session, body.count));
      else throw new Error('Acción desconocida');
      return currentView();
    });
  }
  function download(name, content, type = 'text/plain;charset=utf-8') {
    const url = URL.createObjectURL(new Blob([content], {type}));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = name;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  function boardHTML() {
    const view = engine.view(record.session);
    const data = JSON.stringify({boards: view.boards, kinds: view.kinds}).replace(/</g, '\\u003c');
    return '<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<title>Tablero de discovery</title><link rel="icon" href="data:,"><style>' + course.assets.css + '</style>' +
      '<main class="snapshot"><h1>Tablero de discovery</h1><p>Booking MIT · ' + view.count + '/' + view.total + ' situaciones</p>' +
      '<div id="saved-boards"></div><noscript>Activa JavaScript para ver los tableros. La conversación está en resumen.md.</noscript></main>' +
      '<script>' + course.assets.renderer + '</script><script type="application/json" id="board-data">' + data + '</script>' +
      '<script>const saved=JSON.parse(document.getElementById("board-data").textContent);' +
      'for(const board of Object.values(saved.boards)){const section=document.createElement("section");section.className="saved-board";' +
      'document.getElementById("saved-boards").append(section);WorkshopBoards.render(section,board,saved.kinds);}</script></html>';
  }
  function exportSession() {
    if (unreadable !== null) return download('avance-para-recuperar.json', unreadable, 'application/json');
    read();
    download('session.json', JSON.stringify(record.session, null, 2) + '\n', 'application/json');
  }
  function fileError(error) { byId('file-status').textContent = error.message; }
  function prepareReplace(state, message, label) {
    pending = {state: engine.validate(state), previous: rawStorage()};
    byId('replace-message').textContent = message;
    byId('confirm-replace').textContent = label;
    byId('replace-confirm').hidden = false;
    byId('file-status').textContent = '';
    byId('confirm-replace').focus();
  }
  byId('export-session').addEventListener('click', () => { try { exportSession(); } catch (error) { fileError(error); } });
  byId('import-session').addEventListener('click', () => byId('session-file').click());
  byId('session-file').addEventListener('change', async event => {
    const file = event.target.files[0];
    const ticket = ++importTicket;
    event.target.value = '';
    if (!file) return;
    pending = null;
    byId('replace-confirm').hidden = true;
    try {
      if (file.size > LIMIT) throw new Error('El archivo es demasiado grande. Elige un archivo de avance JSON');
      const state = engine.validate(JSON.parse(await file.text()));
      if (ticket !== importTicket) return;
      prepareReplace(state, `El archivo contiene ${state.answers.length} de ${course.lesson.steps.length} situaciones. Cargarlo reemplazará el avance de este navegador.`, 'Cargar este avance');
    } catch (error) {
      if (ticket === importTicket) fileError(error instanceof SyntaxError ? new Error('El archivo no es un avance JSON válido') : error);
    }
  });
  byId('new-session').addEventListener('click', () => {
    importTicket++;
    try { prepareReplace(engine.initial(), 'Comenzarás desde la primera pregunta. Puedes descargar tu avance actual antes de continuar.', 'Sí, nueva práctica'); }
    catch (error) { fileError(error); }
  });
  byId('cancel-replace').addEventListener('click', () => { importTicket++; pending = null; byId('replace-confirm').hidden = true; });
  byId('confirm-replace').addEventListener('click', async () => {
    if (!pending) return;
    const replacement = pending;
    byId('confirm-replace').disabled = true;
    try {
      await lock(() => {
        if (pending !== replacement || rawStorage() !== replacement.previous) throw new Error('El avance cambió. Cancela esta acción y vuelve a intentarlo; otra pestaña pudo actualizarlo');
        persist(replacement.state);
        pending = null;
      });
      byId('replace-confirm').hidden = true;
      byId('session-tools').open = false;
      byId('file-status').textContent = '';
      notify(true);
    } catch (error) { fileError(error); }
    finally { byId('confirm-replace').disabled = false; }
  });
  window.addEventListener('storage', event => { if ((event.key === KEY || event.key === null) && !memoryOnly) notify(false); });

  function renderCompletion(target, view, helpers) {
    const {node, button, link} = helpers;
    target.replaceChildren(node('p', 'DISCOVERY COMPLETADO', 'eyebrow'), node('h2', 'Tu conversación ya tiene un siguiente paso.'),
      node('p', 'Descubriste el dolor, elegiste una oportunidad y diseñaste un flujo con aprobación y recuperación. Lleva ese contexto a ARA/MODA.'));
    const scores = node('ul', undefined, 'score-list');
    for (const phase of view.phases) scores.append(node('li', `${phase.id}. ${phase.title}: ${phase.recommended}/${phase.total} preguntas recomendadas elegidas.`));
    target.append(scores, node('p', 'El coach valora cómo preguntas. ARA/MODA evalúan los controles y las capacidades de la aplicación.', 'hint'));
    const downloads = node('div', undefined, 'downloads');
    downloads.append(button('Descargar conversación', 'secondary', () => download('resumen.md', engine.summary(record.session))),
      button('Descargar tableros', 'secondary', () => download('tablero.html', boardHTML(), 'text/html;charset=utf-8')),
      button('Descargar avance', 'secondary', exportSession));
    target.append(node('h3', 'Conserva lo que descubriste'), downloads,
      node('p', 'Los tableros descargados se abren sin conexión. El archivo de avance permite retomar en otro navegador.', 'hint'));
    const actions = node('section', undefined, 'completion-actions');
    const guide = 'https://github.com/sjaramillov/agentic-transformation-workshop-latam/blob/main/GUIA_REPLICACION.md';
    actions.append(node('h3', 'Continúa con ARA/MODA'), node('p', 'La guía incluye informes públicos para practicar su lectura. Para una evaluación nueva, usa estos contextos con el código del laboratorio en tu cuenta AWS.'),
      link('Leer ARA con el caso en mente', guide + '#4-lee-ara-con-el-caso-en-mente-d'),
      link('Seguir la guía de evaluación', guide + '#5-relaciona-moda-con-el-trabajo-que-necesita-el-agente-eg'));
    const contexts = node('div', undefined, 'downloads');
    for (const kind of ['ara', 'moda']) contexts.append(button(`Descargar contexto ${kind.toUpperCase()}`, 'secondary', () => download(`${kind}.txt`, engine.context(record.session, kind))));
    actions.append(contexts);
    target.append(actions, node('p', memoryOnly ? 'Descarga tu avance antes de cerrar esta pestaña.' : 'Puedes cerrar esta página. Al volver a este navegador encontrarás tu sesión completa.', 'hint'));
  }
  return {request, renderCompletion, subscribe: listener => listeners.push(listener),
    saveMessage: () => memoryOnly ? 'Avance temporal · descarga una copia' : 'Avance guardado en este navegador'};
})();
