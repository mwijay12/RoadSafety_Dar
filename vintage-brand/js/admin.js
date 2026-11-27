/* ============================================================
   Vintage Juice Point — content desk
   Edits the whole site from one form. Writes localStorage (same key the
   site reads) and reloads the preview iframe so what you see is the real
   page, not an approximation.

   Publish exports js/content-data.js, which sets window.__VJP_CONTENT__
   before the site boots — that is the path to shipping content for
   everyone. There is no server here, so publishing is a file, not a POST.
   ============================================================ */

import { DEFAULTS, KEY, clear, load, normalise, save } from './content.js';

const $ = (sel) => document.querySelector(sel);
const clone = (v) => JSON.parse(JSON.stringify(v));

let data = clone(load());
let pristine = clone(data); // last saved state, for undo
let history = [];
let saveTimer = 0;

const stateEl = $('#state');
const frame = $('#preview');

/* ---------- chrome state ------------------------------------------------ */
function setState(text, dirty) {
  stateEl.innerHTML = text;
  stateEl.classList.toggle('is-dirty', !!dirty);
}

function markDirty() {
  setState('<b>Editing</b> · not saved yet', true);
}

function refreshFrame(immediate) {
  // the iframe boots from localStorage, so a reload is the honest preview
  clearTimeout(refreshFrame.t);
  refreshFrame.t = setTimeout(() => {
    try { frame.contentWindow.location.reload(); } catch { frame.src = `index.html?t=${Date.now()}`; }
  }, immediate ? 0 : 320);
}

/* ---------- persistence ------------------------------------------------- */
function commit({ undoable = true } = {}) {
  if (undoable) history.push(clone(pristine));
  if (history.length > 40) history.shift();
  data = normalise(data);
  const ok = save(data);
  pristine = clone(data);
  if (ok) setState('<b>Saved</b> · this device');
  else setState('Could not save — storage is full or blocked', true);
  refreshFrame();
}

function queueSave() {
  markDirty();
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => commit(), 420);
}

/* ---------- bind a plain input ----------------------------------------- */
function bindField(el) {
  const path = el.dataset.path.split('.');
  const get = () => path.reduce((acc, k) => (acc ? acc[k] : undefined), data);
  const set = (v) => {
    const last = path.pop();
    const owner = path.reduce((acc, k) => acc[k], data);
    owner[last] = v;
  };
  el.value = get() ?? '';
  el.addEventListener('input', () => {
    set(el.value);
    queueSave();
  });
}

/* ---------- repeating rows --------------------------------------------- */
function rowShell(title) {
  const row = document.createElement('div');
  row.className = 'adm__row';
  const head = document.createElement('div');
  head.className = 'adm__rowhd';
  const strong = document.createElement('strong');
  strong.textContent = title;
  const btns = document.createElement('div');
  btns.className = 'adm__rowbtns';
  head.append(strong, btns);
  row.append(head);
  return { row, strong, btns };
}

function iconButton(label, glyph, cls, onClick, disabled) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = `adm__icon${cls ? ` ${cls}` : ''}`;
  b.textContent = glyph;
  b.title = label;
  b.setAttribute('aria-label', label);
  b.disabled = !!disabled;
  b.addEventListener('click', onClick);
  return b;
}

function field(label, value, onInput, opts = {}) {
  const wrap = document.createElement('div');
  wrap.className = `adm__field${opts.wide ? ' adm__field--wide' : ''}`;
  const id = `f${Math.random().toString(36).slice(2, 8)}`;
  const lb = document.createElement('label');
  lb.textContent = label;
  lb.htmlFor = id;
  const input = opts.textarea ? document.createElement('textarea') : document.createElement('input');
  input.id = id;
  if (opts.type) input.type = opts.type;
  input.value = value ?? '';
  input.addEventListener('input', () => onInput(input.value));
  wrap.append(lb, input);
  if (opts.hint) {
    const h = document.createElement('p');
    h.className = 'hint';
    h.textContent = opts.hint;
    wrap.append(h);
  }
  return wrap;
}

/* ---------- board cards ------------------------------------------------- */
function renderCards() {
  const host = $('#cards');
  host.textContent = '';
  $('#cards-hint').textContent =
    `${data.cards.length} of 7 shown. The pinned rail fits about seven before it has to scroll a long way.`;
  data.cards.forEach((card, i) => {
    const { row, strong, btns } = rowShell(card.name || `Card ${i + 1}`);
    btns.append(
      iconButton('Move up', '↑', '', () => move(data.cards, i, -1), i === 0),
      iconButton('Move down', '↓', '', () => move(data.cards, i, 1), i === data.cards.length - 1),
      iconButton('Remove card', '×', 'adm__icon--kill', () => {
        data.cards.splice(i, 1);
        commit();
        renderCards();
      }, data.cards.length <= 1),
    );

    const grid = document.createElement('div');
    grid.className = 'adm__grid';
    grid.append(
      field('Name', card.name, (v) => { card.name = v; strong.textContent = v || `Card ${i + 1}`; queueSave(); }),
      field('Subtitle', card.sub, (v) => { card.sub = v; queueSave(); }),
      field('Price (TZS)', card.price, (v) => { card.price = v; queueSave(); }),
      field('Copy', card.copy, (v) => { card.copy = v; queueSave(); }, { wide: true, textarea: true }),
    );
    row.append(grid);
    host.append(row);
  });
}

function move(list, index, delta) {
  const next = index + delta;
  if (next < 0 || next >= list.length) return;
  const [item] = list.splice(index, 1);
  list.splice(next, 0, item);
  commit();
  renderCards();
}

/* ---------- flavours --------------------------------------------------- */
const HEX = /^#[0-9a-f]{6}$/i;

function renderFlavours() {
  const host = $('#flavours');
  host.textContent = '';
  data.flavours.forEach((fl, i) => {
    const { row, strong, btns } = rowShell(fl.name || `Flavour ${i + 1}`);
    btns.append(
      iconButton('Move up', '↑', '', () => {
        const next = i - 1;
        if (next < 0) return;
        [data.flavours[i - 1], data.flavours[i]] = [data.flavours[i], data.flavours[i - 1]];
        commit(); renderFlavours();
      }, i === 0),
      iconButton('Move down', '↓', '', () => {
        const next = i + 1;
        if (next >= data.flavours.length) return;
        [data.flavours[i + 1], data.flavours[i]] = [data.flavours[i], data.flavours[i + 1]];
        commit(); renderFlavours();
      }, i === data.flavours.length - 1),
      iconButton('Remove flavour', '×', 'adm__icon--kill', () => {
        data.flavours.splice(i, 1);
        commit(); renderFlavours();
      }, data.flavours.length <= 1),
    );

    const grid = document.createElement('div');
    grid.className = 'adm__grid';

    const inkSelect = document.createElement('select');
    ['ink', 'ivory'].forEach((v) => {
      const o = document.createElement('option');
      o.value = v;
      o.textContent = v === 'ink' ? 'Ink text' : 'Ivory text';
      inkSelect.append(o);
    });
    inkSelect.value = fl.ink;
    inkSelect.addEventListener('change', () => { fl.ink = inkSelect.value; queueSave(); });
    const inkWrap = document.createElement('div');
    inkWrap.className = 'adm__field';
    const inkLabel = document.createElement('label');
    inkLabel.textContent = 'Text on colour';
    inkWrap.append(inkLabel, inkSelect);

    const colour = field('Field colour', fl.field, (v) => {
      if (HEX.test(v)) {
        fl.field = v;
        // keep text legible automatically: light fields take ink
        const [r, g, b] = [1, 3, 5].map((k) => parseInt(v.slice(k, k + 2), 16) / 255);
        const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        if (lum > 0.55) { fl.ink = 'ink'; inkSelect.value = 'ink'; }
        queueSave();
      }
    }, { type: 'color', hint: 'Pick a light field and text switches to ink by itself.' });

    grid.append(
      field('Name', fl.name, (v) => { fl.name = v; strong.textContent = v; queueSave(); }),
      field('English', fl.eng, (v) => { fl.eng = v; queueSave(); }),
      field('Price (TZS)', fl.price, (v) => { fl.price = v; queueSave(); }),
      colour,
      inkWrap,
      field('Note', fl.note, (v) => { fl.note = v; queueSave(); }, { wide: true, textarea: true }),
    );
    row.append(grid);
    host.append(row);
  });
}

/* ---------- full menu (menu.html) --------------------------------------- */
function renderMenu() {
  const host = $('#menu');
  host.textContent = '';
  data.menu.forEach((cat, ci) => {
    const row = document.createElement('div');
    row.className = 'adm__row';
    row.style.gridColumn = '1/-1';

    const head = document.createElement('div');
    head.className = 'adm__rowhd';
    const strong = document.createElement('strong');
    strong.textContent = `${cat.title} · ${cat.items.length}`;
    head.append(strong);
    row.append(head);

    const grid = document.createElement('div');
    grid.className = 'adm__grid';
    grid.append(
      field('Category', cat.title, (v) => {
        cat.title = v;
        strong.textContent = `${v} · ${cat.items.length}`;
        queueSave();
      }),
      field('Ingredient line', cat.subtitle, (v) => { cat.subtitle = v; queueSave(); },
        { hint: 'Shown under every item in this category.' }),
    );

    cat.items.forEach((item, ii) => {
      const line = document.createElement('div');
      line.className = 'adm__field adm__field--wide';
      line.style.display = 'grid';
      line.style.gridTemplateColumns = '1.1fr 1.1fr 90px 32px';
      line.style.gap = '8px';
      line.style.alignItems = 'end';

      const name = document.createElement('input');
      name.value = item.name;
      name.setAttribute('aria-label', `Item ${ii + 1} name`);
      name.addEventListener('input', () => { item.name = name.value; queueSave(); });

      const eng = document.createElement('input');
      eng.value = item.english || '';
      eng.setAttribute('aria-label', `Item ${ii + 1} English`);
      eng.placeholder = 'English (optional)';
      eng.addEventListener('input', () => { item.english = eng.value; queueSave(); });

      const price = document.createElement('input');
      price.value = item.price;
      price.setAttribute('aria-label', `Item ${ii + 1} price`);
      price.inputMode = 'numeric';
      price.addEventListener('input', () => { item.price = price.value; queueSave(); });

      const kill = iconButton('Remove item', '×', 'adm__icon--kill', () => {
        cat.items.splice(ii, 1);
        commit(); renderMenu();
      }, cat.items.length <= 1);

      line.append(name, eng, price, kill);
      grid.append(line);
    });

    const add = document.createElement('button');
    add.type = 'button';
    add.className = 'adm__btn';
    add.textContent = '+ Add item';
    add.addEventListener('click', () => {
      cat.items.push({ name: 'New blend', english: '', price: '1,000' });
      commit(); renderMenu();
    });
    grid.append(add);
    row.append(grid);
    host.append(row);
  });
}

/* ---------- add / remove ------------------------------------------------ */
$('#add-card').addEventListener('click', () => {
  if (data.cards.length >= 7) {
    setState('The rail holds seven cards comfortably — remove one first', true);
    return;
  }
  const n = String(data.cards.length + 1).padStart(2, '0');
  data.cards.push({ n, name: 'New blend', sub: 'House', copy: '', price: '1,000', kind: '' });
  commit(); renderCards();
});

$('#add-flavour').addEventListener('click', () => {
  data.flavours.push({
    name: 'New flavour', eng: '', field: '#C86B3F', ink: 'ink', price: '1,000', note: '',
  });
  commit(); renderFlavours();
});

/* ---------- undo / reset / publish -------------------------------------- */
$('#undo').addEventListener('click', () => {
  if (!history.length) {
    setState('Nothing to undo', true);
    return;
  }
  data = normalise(history.pop());
  save(data);
  pristine = clone(data);
  setState('<b>Undone</b> · this device');
  hydrate();
  refreshFrame(true);
});

$('#reset').addEventListener('click', () => {
  if (!window.confirm('Reset every section back to the shipped content? On-device edits are deleted.')) return;
  history.push(clone(pristine));
  clear();
  data = normalise(DEFAULTS);
  pristine = clone(data);
  setState('<b>Reset</b> · shipped content restored');
  hydrate();
  refreshFrame(true);
});

function publishText() {
  return `/* Shipped content — generated by admin.html.
   Commit this file and every visitor sees it. Regenerate rather than edit. */
window.__VJP_CONTENT__ = ${JSON.stringify(data, null, 2)};
`;
}

$('#publish').addEventListener('click', async () => {
  const text = publishText();
  let copied = false;
  try {
    await navigator.clipboard.writeText(text);
    copied = true;
  } catch { copied = false; }

  // fall back to a download when the clipboard is blocked (non-https, Safari)
  if (!copied) {
    const blob = new Blob([text], { type: 'text/javascript' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'content-data.js';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  const box = document.createElement('div');
  box.className = 'adm__row';
  box.style.marginTop = '8px';
  const h = document.createElement('strong');
  h.textContent = copied ? 'Copied js/content-data.js' : 'Downloaded content-data.js';
  const p = document.createElement('p');
  p.className = 'hint';
  p.textContent = 'Save it over vintage-brand/js/content-data.js in the repo and commit. The site loads it before js/main.js.';
  const area = document.createElement('textarea');
  area.value = text;
  area.rows = 8;
  area.className = 'adm__field';
  box.append(h, p, area);
  const side = document.querySelector('.adm__side');
  const old = document.querySelector('#publish-out');
  if (old) old.remove();
  box.id = 'publish-out';
  side.prepend(box);
  if (box.scrollIntoView) box.scrollIntoView({ block: 'start', behavior: 'smooth' });
});

/* ---------- boot -------------------------------------------------------- */
function hydrate() {
  document.querySelectorAll('[data-path]').forEach((el) => {
    const path = el.dataset.path.split('.');
    const v = path.reduce((acc, k) => (acc ? acc[k] : undefined), data);
    if (v != null) el.value = v;
  });
  renderCards();
  renderFlavours();
  renderMenu();
}

document.querySelectorAll('[data-path]').forEach(bindField);
hydrate();
setState('<b>Saved</b> · this device');

// keep two tabs from fighting over the same key
window.addEventListener('storage', (e) => {
  if (e.key !== KEY) return;
  data = clone(load());
  pristine = clone(data);
  hydrate();
  refreshFrame(true);
});
