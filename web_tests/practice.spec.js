const {test, expect} = require('@playwright/test');
const fs = require('node:fs/promises');
const lesson = require('../workshop/discovery.json');
const KEY = 'agentic-transformation-workshop-latam:discovery:v1';
const start = async page => { await page.goto('practica/'); await expect(page.locator('.option')).toHaveCount(2); };
const state = page => page.evaluate(key => JSON.parse(localStorage.getItem(key)).session, KEY);
async function choose(page, i, recommended = true) {
  const choice = lesson.steps[i].choices.find(c => c.recommended === recommended);
  await expect(page.locator('#question h2')).toHaveText(lesson.steps[i].title);
  await page.locator('.option').filter({hasText: choice.text}).click();
  await expect(page.locator('.dialogue p')).toHaveText(choice.response);
  await expect(page.locator('.coach > p').first()).toHaveText(choice.feedback);
  await expect(page.locator('#progress-label')).toHaveText(`${i + 1} de 21 situaciones respondidas`);
}
async function next(page) { await page.locator('#feedback button').click(); }
async function downloaded(page, selector, name) {
  const event = page.waitForEvent('download');
  await selector.click();
  const file = await event;
  expect(file.suggestedFilename()).toBe(name);
  return fs.readFile(await file.path(), 'utf8');
}
async function upload(page, data) {
  await page.locator('#session-tools').evaluate(el => { el.open = true; });
  await page.locator('#session-file').setInputFiles({name: 'session.json', mimeType: 'application/json', buffer: Buffer.from(typeof data === 'string' ? data : JSON.stringify(data))});
}
async function boardMatches(page, index) {
  const phase = lesson.steps[index].phase;
  const answered = new Set(lesson.steps.slice(0, index + 1).map(s => s.id));
  const board = lesson.boards[phase];
  const visible = [...board.items, ...board.support].filter(n => answered.has(n.after));
  await expect(page.locator('#notes .note')).toHaveCount(visible.length);
  for (const note of visible) {
    const card = page.locator(`[data-note-id="${note.id}"]`);
    await expect(card.locator('h4')).toHaveText(note.title);
    const placed = answered.has(note.place_after || note.after);
    if (board.items.includes(note)) {
      const container = placed ? `[data-row="${note.row}"][data-column="${note.column}"]` : '.tray';
      await expect(page.locator(container).locator(`[data-note-id="${note.id}"]`)).toHaveCount(1);
    }
    await expect(card.locator('.autonomy')).toHaveCount(answered.has(note.badge_after) ? 1 : 0);
    await expect(card.locator('.human-badge')).toHaveCount(answered.has(note.human_after) ? 1 : 0);
    await expect(card.locator('.chosen-label')).toHaveCount(answered.has(note.selected_after) ? 1 : 0);
  }
  await expect(page.locator('.endpoint-table tbody tr')).toHaveCount((board.endpoints || []).filter(e => answered.has(e.after)).length);
}

test('complete 21 situations, progressive spatial boards and all downloads', async ({page, context}, testInfo) => {
  const errors = [], unwanted = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('request', r => { if (r.method() !== 'GET' || r.url().includes('/api/')) unwanted.push(r.url()); });
  await page.goto('./');
  await expect(page.locator('body')).toHaveClass(/js-deck/);
  await page.locator('#proposito').getByRole('link', {name: 'Empezar la práctica'}).click();
  await expect(page.locator('.option')).toHaveCount(2);
  for (let i = 0; i < 21; i++) {
    await choose(page, i);
    await boardMatches(page, i);
    if ([0, 8, 14, 20].includes(i)) {
      await page.reload();
      await expect(page.locator('.coach')).toBeVisible();
      expect((await state(page)).feedback).toBe(true);
    }
    await next(page);
  }
  await expect(page.locator('#completion')).toBeVisible();
  await expect(page.locator('.score-list')).toContainText('9/9');
  const full = await state(page);
  expect(full.answers).toHaveLength(21);
  expect(full.feedback).toBe(false);
  const summary = await downloaded(page, page.getByRole('button', {name: 'Descargar conversación', exact: true}), 'resumen.md');
  expect(summary).toContain('Situaciones respondidas: 21/21.');
  expect(summary.match(/\*\*Cliente:\*\*/g)).toHaveLength(21);
  const exported = await downloaded(page, page.locator('#completion').getByRole('button', {name: 'Descargar avance', exact: true}), 'session.json');
  expect(JSON.parse(exported)).toEqual(full);
  for (const kind of ['ARA', 'MODA']) {
    const content = await downloaded(page, page.getByRole('button', {name: `Descargar contexto ${kind}`, exact: true}), `${kind.toLowerCase()}.txt`);
    expect(content).toContain('Discovery guiado Booking MIT');
    expect(content).toContain(lesson.steps[20].notes[0].title);
  }
  const html = await downloaded(page, page.getByRole('button', {name: 'Descargar tableros', exact: true}), 'tablero.html');
  const offline = await context.newPage();
  const offlineRequests = [];
  offline.on('request', r => offlineRequests.push(r.url()));
  await offline.setContent(html);
  await expect(offline.locator('.saved-board')).toHaveCount(3);
  await expect(offline.locator('.note')).toHaveCount(45);
  expect(offlineRequests).toEqual([]);
  await offline.close();
  await page.reload();
  await expect(page.locator('#completion')).toBeVisible();
  expect(errors).toEqual([]);
  expect(unwanted).toEqual([]);
  // Capture after the runtime assertions: WebKit can report Playwright's own
  // screenshot stylesheet injection under the deliberately strict page CSP.
  await page.screenshot({path: testInfo.outputPath('completed.png'), fullPage: true, caret: 'initial'});
});

test('alternative questions give coaching and still complete the same case', async ({page}) => {
  await start(page);
  for (let i = 0; i < 21; i++) {
    await choose(page, i, false);
    await expect(page.locator('.coach')).toContainText('Una pregunta que abre más información');
    await next(page);
  }
  await expect(page.locator('.score-list')).toContainText('0/9');
  await expect(page.locator('.score-list li').nth(1)).toContainText('0/6');
  await expect(page.locator('.score-list li').nth(2)).toContainText('0/6');
  const summary = await downloaded(page, page.getByRole('button', {name: 'Descargar conversación'}), 'resumen.md');
  expect(summary).toContain(lesson.steps[0].choices.find(c => !c.recommended).text);
});

test('export and import resume the feedback in a fresh browser context', async ({page, browser, baseURL}) => {
  await start(page);
  await choose(page, 0);
  await page.locator('#session-tools summary').click();
  const exported = await downloaded(page, page.locator('#export-session'), 'session.json');
  const freshContext = await browser.newContext({baseURL});
  const fresh = await freshContext.newPage();
  await start(fresh);
  await upload(fresh, exported);
  await expect(fresh.locator('#replace-confirm')).toBeVisible();
  expect((await state(fresh)).answers).toHaveLength(0);
  await fresh.locator('#confirm-replace').click();
  await expect(fresh.locator('.dialogue')).toBeVisible();
  expect(await state(fresh)).toEqual(JSON.parse(exported));
  await next(fresh);
  await expect(fresh.locator('#question h2')).toHaveText(lesson.steps[1].title);
  await freshContext.close();
});

test('invalid imports preserve progress; reset requires an explicit choice', async ({page}) => {
  await start(page);
  await choose(page, 0);
  const before = await state(page);
  for (const value of ['not json', {...before, lesson_id: 'other'}, {...before, answers: [{step: 'c6', choice: 'explore'}]}, ' '.repeat(129 * 1024)]) {
    await upload(page, value);
    await expect(page.locator('#file-status')).not.toBeEmpty();
    await expect(page.locator('#replace-confirm')).toBeHidden();
    expect(await state(page)).toEqual(before);
  }
  await page.locator('#new-session').click();
  await page.locator('#cancel-replace').click();
  expect(await state(page)).toEqual(before);
  await page.locator('#new-session').click();
  await page.locator('#confirm-replace').click();
  await expect(page.locator('.option')).toHaveCount(2);
  expect((await state(page)).answers).toEqual([]);
});

test('corrupt stored data can be downloaded before starting again', async ({page}) => {
  await start(page);
  await page.evaluate(key => localStorage.setItem(key, '{broken'), KEY);
  await page.reload();
  await expect(page.locator('#error')).toBeVisible();
  expect(await downloaded(page, page.locator('#export-session'), 'avance-para-recuperar.json')).toBe('{broken');
  await page.locator('#new-session').click();
  await page.locator('#confirm-replace').click();
  await expect(page.locator('.option')).toHaveCount(2);
  await choose(page, 0);
});

test('storage unavailable allows practice and export with a visible notice', async ({page}) => {
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => { throw new DOMException('Blocked', 'SecurityError'); };
    Storage.prototype.setItem = () => { throw new DOMException('Blocked', 'SecurityError'); };
  });
  await start(page);
  await expect(page.locator('#storage-notice')).toBeVisible();
  await expect(page.locator('#save-status')).toContainText('temporal');
  await choose(page, 0);
  await next(page);
  await choose(page, 1);
  await page.locator('#session-tools summary').click();
  const saved = JSON.parse(await downloaded(page, page.locator('#export-session'), 'session.json'));
  expect(saved.answers).toHaveLength(2);
  expect(saved.feedback).toBe(true);
});

test('tabs stay synchronized and reject stale and concurrent answers', async ({page, context}) => {
  await start(page);
  const other = await context.newPage();
  await start(other);
  const stale = await page.evaluate(() => WorkshopWeb.request('/api/session'));
  await choose(page, 0);
  await expect(other.locator('.dialogue')).toBeVisible();
  const rejected = await other.evaluate(async token => {
    try { await WorkshopWeb.request('/api/answer', {headers: {'X-Workshop-Token': token}, body: JSON.stringify({cursor: 0, choice: 'explore'})}); return false; }
    catch { return true; }
  }, stale.token);
  expect(rejected).toBe(true);
  await next(other);
  await expect(page.locator('#question h2')).toHaveText(lesson.steps[1].title);
  const current = await page.evaluate(() => WorkshopWeb.request('/api/session'));
  const race = async tab => tab.evaluate(async token => {
    try { await WorkshopWeb.request('/api/answer', {headers: {'X-Workshop-Token': token}, body: JSON.stringify({cursor: 1, choice: 'explore'})}); return true; }
    catch { return false; }
  }, current.token);
  expect((await Promise.all([race(page), race(other)])).filter(Boolean)).toHaveLength(1);
  expect((await state(page)).answers).toHaveLength(2);
  await other.close();
});

test('a full storage quota preserves the new answer in a downloadable session', async ({page}) => {
  await start(page);
  await choose(page, 0);
  await next(page);
  await page.evaluate(() => { Storage.prototype.setItem = () => { throw new DOMException('Full', 'QuotaExceededError'); }; });
  await choose(page, 1);
  await expect(page.locator('#storage-notice')).toBeVisible();
  await expect(page.locator('#save-status')).toContainText('temporal');
  await page.locator('#session-tools summary').click();
  const saved = JSON.parse(await downloaded(page, page.locator('#export-session'), 'session.json'));
  expect(saved.answers).toHaveLength(2);
  expect((await state(page)).answers).toHaveLength(1);
});

test('a browser denying persistent locks still offers a temporary practice', async ({page}) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'locks', {value: {request: async () => { throw new DOMException('Blocked', 'SecurityError'); }}});
  });
  await start(page);
  await choose(page, 0);
  await expect(page.locator('#storage-notice')).toBeVisible();
  await page.locator('#session-tools summary').click();
  const saved = JSON.parse(await downloaded(page, page.locator('#export-session'), 'session.json'));
  expect(saved.answers).toHaveLength(1);
});

test('another tab cannot silently lose answers during a pending import', async ({page, context}) => {
  await start(page);
  const empty = await state(page);
  await upload(page, empty);
  const other = await context.newPage();
  await start(other);
  await choose(other, 0);
  await expect(page.locator('.dialogue')).toBeVisible();
  await page.locator('#confirm-replace').click();
  await expect(page.locator('#file-status')).toContainText('otra pestaña');
  expect((await state(page)).answers).toHaveLength(1);
  await other.close();
});

test('keyboard, board expansion and small screens remain usable', async ({page}) => {
  await start(page);
  await page.locator('.option').first().focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.coach')).toBeVisible();
  await expect(page.locator('#exercise')).toBeFocused();
  await page.locator('#expand-board').click();
  await expect(page.locator('#expand-board')).toHaveAttribute('aria-expanded', 'true');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator('#expand-board').click();
  await expect(page.locator('#exercise')).toBeVisible();
  await expect(page.locator('#exercise')).toBeFocused();
  await expect(page.locator('#question h2')).toBeInViewport();
  for (const phase of lesson.phases) {
    await page.locator('.filter').filter({hasText: `${phase.id} ·`}).click();
    await expect(page.locator('#notes .map-title')).toHaveText(lesson.boards[phase.id].title);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
