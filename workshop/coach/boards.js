'use strict';
// Shared by the live lesson and its self-contained, offline board export.
const WorkshopBoards = (() => {
  function el(tag, text, className) {
    const value = document.createElement(tag);
    if (text !== undefined) value.textContent = text;
    if (className) value.className = className;
    return value;
  }
  function card(note, kinds) {
    const value = el('article', undefined, `note ${note.kind}`);
    value.dataset.noteId = note.id;
    if (note.selected) value.classList.add('selected');
    value.append(el('small', kinds[note.kind]), el('h4', note.title), el('p', note.text));
    if (note.badge) value.append(el('span', note.badge, 'autonomy'));
    if (note.human) value.append(el('span', 'H · aprobación humana', 'human-badge'));
    if (note.selected) value.append(el('strong', 'Oportunidad elegida', 'chosen-label'));
    return value;
  }
  function region(table, label) {
    const scroll = el('div', undefined, 'board-scroll');
    scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', label + '. Desplazamiento horizontal disponible.');
    scroll.append(table);
    return scroll;
  }
  function render(target, board, kinds) {
    target.replaceChildren(el('h3', board.title, 'map-title'), el('p', board.description, 'map-description'));
    const waiting = board.items.filter(n => !n.placed);
    if (waiting.length) {
      const tray = el('section', undefined, 'tray');
      tray.append(el('h4', 'Por ubicar · seguimos investigando'));
      const notes = el('div', undefined, 'support-notes');
      waiting.forEach(n => notes.append(card(n, kinds)));
      tray.append(notes);
      target.append(tray);
    }
    const table = el('table', undefined, `process-map ${board.type}`);
    const caption = board.type === 'quadrant' ? '↑ Disponibilidad de datos · Criterio requerido →' : board.type === 'timeline' ? 'Recorrido habitual 1 → 4 · Excepción y recuperación 5' : '1 → 2 → 3 → 4 → 5 → 6 · Si se rechaza en 4, termina sin escritura';
    table.append(el('caption', caption));
    const head = el('thead');
    const headings = el('tr');
    const corner = el('th', board.type === 'quadrant' ? 'Datos / criterio' : 'Carril / paso');
    corner.scope = 'col';
    headings.append(corner);
    for (const column of board.columns) {
      const th = el('th', column.label);
      th.scope = 'col';
      th.dataset.column = column.id;
      headings.append(th);
    }
    head.append(headings);
    table.append(head);
    const body = el('tbody');
    for (const row of board.rows) {
      const tr = el('tr');
      const label = el('th', row.label);
      label.scope = 'row';
      tr.append(label);
      for (const column of board.columns) {
        const cell = el('td');
        cell.dataset.row = row.id;
        cell.dataset.column = column.id;
        const zone = board.zones?.find(z => z.row === row.id && z.column === column.id);
        if (zone) cell.append(el('h4', zone.label, 'zone-label'));
        const placed = board.items.filter(n => n.placed && n.row === row.id && n.column === column.id);
        placed.forEach(n => cell.append(card(n, kinds)));
        if (!placed.length) {
          const placeholder = el('span', zone ? 'Sin oportunidad ubicada aún' : '·', 'empty-cell');
          if (!zone) placeholder.setAttribute('aria-label', 'Sin nota en este paso');
          cell.append(placeholder);
        }
        tr.append(cell);
      }
      body.append(tr);
    }
    table.append(body);
    target.append(el('p', 'Puedes ampliar el tablero o desplazarlo horizontalmente para seguir el recorrido.', 'scroll-hint'), region(table, board.title));
    if (board.endpoints.length) {
      const endpoints = el('table', undefined, 'endpoint-table');
      endpoints.append(el('caption', 'Superficie que evaluará ARA'));
      const h = el('thead');
      const r = el('tr');
      for (const text of ['Uso del agente', 'Operación', 'Efecto']) {
        const th = el('th', text); th.scope = 'col'; r.append(th);
      }
      h.append(r); endpoints.append(h);
      const b = el('tbody');
      for (const endpoint of board.endpoints) {
        const tr = el('tr');
        tr.append(el('td', endpoint.role), el('td', endpoint.method), el('td', endpoint.purpose));
        b.append(tr);
      }
      endpoints.append(b);
      target.append(region(endpoints, 'Operaciones de lectura y escritura'));
    }
    if (board.support.length) {
      const support = el('section', undefined, 'board-support');
      support.append(el('h4', 'Acuerdos y dependencias'));
      const notes = el('div', undefined, 'support-notes');
      board.support.forEach(n => notes.append(card(n, kinds)));
      support.append(notes);
      target.append(support);
    }
  }
  return {render};
})();
