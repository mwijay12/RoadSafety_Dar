/* ============================================================
   Vintage Juice Point — content → DOM
   Runs before main.js touches anything, so ScrollTrigger, SplitText
   and the pinned rail all measure the final layout.
   ============================================================ */

import { load } from './content.js';

const PHOTO_SRC = 'assets/img/range-labelled.jpg';
const PHOTO_ALT = 'Five bottles of cold-pressed juice with Vintage Juice Point labels against a terracotta wall';

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  return node;
}

/** Build one board card. The slab/photo/end variants are presentation only. */
function card(d) {
  if (d.kind === 'photo') {
    const a = el('article', 'card card--photo');
    const img = el('img');
    img.src = PHOTO_SRC;
    img.alt = PHOTO_ALT;
    img.loading = 'lazy';
    a.appendChild(img);
    return a;
  }
  const a = el('article', `card${d.kind === 'slab' ? ' card--slab' : ''}`);
  a.appendChild(el('span', 'card__n', d.n));
  a.appendChild(el('h3', null, d.name));
  if (d.sub) a.appendChild(el('p', 'card__sub', d.sub));
  if (d.copy) a.appendChild(el('p', 'card__copy', d.copy));
  if (d.price) a.appendChild(el('span', 'card__price', d.price));
  return a;
}

/** The brass closing card with the giant "Read the menu" link. */
function endCard() {
  const a = el('article', 'card card--end');
  a.appendChild(el('p', 'kicker', 'All 22 blends'));
  const link = el('a', 'giant-link');
  link.href = 'menu.html';
  link.setAttribute('aria-label', 'Read the full menu');
  ['Read ', 'the ', 'menu'].forEach((word) => {
    const ln = el('span', 'ln', word);
    link.appendChild(ln);
  });
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 12');
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', 'M0 6h22M17 1l5 5-5 5');
  svg.appendChild(path);
  link.appendChild(svg);
  a.appendChild(link);
  return a;
}

/** Render the pinned rail: cards from content, a photo spliced mid-way. */
export function board(content) {
  const rail = document.querySelector('[data-rail]');
  if (!rail) return;
  rail.textContent = '';
  const cards = content.cards.slice();
  const photoAt = Math.min(3, cards.length); // after the third card, as before
  cards.splice(photoAt, 0, { kind: 'photo' });
  cards.forEach((d) => rail.appendChild(card(d)));
  rail.appendChild(endCard());
}

/** One dot per flavour, coloured by its field. */
export function flavourDots(content) {
  const list = document.querySelector('[data-flavour-list]');
  if (!list) return;
  list.textContent = '';
  content.flavours.forEach((f, i) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset.go = String(i);
    b.setAttribute('aria-label', f.name);
    if (i === 0) b.className = 'is-live';
    const i2 = document.createElement('i');
    i2.style.setProperty('--dot', f.field);
    b.appendChild(i2);
    li.appendChild(b);
    list.appendChild(li);
  });
}

/** Stamp every [data-c="path.to.value"] from content. */
export function fields(content) {
  document.querySelectorAll('[data-c]').forEach((node) => {
    const path = node.dataset.c.split('.');
    let value = content;
    for (const key of path) value = value && value[key];
    if (typeof value === 'number') {
      // counters: the live number and the animation target must agree
      node.textContent = value.toLocaleString('en-US') + (node.dataset.suffix || '');
      node.dataset.count = String(value);
      return;
    }
    if (typeof value !== 'string') return;
    // Hero kicker/meta carry a decorative <i> separator inside the string
    // ("Dar es Salaam · Tanzania"): rebuild it as text + <i> + text so the
    // dot is never lost, and it always matches the saved copy.
    const italics = node.querySelector('i');
    if (italics) {
      const dot = italics.textContent || '·';
      const [head, ...rest] = value.split(dot);
      node.textContent = '';
      node.appendChild(document.createTextNode(head.trim()));
      if (rest.length) {
        const mark = document.createElement('i');
        mark.setAttribute('aria-hidden', 'true');
        mark.textContent = dot;
        node.appendChild(mark);
        node.appendChild(document.createTextNode(rest.join(dot).trim()));
      }
    } else {
      node.textContent = value;
    }
    // Unsupplied details stay visibly muted until someone types a real value.
    if (node.hasAttribute('data-placeholder')) {
      node.classList.toggle('pending', /XXX|^\s*Add opening hours\s*$/i.test(value));
    }
  });
}

/** Convenience: render everything. */
export function renderAll(content) {
  board(content);
  flavourDots(content);
  fields(content);
  year();
}

/** Footer year, so the page does not claim 2026 forever. */
export function year() {
  const el = document.querySelector('[data-year]');
  if (el) el.textContent = String(new Date().getFullYear());
}

/** Render now if the visitor is on the site, no-op on chrome-less pages. */
export function init() {
  if (!document.querySelector('[data-rail]')) return null;
  const content = load();
  renderAll(content);
  return content;
}
