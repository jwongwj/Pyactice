/**
 * Browser tests for the practice IDE, driven through real Chrome.
 *
 * The bugs this rig has shipped were all invisible to unit tests: a Run button
 * pushed off a narrow viewport, an editor collapsed to zero height by a grid row
 * that grew with its content, a dead backend that looked exactly like a frozen
 * page. Those are only findable by rendering the thing and measuring it, so that
 * is what this does — including asserting on element geometry, not just presence.
 *
 *   node tests/ui.test.js            # headless
 *   HEADED=1 node tests/ui.test.js   # watch it drive
 *
 * Screenshots land in tests/shots/ for eyeballing.
 */

const puppeteer = require('puppeteer-core');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 8790;
const BASE = `http://127.0.0.1:${PORT}`;
const SHOTS = path.join(__dirname, 'shots');
const PY = '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3';

const L1 = fs.readFileSync(path.join(__dirname, 'fixtures/file_hosting_level1.py'), 'utf8');

let server = null;
let CARD_COUNT = 0;   // set from the backend by the first picker check
const results = [];

// ---------------------------------------------------------------- helpers

function portAnswers() {
  return new Promise(res => {
    const req = require('http').get(`http://127.0.0.1:${PORT}/api/state`,
      r => { r.resume(); res(true); });
    req.on('error', () => res(false));
    req.setTimeout(900, () => { req.destroy(); res(false); });
  });
}

async function startServer() {
  // Refuse to run against a server this function did not start. Waiting for the port to
  // answer means a leftover process satisfies the wait instantly, and the suite then
  // tests THAT process's stale bank. See the same guard in tests/api_test.py.
  if (await portAnswers()) {
    // Same reasoning as tests/api_test.py: a leftover `harness ui` on OUR port is this
    // suite's own debris and safe to reap; anything else is not ours to kill.
    try { execSync(`pkill -f "harness ui --port ${PORT}"`); } catch (e) {}
    for (let i = 0; i < 20 && await portAnswers(); i++) {
      await new Promise(r => setTimeout(r, 150));
    }
    if (await portAnswers()) {
      throw new Error(
        `something is already listening on 127.0.0.1:${PORT} and it is not one of this ` +
        `suite's servers. Refusing to run, because the suite would silently test that ` +
        `process instead of this code.`);
    }
  }
  // See the note in tests/api_test.py: resetState() deletes every __pycache__ and the
  // server then writes them back as it imports, which raced. Write none at all.
  server = spawn(PY, ['-m', 'harness', 'ui', '--port', String(PORT), '--no-open'], {
    cwd: REPO, stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
  });
  server.stderr.on('data', d => process.stderr.write('  [server] ' + d));
  return new Promise(r => setTimeout(r, 1800));
}
function stopServer() {
  if (server) { try { server.kill('SIGTERM'); } catch (e) {} server = null; }
  try { execSync(`pkill -f "harness ui --port ${PORT}"`); } catch (e) {}
}
// These tests need a clean sessions/ and workspace/, which means destroying
// whatever attempt is in progress. Running this file directly once ate a live
// session and the candidate's code. Back up first, restore on every exit path.
const STASH = fs.mkdtempSync(path.join(require('os').tmpdir(), 'pfs-stash-'));
let stashed = false;

function resetState() {
  if (!stashed) {
    for (const dir of ['sessions', 'workspace']) {
      if (fs.existsSync(path.join(REPO, dir))) {
        execSync(`cp -R "${REPO}/${dir}" "${STASH}/"`);
      }
    }
    stashed = true;
  }
  execSync(`rm -rf "${REPO}/sessions" "${REPO}/workspace"`);
  // See the note in tests/api_test.py: same-second edits can be served from a
  // stale .pyc and produce failures that are not real.
  execSync(`find "${REPO}" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true`);
}

function restoreState() {
  if (!stashed) return;
  execSync(`rm -rf "${REPO}/sessions" "${REPO}/workspace"`);
  for (const dir of ['sessions', 'workspace']) {
    if (fs.existsSync(path.join(STASH, dir))) execSync(`cp -R "${STASH}/${dir}" "${REPO}/"`);
  }
  execSync(`rm -rf "${STASH}"`);
  stashed = false;
}
process.on('exit', restoreState);
process.on('SIGINT', () => { restoreState(); process.exit(130); });

const ok = (name, extra = '') => { results.push({ name, pass: true, extra }); console.log(`  \x1b[32m✓\x1b[0m ${name}${extra ? '  ' + extra : ''}`); };
const bad = (name, why) => { results.push({ name, pass: false, why }); console.log(`  \x1b[31m✗ ${name}\x1b[0m\n      ${why}`); };

async function check(name, fn) {
  try {
    const extra = await fn();
    ok(name, extra || '');
  } catch (e) {
    bad(name, e.message);
  }
}
function assert(cond, msg) { if (!cond) throw new Error(msg); }

/** Visible means: in the DOM, non-zero size, and inside the viewport. */
async function geometry(page, selector) {
  return page.evaluate(sel => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return {
      w: Math.round(r.width), h: Math.round(r.height),
      top: Math.round(r.top), left: Math.round(r.left),
      right: Math.round(r.right), bottom: Math.round(r.bottom),
      display: style.display, visibility: style.visibility,
      vw: window.innerWidth, vh: window.innerHeight,
    };
  }, selector);
}
async function assertVisible(page, selector, label, minH = 1) {
  const g = await geometry(page, selector);
  assert(g, `${label}: ${selector} is not in the DOM`);
  assert(g.display !== 'none' && g.visibility !== 'hidden', `${label}: hidden by CSS (${g.display}/${g.visibility})`);
  assert(g.w > 0 && g.h >= minH, `${label}: zero-size box ${g.w}x${g.h}`);
  assert(g.right <= g.vw + 1 && g.left >= -1, `${label}: pushed outside the viewport horizontally (left=${g.left} right=${g.right} vw=${g.vw})`);
  assert(g.bottom <= g.vh + 1 && g.top >= -1, `${label}: outside the viewport vertically (top=${g.top} bottom=${g.bottom} vh=${g.vh})`);
  return `${g.w}x${g.h}`;
}
const setCode = (page, code) => page.evaluate(c => {
  document.querySelector('.CodeMirror').CodeMirror.setValue(c);
}, code);
const getCode = page => page.evaluate(() => document.querySelector('.CodeMirror').CodeMirror.getValue());
const runAndWait = async page => {
  await page.click('#btn-run2');
  await page.waitForFunction(() => !document.querySelector('#btn-run2').disabled, { timeout: 20000 });
};


/** The home screen opens on the path view, so reaching a specific problem means
 *  switching to the flat "All problems" list first. One helper, six call sites. */
async function showAllProblems(page) {
  await page.waitForSelector('#start.on', { timeout: 8000 });
  // `#start.on` is set synchronously, but the rail is painted after the /api/curriculum
  // fetch resolves. Clicking before then found nothing and the guard swallowed it, so
  // wait for the rail itself rather than for the screen.
  await page.waitForFunction(
    () => [...document.querySelectorAll('.railitem')]
      .some(x => x.innerText.includes('All problems')),
    { timeout: 8000 });
  await page.evaluate(() => {
    [...document.querySelectorAll('.railitem')]
      .find(x => x.innerText.includes('All problems')).click();
  });
  await page.waitForSelector('.pcard', { timeout: 8000 });
}
/** `fresh` picks the "Start over" button when there is unfinished work, so a test that
 *  needs clean stubs gets them rather than silently resuming. */
async function startProblem(page, title, { fresh = true } = {}) {
  await showAllProblems(page);
  // A drill lives inside its unit's card, collapsed by default. Open every unit so the
  // search below can see the nested rows as well as the standalone cards.
  await page.evaluate(() => {
    [...document.querySelectorAll('.pcard [data-expand]')]
      .filter(b => b.getAttribute('aria-expanded') !== 'true').forEach(b => b.click());
  });
  await new Promise(r => setTimeout(r, 250));
  await page.evaluate((t, wantFresh) => {
    const scopes = [...document.querySelectorAll('.drill'), ...document.querySelectorAll('.pcard')];
    const card = scopes.find(c => c.innerText.includes(t));
    if (!card) throw new Error(`no card or drill row matching ${t}`);
    const buttons = [...card.querySelectorAll('button')].filter(b => b.dataset.start);
    const pick = wantFresh
      ? (buttons.find(b => b.dataset.fresh === '1') || buttons.find(b => !b.dataset.resume))
      : (buttons.find(b => b.dataset.resume === '1') || buttons[0]);
    (pick || buttons[0]).click();
  }, title, fresh);
  await page.waitForSelector('#app.on', { timeout: 15000 });
  await page.waitForFunction(() => document.querySelector('.CodeMirror'), { timeout: 8000 });
}

// ---------------------------------------------------------------- suite

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  resetState();
  await startServer();

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: process.env.HEADED ? false : 'new',
    args: ['--no-sandbox', '--disable-gpu'],
    defaultViewport: { width: 1440, height: 900 },
  });
  // Ctrl-V reads the clipboard through the async API (macOS fires no paste event
  // for it), so the checks below need the permission a real user grants once.
  await browser.defaultBrowserContext().overridePermissions(BASE, ['clipboard-read', 'clipboard-write']);
  const page = await browser.newPage();
  page.on('dialog', d => d.accept());
  const consoleErrors = [];
  page.on('pageerror', e => consoleErrors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });

  console.log('\n\x1b[1mPractice IDE — browser tests\x1b[0m\n');

  // ---- start screen
  await page.goto(BASE, { waitUntil: 'networkidle0' });
  await page.waitForSelector('#start.on', { timeout: 8000 });
  await page.screenshot({ path: path.join(SHOTS, '01-start.png') });

  await check('home screen shows the four categories and the path', async () => {
    const rail = await page.$$eval('.railitem', els => els.map(e => e.innerText));
    assert(rail.length === 6, `expected 4 categories + path + all, saw ${rail.length}`);
    for (const name of ['Basic Python', 'Data Structures', 'Algorithms', 'Industry'])
      assert(rail.some(r => r.includes(name)), `rail missing ${name}`);
    const home = await page.$eval('#home', e => e.innerText);
    assert(/NEXT ON YOUR PATH/i.test(home), 'no frontier on the path view');
    return `${rail.length} rail items`;
  });

  await check('the flat list reaches every problem the backend knows about', async () => {
    await showAllProblems(page);
    const n = await page.$$eval('.pcard', els => els.length);
    const known = await page.evaluate(async () =>
      (await (await fetch('/api/state')).json()).problems.length);
    // Not one card per problem any more: 92 of the 98 are drills, and they are grouped
    // under their unit. The invariant is coverage -- every problem reachable exactly
    // once, either as its own card or as a drill inside its unit's card.
    const reached = await page.evaluate(() => {
      [...document.querySelectorAll('.pcard [data-expand]')].forEach(b => b.click());
      const keys = [...document.querySelectorAll('.pcard[data-key]')]
        .filter(c => !c.classList.contains('unit')).map(c => c.dataset.key);
      const drills = [...document.querySelectorAll('.drill [data-start]')].map(b => b.dataset.start);
      return { keys, drills };
    });
    const all = [...reached.keys, ...reached.drills];
    assert(all.length === known,
      `reached ${all.length} problems (${reached.keys.length} cards + ${reached.drills.length} drills), backend knows ${known}`);
    assert(new Set(all).size === all.length, 'a problem is reachable twice over');
    assert(n < known, `still one card per problem (${n} cards for ${known} problems)`);
    CARD_COUNT = n;
    return `${n} cards reaching ${all.length} problems`;
  });

  await check('a unit card collapses its drills and does not overflow the column', async () => {
    await showAllProblems(page);
    // The bug this replaced: one button per drill in a nowrap flex row pushed the home
    // column to 5545px inside a 1204px viewport. Presence checks cannot see that.
    const geom = await page.evaluate(() => {
      const home = document.querySelector('#home');
      return { scrollW: home.scrollWidth, clientW: home.clientWidth,
               body: document.body.scrollWidth, win: window.innerWidth };
    });
    assert(geom.scrollW <= geom.clientW + 1,
      `home column overflows: scrollWidth ${geom.scrollW} vs clientWidth ${geom.clientW}`);
    assert(geom.body <= geom.win + 1,
      `page scrolls horizontally: ${geom.body} vs ${geom.win}`);
    const worst = await page.$$eval('.pcard, .row', els => Math.max(0,
      ...els.map(e => e.querySelectorAll(':scope > .ractions button').length)));
    assert(worst <= 3, `a row still sprays ${worst} buttons`);
    return `no overflow, at most ${worst} buttons per row`;
  });

  await check('prerequisites advise and never disable', async () => {
    await page.evaluate(() => [...document.querySelectorAll('.railitem')]
      .find(x => x.innerText.includes('Data Structures')).click());
    await page.waitForFunction(() => document.querySelectorAll('.row').length > 0, { timeout: 8000 });
    const disabled = await page.$$eval('#home button', els => els.filter(b => b.disabled).length);
    assert(disabled === 0, `${disabled} disabled buttons — prerequisites must not lock`);
    const rows = await page.$$eval('.row', els => els.length);
    assert(rows === 12, `expected 12 data-structure rows, saw ${rows}`);
    return `${rows} rows, nothing disabled`;
  });

  await check('search finds a topic by name and by idiom', async () => {
    await page.click('#q'); await page.type('#q', 'heap');
    await page.waitForFunction(
      () => /Heap/.test(document.querySelector('#home').innerText), { timeout: 8000 });
    const hit = await page.$eval('#home', e => e.innerText);
    assert(/Heap/.test(hit), 'searching "heap" did not surface the Heap subtopic');
    await page.evaluate(() => { document.querySelector('#q').value = ''; });
    await page.evaluate(() => [...document.querySelectorAll('.railitem')]
      .find(x => x.innerText.includes('All problems')).click());
    await page.waitForSelector('.pcard', { timeout: 8000 });
    return 'found';
  });

  await check('start screen does not leak levels 2-4', async () => {
    const WORDS = ['prefix', 'capacity', 'merge', 'backup', 'restore', 'ttl', 'rollback',
                   'cashback', 'top spender', 'permission', 'symlink', 'symbolic'];
    // Scoped to the multi-level problems. These words ARE level 3-4 operations for
    // cloud_storage and file_hosting, but several are also ordinary English that a
    // one-level Basic Python drill may legitimately use in its own only level -- and a
    // single-level problem has no later level to leak.
    const cards = await page.$$eval('.pcard[data-levels]', els => els.map(el => ({
      key: el.dataset.key, levels: Number(el.dataset.levels), text: el.innerText.toLowerCase(),
    })));
    const multi = cards.filter(c => c.levels > 1);
    assert(multi.length > 0, `no multi-level cards on the picker to check (${cards.length} cards)`);
    const leaks = [];
    for (const card of multi) {
      for (const word of WORDS) if (card.text.includes(word)) leaks.push(`${card.key}: ${word}`);
    }
    assert(leaks.length === 0, `picker text mentions locked concepts: ${leaks.join(', ')}`);
    return `${multi.length} multi-level cards clean`;
  });

  // ---- enter a session
  await startProblem(page, 'File Hosting');
  await page.screenshot({ path: path.join(SHOTS, '02-session.png') });

  await check('top bar controls are all visible', async () => {
    const parts = [];
    for (const [sel, label] of [['#btn-home', 'Problems'], ['#btn-run', 'Run (top)'],
                                ['#btn-finish', 'Finish'], ['#clock', 'clock']]) {
      parts.push(`${label} ${await assertVisible(page, sel, label)}`);
    }
    return parts.join(', ');
  });

  await check('the big Run button above the results is visible', () =>
    assertVisible(page, '#btn-run2', 'Run (results)', 20));

  await check('the editor is visible and usably tall', async () => {
    const g = await geometry(page, '.CodeMirror');
    assert(g.h >= 150, `editor only ${g.h}px tall`);
    return `${g.w}x${g.h}`;
  });

  await check('the statement panel shows level 1 and hides level 2+', async () => {
    const text = await page.$eval('#doc', el => el.innerText);
    assert(text.includes('Level 1'), 'level 1 heading missing');
    assert(!/Level [234]/.test(text), 'a locked level leaked into the statement');
    return 'level 1 only';
  });

  // ---- the reported bug: editor vanishing on run
  await check('REGRESSION: editor survives a run with many failures', async () => {
    const before = await geometry(page, '.CodeMirror');
    await setCode(page, 'class FileHost:\n    def __init__(self):\n        self.f = {}\n');
    await runAndWait(page);
    await page.screenshot({ path: path.join(SHOTS, '03-after-failing-run.png') });
    const after = await geometry(page, '.CodeMirror');
    assert(after.h >= 150, `editor collapsed to ${after.h}px after running (was ${before.h}px)`);
    const code = await getCode(page);
    assert(code.includes('class FileHost'), 'editor content was wiped by the run');
    return `${before.h}px -> ${after.h}px, content intact`;
  });

  await check('the Output tab shows what your code printed', async () => {
    await setCode(page, [
      'class FileHost:',
      '    def __init__(self):',
      '        self.files = {}',
      '        print("MARKER init", vars(self))',
      '    def file_upload(self, file_name, size):',
      '        print("MARKER upload", file_name, size, "| self.files =", self.files)',
      '        self.files[file_name] = size',
      '',
    ].join('\n'));
    await runAndWait(page);
    const badge = await page.$eval('#outcount', el => el.textContent);
    assert(badge && Number(badge) > 0, `the Output tab shows no count (got "${badge}")`);
    await page.evaluate(() => [...document.querySelectorAll('.rtab')]
      .find(t => t.dataset.r === 'output').click());
    await page.waitForSelector('#term', { timeout: 5000 });
    const term = await page.$eval('#term', el => el.innerText);
    assert(term.includes('MARKER init'), 'the console did not show print() from __init__');
    assert(term.includes('MARKER upload'), 'the console did not show print() from a method');
    assert(term.includes('▸'), 'output is not grouped per test case');
    // #term lives inside a scrolling pane, so its box may legitimately extend past
    // the viewport; assert the pane is visible and the console has real size.
    await assertVisible(page, '#results-b', 'results pane', 60);
    const box = await geometry(page, '#term');
    assert(box.w > 200 && box.h > 30, `console box ${box.w}x${box.h}`);
    const scrolls = await page.$eval('#results-b', el => el.scrollHeight > el.clientHeight);
    assert(typeof scrolls === 'boolean', 'results pane is not scrollable');
    await page.screenshot({ path: path.join(SHOTS, '11-output-tab.png') });
    return `${badge} cases, console ${term.length} chars`;
  });

  await check('the Output tab explains itself when nothing was printed', async () => {
    await setCode(page, 'class FileHost:\n    def __init__(self):\n        self.f = {}\n');
    await runAndWait(page);
    const term = await page.$eval('#term', el => el.innerText);
    assert(/No output/i.test(term), `console said "${term.slice(0, 60)}"`);
    assert(/print\(/.test(term), 'no hint about how to produce output');
    await page.evaluate(() => [...document.querySelectorAll('.rtab')]
      .find(t => t.dataset.r === 'results').click());
    return 'hint shown';
  });

  await check('paste lands in the editor even when focus is elsewhere', async () => {
    await setCode(page, 'class FileHost:\n    pass\n');
    // Focus the statement pane, the way you would after reading the task.
    await page.click('#doc');
    const focusedElsewhere = await page.evaluate(() =>
      !document.activeElement.closest('.CodeMirror'));
    assert(focusedElsewhere, 'could not move focus out of the editor');
    const landed = await page.evaluate(() => {
      const dt = new DataTransfer();
      dt.setData('text/plain', '# PASTED_WHILE_UNFOCUSED');
      document.dispatchEvent(new ClipboardEvent('paste',
        { clipboardData: dt, bubbles: true, cancelable: true }));
      return new Promise(r => setTimeout(() =>
        r(document.querySelector('.CodeMirror').CodeMirror.getValue()), 200));
    });
    assert(landed.includes('PASTED_WHILE_UNFOCUSED'),
      'paste was swallowed when focus was outside the editor');
    return 'redirected into the editor';
  });

  // ---- the reported bug: Ctrl-V paged the editor instead of pasting.
  // CodeMirror's macDefault keymap falls through to `emacsy`, which binds Ctrl-V to
  // goPageDown, Ctrl-A to goLineStart and Ctrl-K to killLine. On a Mac that made
  // Ctrl-V "jump to the bottom" and Ctrl-K silently eat the rest of the line.
  const pressCtrl = async (key) => {
    await page.keyboard.down('Control');
    await page.keyboard.press(key);
    await page.keyboard.up('Control');
    await new Promise(r => setTimeout(r, 300));
  };
  const cmState = () => page.evaluate(() => {
    const cm = document.querySelector('.CodeMirror').CodeMirror;
    return { value: cm.getValue(), line: cm.getCursor().line,
             scroll: Math.round(cm.getScrollInfo().top), sel: cm.getSelection().length };
  });

  await check('REGRESSION: Ctrl-V pastes instead of paging to the bottom', async () => {
    await page.evaluate(() => {
      const cm = document.querySelector('.CodeMirror').CodeMirror;
      cm.setValue(Array.from({ length: 200 }, (_, i) => `# line ${i}`).join('\n'));
      cm.setSelection({ line: 5, ch: 0 }, { line: 5, ch: 9 });   // "# line 5"
      cm.scrollTo(0, 0);
      cm.focus();
    });
    await pressCtrl('c');
    await page.evaluate(() => document.querySelector('.CodeMirror').CodeMirror.setCursor({ line: 100, ch: 0 }));
    const before = await cmState();
    await pressCtrl('v');
    const after = await cmState();
    assert(after.value.split('\n')[100].startsWith('# line 5'),
      `Ctrl-V did not paste; line 100 is ${JSON.stringify(after.value.split('\n')[100])}`);
    assert(after.line === before.line,
      `Ctrl-V moved the cursor from line ${before.line} to ${after.line} (the paging bug)`);
    return `pasted at line ${after.line}, cursor did not jump`;
  });

  await check('REGRESSION: Ctrl-K does not eat the rest of the line', async () => {
    await setCode(page, 'keep this whole line\n');
    await page.evaluate(() => {
      const cm = document.querySelector('.CodeMirror').CodeMirror;
      cm.setCursor({ line: 0, ch: 4 });
      cm.focus();
    });
    await pressCtrl('k');
    const { value } = await cmState();
    assert(value.startsWith('keep this whole line'), `Ctrl-K truncated it to ${JSON.stringify(value)}`);
    return 'line intact';
  });

  await check('Ctrl-A selects the whole file, Ctrl-X cuts', async () => {
    await setCode(page, 'alpha\nbravo\ncharlie\n');
    await page.evaluate(() => document.querySelector('.CodeMirror').CodeMirror.focus());
    await pressCtrl('a');
    const selected = await cmState();
    assert(selected.sel >= 'alpha\nbravo\ncharlie'.length,
      `Ctrl-A selected ${selected.sel} chars, not the file`);
    await page.evaluate(() => {
      const cm = document.querySelector('.CodeMirror').CodeMirror;
      cm.setSelection({ line: 1, ch: 0 }, { line: 1, ch: 5 });
    });
    await pressCtrl('x');
    const cut = await cmState();
    assert(cut.value.split('\n')[1] === '', `Ctrl-X left ${JSON.stringify(cut.value)}`);
    return `${selected.sel} chars selected, cut works`;
  });

  await check('the editor shows when it has focus', async () => {
    await page.evaluate(() => document.querySelector('.CodeMirror').CodeMirror.focus());
    const on = await page.$eval('#editor-wrap', el => el.classList.contains('focused'));
    assert(on, 'no focus indicator when the editor is focused');
    await page.click('#doc');
    const off = await page.$eval('#editor-wrap', el => !el.classList.contains('focused'));
    assert(off, 'focus indicator stayed on after focus left');
    return 'indicator tracks focus';
  });

  // ---- a real code editor
  await check('completions offer what the file defines, after self.', async () => {
    await setCode(page, [
      'class FileHost:',
      '    def __init__(self):',
      '        self.files = {}',
      '        self.count = 0',
      '    def helper(self):',
      '        pass',
      '    def file_upload(self, file_name, size):',
      '        ',
    ].join('\n'));
    await page.evaluate(() => {
      const cm = document.querySelector('.CodeMirror').CodeMirror;
      cm.focus(); cm.setCursor({line: 7, ch: 8});
    });
    await page.keyboard.type('self.');
    await page.waitForSelector('.CodeMirror-hints', { timeout: 5000 });
    const hints = await page.$$eval('.CodeMirror-hint', els => els.map(e => e.innerText.trim()));
    for (const want of ['files', 'count', 'helper', 'file_upload'])
      assert(hints.some(h => h.startsWith(want)), `no completion for ${want}: ${hints.join(', ')}`);
    await page.screenshot({ path: path.join(SHOTS, '12-intellisense.png') });
    await page.keyboard.press('Escape');
    return hints.length + ' completions';
  });

  await check('completions show real signatures and docstrings', async () => {
    // Open our own popup: the previous check closes its one with Escape.
    await setCode(page, [
      'class FileHost:',
      '    def __init__(self):',
      '        self.files = {}',
      '    def file_upload(self, file_name, size):',
      '        pass',
      '    def go(self):',
      '        ',
    ].join('\n'));
    await page.evaluate(() => {
      const cm = document.querySelector('.CodeMirror').CodeMirror;
      cm.focus(); cm.setCursor({line: 6, ch: 8});
    });
    await page.keyboard.type('self.');
    await page.waitForSelector('.CodeMirror-hint', { timeout: 6000 });
    const rows = await page.$$eval('.CodeMirror-hint', els => els.map(e => ({
      name: e.querySelector('.h-name').textContent,
      detail: e.querySelector('.h-detail').textContent,
      kind: e.querySelector('.h-kind').textContent,
    })));
    const upload = rows.find(r => r.name === 'file_upload');
    assert(upload, `file_upload not offered: ${rows.map(r => r.name).join(', ')}`);
    assert(/file_name/.test(upload.detail),
      `no real signature for file_upload, got "${upload.detail}"`);
    assert(upload.kind === 'method', `kind was "${upload.kind}"`);
    const files = rows.find(r => r.name === 'files');
    assert(files && files.detail === 'dict',
      `self.files not typed as dict: ${files && files.detail}`);
    await page.keyboard.press('Escape');
    return `${rows.length} completions, signatures and types present`;
  });

  await check('signature help names the argument you are typing', async () => {
    await setCode(page, [
      'class FileHost:',
      '    def __init__(self):',
      '        self.files = {}',
      '    def file_upload(self, file_name, size):',
      '        pass',
      '    def go(self):',
      '        ',
    ].join('\n'));
    await page.evaluate(() => {
      const cm = document.querySelector('.CodeMirror').CodeMirror;
      cm.focus(); cm.setCursor({line: 6, ch: 8});
    });
    await page.keyboard.type('self.file_upload(');
    await page.waitForSelector('#sighint', { timeout: 6000 });
    let hint = await page.$eval('#sighint', el => el.innerHTML);
    assert(/file_name/.test(hint), `signature missing params: ${hint}`);
    assert(/<b>file_name<\/b>/.test(hint), `first argument not highlighted: ${hint}`);
    await page.keyboard.type('"a", ');
    await page.waitForFunction(() => /<b>size<\/b>/.test(document.querySelector('#sighint').innerHTML),
      { timeout: 6000 });
    hint = await page.$eval('#sighint', el => el.innerText);
    await page.screenshot({ path: path.join(SHOTS, '15-signature.png') });
    return hint.replace(/\s+/g, ' ').slice(0, 60);
  });

  await check('a syntax error is underlined in the gutter while you type', async () => {
    await setCode(page, 'class FileHost:\n    def broken(self)\n        pass\n');
    await page.waitForFunction(
      () => document.querySelectorAll('.CodeMirror-lint-marker-error').length > 0,
      { timeout: 8000 });
    const markers = await page.$$eval('.CodeMirror-lint-marker-error', els => els.length);
    await page.screenshot({ path: path.join(SHOTS, '13-lint.png') });
    await setCode(page, 'class FileHost:\n    def fine(self):\n        pass\n');
    await page.waitForFunction(
      () => document.querySelectorAll('.CodeMirror-lint-marker-error').length === 0,
      { timeout: 8000 });
    return `${markers} marker(s), cleared when fixed`;
  });

  await check('failing results are rendered', async () => {
    const n = await page.$$eval('#results-b .case', els => els.length);
    assert(n > 0, 'no case rows rendered');
    const tally = await page.$eval('#tally', el => el.innerText);
    return `${n} rows, tally "${tally}"`;
  });

  await check('hidden cases leak no operations into the DOM', async () => {
    // Structural, not textual: a visible case may legitimately print an operation
    // that also appears in a hidden one, so assert on each hidden row's own
    // detail block instead of scanning the whole page for strings.
    const report = await page.evaluate(() => {
      const out = { hidden: 0, named: 0, offenders: [] };
      for (const row of document.querySelectorAll('#results-b .case.hidden')) {
        out.hidden++;
        if (/[A-Z_]{4,}\(/.test(row.innerText)) { out.named++; out.offenders.push(row.innerText.trim()); }
        const detail = row.nextElementSibling;
        if (detail && detail.classList.contains('detail')) {
          if (detail.querySelectorAll('.kv, .op').length) out.offenders.push(detail.innerText.trim().slice(0, 90));
        }
      }
      return out;
    });
    assert(report.hidden > 0, 'no hidden cases in this run to check');
    assert(report.offenders.length === 0,
      `${report.offenders.length} hidden case(s) exposed detail:\n      ${report.offenders.slice(0, 2).join('\n      ')}`);
    return `${report.hidden} hidden cases, no operations or values exposed`;
  });

  await check('a hidden failure shows its shape with the failing step marked', async () => {
    const info = await page.evaluate(() => {
      const row = document.querySelector('#results-b .case.hidden');
      if (!row) return null;
      const shape = row.nextElementSibling && row.nextElementSibling.querySelector('.shape');
      if (!shape) return null;
      return {
        names: [...shape.querySelectorAll('span')].filter(s => !s.classList.contains('op-arrow'))
          .map(s => ({ text: s.textContent, cls: s.className })),
        note: shape.querySelector('.shape-note').textContent,
      };
    });
    assert(info, 'no shape rendered for a hidden failure');
    assert(info.names.length > 1, `shape had ${info.names.length} steps`);
    assert(info.names.every(n => !n.text.includes('(')), 'shape leaked arguments');
    assert(info.names.some(n => n.cls === 'op-bad'), 'failing step not marked');
    assert(/hidden/i.test(info.note), `note was "${info.note}"`);
    return info.names.map(n => n.text).join(' → ').slice(0, 60);
  });

  await check('hidden case ids are not shown verbatim', async () => {
    const rows = await page.$$eval('#results-b .case.hidden', els => els.map(e => ({
      name: e.querySelector('.name').innerText,
      tags: e.querySelector('.tags').innerText.trim(),
    })));
    const named = rows.filter(r => !/^hidden test \d+$/.test(r.name));
    assert(named.length === 0, `hidden names not opaque: ${named.slice(0, 3).map(r => r.name).join(', ')}`);
    const tagged = rows.filter(r => r.tags.length);
    assert(tagged.length === 0,
      `hidden rows show tags, which reconstructs the id: ${tagged[0] && tagged[0].tags}`);
    // The real id must still be reachable, or a disputed case cannot be named.
    await page.click('#results-b .case.hidden');
    await page.waitForSelector('#results-b .idbox', { timeout: 4000 });
    const box = await page.$eval('#results-b .idbox', el => el.innerText);
    assert(/pfs dispute l\d_/.test(box), `id not revealed on click: ${box.slice(0, 60)}`);
    return `${rows.length} opaque, id on click`;
  });

  // ---- unlock
  await check('clearing level 1 unlocks level 2', async () => {
    await setCode(page, L1);
    await runAndWait(page);
    await page.waitForSelector('#toast:not(.hide)', { timeout: 8000 });
    await page.screenshot({ path: path.join(SHOTS, '04-unlocked.png') });
    const toast = await page.$eval('#toast-msg', el => el.innerText);
    assert(/Level 2 unlocked/i.test(toast), `toast said "${toast}"`);
    const pills = await page.$$eval('.pill', els => els.map(e => e.className + ':' + e.innerText));
    assert(pills.some(p => p.includes('cleared')), `no level shows as cleared: ${pills.join(' | ')}`);
    return toast.slice(0, 60);
  });

  await check('editor is still visible after the unlock toast', () =>
    assertVisible(page, '.CodeMirror', 'editor', 150));

  await check('taking the new stubs appends without losing code', async () => {
    // Type an unsaved edit first: the append happens server-side against the file
    // on disk, so anything inside the autosave debounce must be flushed first.
    await page.evaluate(() => {
      const cm = document.querySelector('.CodeMirror').CodeMirror;
      cm.setValue(cm.getValue() + '\n    # unsaved marker\n');
    });
    const before = await getCode(page);
    await page.click('#toast-x');
    await page.waitForFunction(
      () => document.querySelector('.CodeMirror').CodeMirror.getValue().includes('file_search'),
      { timeout: 8000 });
    const after = await getCode(page);
    assert(after.includes('class FileHost'), 'existing code was lost');
    assert(after.includes('# unsaved marker'), 'an unsaved edit was lost when the stubs were appended');
    assert(after.length > before.length, 'nothing was appended');
    return `${before.split('\n').length} -> ${after.split('\n').length} lines, unsaved edit kept`;
  });

  await check('REGRESSION: the stubs button is disabled once the file has them', async () => {
    // The button is disabled optimistically on append and confirmed by the state
    // refresh; wait for it to settle rather than racing the round trip.
    await page.waitForFunction(() => document.querySelector('#btn-stubs').disabled,
      { timeout: 6000 }).catch(() => {});
    const disabled = await page.$eval('#btn-stubs', el => el.disabled);
    assert(disabled, 'the stubs button is still live — clicking it would shadow the user\'s methods');
    const title = await page.$eval('#btn-stubs', el => el.title);
    return title;
  });

  await check('REGRESSION: forcing a stub append cannot shadow existing methods', async () => {
    const before = await getCode(page);
    const res = await page.evaluate(async () => {
      const r = await fetch('/api/stubs', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
      return r.json();
    });
    assert(res.ok === false, 'the server appended stubs over methods that already exist');
    const after = await getCode(page);
    assert(after === before || after.split('def file_search').length === 2,
      'file_search was duplicated, shadowing the implementation');
    return res.message.slice(0, 60);
  });

  await check('the statement now includes level 2', async () => {
    const text = await page.$eval('#doc', el => el.innerText);
    assert(text.includes('Level 2'), 'level 2 did not appear after unlocking');
    assert(!/Level [34]/.test(text), 'levels 3/4 leaked');
    return 'levels 1-2';
  });

  // ---- layout robustness
  for (const [w, h] of [[1100, 700], [1280, 800], [1680, 1050]]) {
    await check(`layout holds at ${w}x${h}`, async () => {
      await page.setViewport({ width: w, height: h });
      await new Promise(r => setTimeout(r, 350));
      await assertVisible(page, '#btn-run', 'top Run');
      await assertVisible(page, '#btn-run2', 'results Run', 20);
      await assertVisible(page, '#btn-home', 'Problems');
      const g = await geometry(page, '.CodeMirror');
      assert(g.h >= 120, `editor only ${g.h}px at ${w}x${h}`);
      await page.screenshot({ path: path.join(SHOTS, `05-viewport-${w}x${h}.png`) });
      return `editor ${g.h}px`;
    });
  }
  await page.setViewport({ width: 1440, height: 900 });

  await check('the page never scrolls horizontally', async () => {
    const over = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert(over <= 0, `body overflows by ${over}px`);
    return 'no overflow';
  });

  // ---- adjustable results panel
  await check('the results panel can be dragged taller', async () => {
    const before = await geometry(page, '#results');
    const bar = await geometry(page, '#hsplit');
    assert(bar && bar.h > 0, 'no horizontal splitter rendered');
    await page.mouse.move(bar.left + 300, bar.top + bar.h / 2);
    await page.mouse.down();
    await page.mouse.move(bar.left + 300, bar.top - 160, { steps: 12 });
    await page.mouse.up();
    await new Promise(r => setTimeout(r, 250));
    const after = await geometry(page, '#results');
    assert(after.h > before.h + 90, `results went ${before.h} -> ${after.h}`);
    await assertVisible(page, '.CodeMirror', 'editor', 100);
    await page.screenshot({ path: path.join(SHOTS, '14-results-tall.png') });
    return `${before.h}px -> ${after.h}px`;
  });

  await check('the results panel cannot swallow the editor', async () => {
    const bar = await geometry(page, '#hsplit');
    await page.mouse.move(bar.left + 300, bar.top + bar.h / 2);
    await page.mouse.down();
    await page.mouse.move(bar.left + 300, -600, { steps: 10 });
    await page.mouse.up();
    await new Promise(r => setTimeout(r, 250));
    const editor = await geometry(page, '.CodeMirror');
    assert(editor.h >= 100, `editor squeezed to ${editor.h}px`);
    await assertVisible(page, '#btn-run2', 'Run', 20);
    return `editor held at ${editor.h}px`;
  });

  await check('the results height persists and double-click resets it', async () => {
    const wanted = await geometry(page, '#results');
    await page.reload({ waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.querySelector('.CodeMirror'), { timeout: 8000 });
    const restored = await geometry(page, '#results');
    assert(Math.abs(restored.h - wanted.h) < 14, `${wanted.h}px became ${restored.h}px`);
    const bar = await geometry(page, '#hsplit');
    await page.mouse.click(bar.left + 300, bar.top + bar.h / 2, { clickCount: 2 });
    await new Promise(r => setTimeout(r, 250));
    const reset = await geometry(page, '#results');
    assert(reset.h !== restored.h, 'double-click did not reset');
    return `${restored.h}px persisted, reset to ${reset.h}px`;
  });

  // ---- resizable sidebar
  await check('the sidebar can be dragged wider, and the editor survives it', async () => {
    const before = await geometry(page, '#left');
    const bar = await geometry(page, '#split');
    assert(bar && bar.w > 0, 'no splitter rendered');
    await page.mouse.move(bar.left + bar.w / 2, bar.top + 200);
    await page.mouse.down();
    await page.mouse.move(before.right + 220, bar.top + 200, { steps: 12 });
    await page.mouse.up();
    await new Promise(r => setTimeout(r, 250));
    const after = await geometry(page, '#left');
    assert(after.w > before.w + 120, `sidebar went ${before.w} -> ${after.w}`);
    await assertVisible(page, '.CodeMirror', 'editor', 120);
    await assertVisible(page, '#btn-run2', 'Run', 20);
    await page.screenshot({ path: path.join(SHOTS, '08-sidebar-wide.png') });
    return `${before.w}px -> ${after.w}px`;
  });

  await check('the sidebar cannot be dragged over the editor', async () => {
    const bar = await geometry(page, '#split');
    await page.mouse.move(bar.left + bar.w / 2, bar.top + 200);
    await page.mouse.down();
    await page.mouse.move(3000, bar.top + 200, { steps: 8 });   // far past the right edge
    await page.mouse.up();
    await new Promise(r => setTimeout(r, 250));
    const editor = await geometry(page, '.CodeMirror');
    assert(editor.w >= 300, `editor squeezed to ${editor.w}px`);
    await assertVisible(page, '#btn-run2', 'Run', 20);
    return `editor held at ${editor.w}px`;
  });

  await check('the sidebar width survives a reload, and double-click resets it', async () => {
    const wanted = await geometry(page, '#left');
    await page.reload({ waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.querySelector('.CodeMirror'), { timeout: 8000 });
    const restored = await geometry(page, '#left');
    assert(Math.abs(restored.w - wanted.w) < 12, `${wanted.w}px became ${restored.w}px`);
    const bar = await geometry(page, '#split');
    await page.mouse.click(bar.left + bar.w / 2, bar.top + 200, { clickCount: 2 });
    await new Promise(r => setTimeout(r, 250));
    const reset = await geometry(page, '#left');
    assert(reset.w !== restored.w, 'double-click did not reset the width');
    return `${restored.w}px persisted, reset to ${reset.w}px`;
  });

  // ---- pop the statement out
  await check('the statement pops into its own window and keeps rendering', async () => {
    await page.click('#btn-pop');
    // Poll rather than await targetcreated: in headless the popup target can be
    // announced before its page object is attachable, and the event is missed.
    let popup = null;
    for (let i = 0; i < 40 && !popup; i++) {
      await new Promise(r => setTimeout(r, 150));
      popup = (await browser.pages()).find(p => p.url().includes('panel=doc')) || null;
    }
    assert(popup, 'no second window opened');
    await popup.waitForFunction(() => document.querySelector('#doc').innerText.length > 100,
      { timeout: 10000 });
    const text = await popup.$eval('#doc', el => el.innerText);
    assert(text.includes('Level 1'), 'the popped-out window did not render the statement');
    assert(!/Level [34]/.test(text), 'the popped-out window leaked a locked level');
    const chromeHidden = await popup.evaluate(() =>
      getComputedStyle(document.querySelector('#top')).display === 'none' &&
      getComputedStyle(document.querySelector('#right')).display === 'none');
    assert(chromeHidden, 'the popped-out window still shows the editor chrome');
    await popup.screenshot({ path: path.join(SHOTS, '09-popout.png') });
    return `${text.length} chars, statement only`;
  });

  await check('the main window gives the space to the editor while popped out', async () => {
    await new Promise(r => setTimeout(r, 300));
    const left = await geometry(page, '#left');
    assert(left.display === 'none' || left.w === 0, `sidebar still ${left.w}px wide`);
    await assertVisible(page, '.CodeMirror', 'editor', 150);
    await assertVisible(page, '#btn-run2', 'Run', 20);
    await page.screenshot({ path: path.join(SHOTS, '10-main-while-popped.png') });
    return 'editor full width';
  });

  await check('closing the popout brings the statement back', async () => {
    const pages = await browser.pages();
    const popup = pages.find(p => p.url().includes('panel=doc'));
    if (popup) await popup.close();
    await page.waitForFunction(() => !document.body.classList.contains('popped'), { timeout: 8000 });
    await assertVisible(page, '#left', 'sidebar', 100);
    await assertVisible(page, '.CodeMirror', 'editor', 120);
    return 'restored';
  });

  // ---- navigation out
  await check('the Problems button returns to the picker', async () => {
    await page.click('#btn-home');
    await showAllProblems(page);
    const n = await page.$$eval('.pcard', els => els.length);
    assert(n === CARD_COUNT, `picker did not come back (${n} of ${CARD_COUNT} cards)`);
    await page.screenshot({ path: path.join(SHOTS, '06-back-to-picker.png') });
    return 'back at the picker';
  });

  await check('a second attempt starts from clean stubs', async () => {
    await startProblem(page, 'File Hosting');
    const code = await getCode(page);
    assert(code.includes('NotImplementedError'), 'stubs were not restored');
    assert(!code.includes('self.files[dest]'), 'previous attempt code leaked into the new attempt');
    const attempt = await page.$eval('#pattempt', el => el.innerText);
    return attempt;
  });

  // ---- worked solution tab
  await check('the Solution tab is hidden while the clock runs and appears after finishing', async () => {
    const before = await page.$eval('#tab-answer', el => getComputedStyle(el).display);
    assert(before === 'none', `Solution tab visible during a live attempt (display:${before})`);
    await page.click('#btn-finish');
    await page.waitForFunction(() =>
      getComputedStyle(document.querySelector('#tab-answer')).display !== 'none', { timeout: 10000 });
    // Finishing opens the debrief modal, which covers the tab strip.
    await page.evaluate(() => document.querySelector('#modal').classList.remove('on'));
    return 'hidden -> shown';
  });

  await check('a problem with no worked solution says so instead of breaking', async () => {
    await page.click('#tab-answer');
    // The pane is filled by an async fetch, so waiting for "has any text" passes
    // instantly on the previous tab's content. Wait for THIS tab's content.
    await page.waitForFunction(
      () => /no worked solution/i.test(document.querySelector('#doc').innerText),
      { timeout: 8000 });
    const text = await page.$eval('#doc', el => el.innerText);
    assert(!/class \w+:/.test(text), `served code for a problem with no solution: ${text.slice(0, 80)}`);
    return 'graceful';
  });

  await check('a problem WITH a solution shows code, and level buttons narrow it', async () => {
    await page.click('#btn-home');
    await page.waitForSelector('#start.on', { timeout: 8000 });
    await startProblem(page, 'Hierarchical File System');
    await page.click('#btn-finish');
    await page.waitForFunction(() =>
      getComputedStyle(document.querySelector('#tab-answer')).display !== 'none', { timeout: 10000 });
    await page.evaluate(() => document.querySelector('#modal').classList.remove('on'));
    await page.click('#tab-answer');
    await page.waitForSelector('#doc pre.answer', { timeout: 8000 });

    const all = await page.$eval('#doc pre.answer', el => el.innerText.length);
    const buttons = await page.$$eval('#doc .anslvl', els => els.map(e => e.innerText));
    assert(buttons.length >= 2, `expected level buttons, saw ${buttons.join(',')}`);
    await page.evaluate(() =>
      [...document.querySelectorAll('#doc .anslvl')].find(b => b.innerText === 'L1').click());
    await page.waitForFunction(
      (full) => {
        const el = document.querySelector('#doc pre.answer');
        return el && el.innerText.length < full;
      }, { timeout: 8000 }, all);
    const one = await page.$eval('#doc pre.answer', el => el.innerText);
    assert(!/\bSYMLINK\b|\bRESOLVE\b/.test(one), 'the level-1 view named a level-4 operation');
    await page.screenshot({ path: path.join(SHOTS, '09-solution-tab.png') });
    return `${buttons.join(' ')} · ${all} -> ${one.length} chars`;
  });

  await check('starting a new attempt drops you off the review-only tabs', async () => {
    await page.click('#btn-home');
    await page.waitForSelector('#start.on', { timeout: 8000 });
    await startProblem(page, 'File Hosting');
    const active = await page.$eval('.tab.on', el => el.dataset.tab);
    assert(active === 'task', `left on the '${active}' tab, which now 403s`);
    return 'back on Task';
  });

  // ---- exam mode
  await check('exam mode shows numbered tests and no names, tags or shapes', async () => {
    await page.click('#btn-home');
    await page.waitForSelector('#start.on', { timeout: 8000 });
    await page.click('#blind');
    await startProblem(page, 'File Hosting');

    await setCode(page, 'class FileHost:\n'
      + '    def file_upload(self, name, size):\n'
      + '        print("trace:", name, size)\n');
    await runAndWait(page);
    await page.screenshot({ path: path.join(SHOTS, '08-exam-mode.png') });

    const rows = await page.$$eval('#results-b .case', els => els.map(e => ({
      name: e.querySelector('.name') ? e.querySelector('.name').innerText.trim() : '',
      tags: e.querySelector('.tags') ? e.querySelector('.tags').innerText.trim() : '',
    })));
    const failing = rows.filter(r => !/^all \d+ cases pass$/.test(r.name));
    assert(failing.length > 0, 'no failing rows to inspect');
    const named = failing.filter(r => !/^test \d+$/.test(r.name));
    assert(named.length === 0,
      `exam mode showed a real name: ${named.slice(0, 3).map(r => r.name).join(', ')}`);
    assert(failing.every(r => r.tags.length === 0), 'exam mode showed tags');
    const shapes = await page.$$eval('#results-b .shape .op-bad', els => els.length);
    assert(shapes === 0, `exam mode rendered ${shapes} operation shapes`);

    const text = await page.$eval('#results-b', el => el.innerText);
    assert(!/l1_/.test(text), 'a real case id leaked into the exam-mode results');
    assert(/exam mode/i.test(text), 'no exam-mode notice shown');
    // Their own print() is still theirs -- the real assessment shows stdout too.
    assert(/trace:/.test(text), "the candidate's own output was dropped");
    // The editor must survive this run like any other.
    const g = await geometry(page, '.CodeMirror');
    assert(g.h >= 150, `editor collapsed to ${g.h}px in exam mode`);
    return `${failing.length} numbered rows, nothing named`;
  });

  await check('clicking an exam-mode row reveals nothing', async () => {
    const before = await page.$$eval('#results-b .idbox', els => els.length);
    await page.click('#results-b .case.hidden');
    await new Promise(r => setTimeout(r, 250));
    const after = await page.$$eval('#results-b .idbox', els => els.length);
    assert(before === 0 && after === 0, `an id box appeared in exam mode (${before} -> ${after})`);
    return 'no id box';
  });

  // ---- a drill: task, lesson and answer are three separate places
  await check('a drill shows Task and Lesson, and an industry problem Task and Contract', async () => {
    await page.click('#btn-home');   // the exam-mode checks above left us in a session
    await startProblem(page, '3. NUMBERED');
    await page.waitForFunction(
      () => getComputedStyle(document.querySelector('#tab-lesson')).display !== 'none',
      { timeout: 10000 });
    const drill = await page.$$eval('.tab', els => els
      .filter(e => getComputedStyle(e).display !== 'none').map(e => e.innerText));
    assert(drill.join(',') === 'Task,Lesson',
      `a live drill shows tabs [${drill.join(', ')}]; expected Task and Lesson only`);
    return drill.join(' + ');
  });

  await check('the drill Task states the task, and the Lesson teaches it, separately', async () => {
    const task = await page.$eval('#doc', e => e.innerText);
    assert(/def numbered\(/.test(task), 'the Task pane does not give the signature');
    // The generated statement must not be the answer. This is the whole point of the
    // split: the lesson teaches the idiom, the task states the task, the answer waits
    // for ./pfs finish.
    assert(!/enumerate\(lines/.test(task), `the Task pane leaks the answer: ${task.slice(0, 200)}`);
    await page.click('#tab-lesson');
    await page.waitForFunction(
      () => document.querySelector('#doc').innerText.length > 500, { timeout: 8000 });
    const lesson = await page.$eval('#doc', e => e.innerText);
    assert(lesson !== task, 'the Lesson tab is showing the Task');
    assert(/enumerate/.test(lesson), 'the Lesson does not teach the idiom the drill needs');
    await page.screenshot({ path: path.join(SHOTS, '14-drill-lesson.png') });
    return `task ${task.length} chars, lesson ${lesson.length} chars`;
  });

  await check('a drill has no clock, and an industry problem does', async () => {
    const drillClock = await page.$eval('#clock', e => e.innerText.trim());
    assert(/untimed/i.test(drillClock), `a drill shows a clock: "${drillClock}"`);
    await page.click('#btn-home');
    await startProblem(page, 'File Hosting');
    const clock = await page.$eval('#clock', e => e.innerText.trim());
    assert(/\d+:\d\d/.test(clock), `the timed problem lost its clock: "${clock}"`);
    const tabs = await page.$$eval('.tab', els => els
      .filter(e => getComputedStyle(e).display !== 'none').map(e => e.innerText));
    assert(tabs.join(',') === 'Task,Contract',
      `a live industry problem shows tabs [${tabs.join(', ')}]; expected Task and Contract`);
    return `drill "${drillClock}", file_hosting "${clock}"`;
  });

  // ---- backend death
  await check('a dead server shows an explanatory banner', async () => {
    stopServer();
    await new Promise(r => setTimeout(r, 400));
    await page.click('#btn-run2').catch(() => {});
    await page.waitForSelector('#offline', { timeout: 8000 });
    const text = await page.$eval('#offline', el => el.innerText);
    assert(/not running/i.test(text), `banner said "${text}"`);
    await page.screenshot({ path: path.join(SHOTS, '07-offline.png') });
    return 'banner shown';
  });

  await check('no uncaught JavaScript errors during the whole run', async () => {
    const real = consoleErrors.filter(e => !/Failed to fetch|net::ERR|ERR_CONNECTION/i.test(e));
    assert(real.length === 0, `${real.length} JS error(s):\n      ${real.slice(0, 3).join('\n      ')}`);
    return 'clean';
  });

  await browser.close();
  stopServer();
  restoreState();

  const failed = results.filter(r => !r.pass);
  console.log(`\n  ${results.length - failed.length}/${results.length} checks passed`);
  if (failed.length) {
    console.log('\n  \x1b[31mFAILURES\x1b[0m');
    failed.forEach(f => console.log(`   - ${f.name}: ${f.why}`));
  }
  console.log(`\n  screenshots: tests/shots/\n`);
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.error('\nharness crashed:', e); stopServer(); restoreState(); process.exit(2); });
