/* ============================================================
   Vintage Juice Point — quote field
   The house line is the biggest type on the page, so it is measured,
   not guessed. Given the brass field's box, the line is split into the
   number of rows that fills it and sized to the widest row — which is
   what keeps the field from reading as centred text on empty brass.
   Edit the sentence in the admin panel and the field recomposes itself.
   ============================================================ */

import { gsap } from '../vendor/gsap/gsap-core.js';
import { ScrollTrigger } from '../vendor/gsap/ScrollTrigger.js';

const E = { out: 'power3.out' };

const MEASURE = 100; // px, ratios only

const tokens = (t) => String(t).split(/\s+/).filter(Boolean);

/** measure words + the word space, in the display face at 600. */
function measureWords(words) {
  const ctx = measureWords.ctx || (measureWords.ctx = document.createElement('canvas').getContext('2d'));
  // keep this string identical to .quote p in css/style.css, or the measured
  // fit will not match what the browser renders
  ctx.font = `600 ${MEASURE}px "Cormorant Garamond", Georgia, serif`;
  const space = ctx.measureText(' ').width / MEASURE;
  return { widths: words.map((w) => ctx.measureText(w).width / MEASURE), space };
}

/**
 * Split `count` items into exactly n contiguous groups, minimising the
 * widest group (balanced partition DP). Returns [start, end) pairs.
 */
function partition(em, n, space = 0.26) {
  const count = em.length;
  if (n > count) return null;
  const pre = [0];
  for (let i = 0; i < count; i++) pre.push(pre[i] + em[i] + space);
  const width = (i, j) => pre[j] - pre[i] - space;

  const best = Array.from({ length: n + 1 }, () => new Array(count + 1).fill(Infinity));
  const cut = Array.from({ length: n + 1 }, () => new Array(count + 1).fill(0));
  best[0][0] = 0;
  for (let l = 1; l <= n; l++) {
    for (let i = l; i <= count; i++) {
      for (let j = l - 1; j < i; j++) {
        const cost = Math.max(best[l - 1][j], width(j, i));
        if (cost < best[l][i]) { best[l][i] = cost; cut[l][i] = j; }
      }
    }
  }
  const out = [];
  let i = count;
  for (let l = n; l > 0; l--) { const j = cut[l][i]; out.unshift([j, i]); i = j; }
  return out;
}

/**
 * One masked row: .ln (block, clipped) > span (the thing that moves) with a
 * real trailing space inside the span. The line boxes are block level, so
 * without that space screen readers, search engines and copy/paste read the
 * sentence as one run-on word ("aboutwhere"). The space has to live inside
 * the span, not after it — a text node between two blocks gets trimmed.
 */
function writeRow(parent, text, trailingSpace) {
  const ln = document.createElement('span');
  ln.className = 'ln';
  const inner = document.createElement('span');
  inner.textContent = text;
  if (trailingSpace) inner.appendChild(document.createTextNode(' '));
  ln.appendChild(inner);
  parent.appendChild(ln);
}

/**
 * Compose the field. Returns { lines, size, fill } or null when the box
 * cannot be measured (hidden tab, no layout).
 */
export function fitQuote(p, text, decor = ['“', '”']) {
  const field = p.closest('.quote');
  if (!field) return null;
  const list = tokens(text);
  if (!list.length) return null;

  const cs = getComputedStyle(field);
  const usable = Math.min(
    field.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
    1520,
  );
  const room = field.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - 96;
  // Not measurable (hidden tab, jsdom, first paint): still write the copy in
  // plain rows at the CSS size, so edited text is never stale.
  if (!(usable > 0) || !(room > 0)) {
    p.textContent = '';
    p.style.fontSize = '';
    const half = Math.ceil(list.length / 2);
    writeRow(p, `${decor[0]}${list.slice(0, half).join(' ')}`, true);
    writeRow(p, `${list.slice(half).join(' ')}${decor[1]}`, false);
    p.setAttribute('aria-label', `${decor[0]}${list.join(' ')}${decor[1]}`);
    return null;
  }

  // the marks ride on the first and last word, so they count in the fit
  const marked = list.slice();
  marked[0] = decor[0] + marked[0];
  marked[marked.length - 1] = `${marked[marked.length - 1]}${decor[1]}`;
  const { widths: em, space } = measureWords(marked);
  const lineHeight = 0.9;

  let best = null;
  for (let n = Math.min(4, list.length); n >= 2; n--) {
    const groups = partition(em, n, space);
    if (!groups) continue;
    const rowEm = groups.map(([i, j]) => em.slice(i, j).reduce((a, b) => a + b, 0) + space * (j - i - 1));
    const widest = Math.max(...rowEm);
    const size = Math.min((usable * 0.98) / widest, room / (lineHeight * n));
    // how much of the field the block covers, both ways
    const fillW = (widest * size) / usable;
    const fillH = (lineHeight * n * size) / room;
    const fill = fillW * fillH;
    if (!best || fill > best.fill + 0.006) best = { n, groups, widest, size, fill };
  }
  if (!best) return null;

  p.textContent = '';
  p.style.fontSize = `${Math.round(best.size)}px`;
  best.groups.forEach(([i, j], li) => {
    const head = li === 0 ? decor[0] : '';
    const tail = li === best.groups.length - 1 ? decor[1] : '';
    writeRow(p, head + list.slice(i, j).join(' ') + tail, li < best.groups.length - 1);
  });
  if (!p.hasAttribute('aria-label')) p.setAttribute('aria-label', `${decor[0]}${list.join(' ')}${decor[1]}`);
  return { lines: best.n, size: Math.round(best.size), fill: +best.fill.toFixed(2) };
}

/** Compose the brass quote field. The masked row reveal is owned by
    headlines() in main.js, which runs after this so it animates the rows
    this function produced — not the ones the HTML shipped with. */
export function quote(content) {
  const p = document.querySelector('.quote__text');
  if (!p) return;

  const text = (content && content.quote && content.quote.text) || p.textContent;
  const refit = () => {
    // a narrower viewport wants fewer, wider rows
    const n = fitQuote(p, text);
    return n;
  };
  refit();

  // webfont metrics land after first paint, so measure again when they do
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => { refit(); ScrollTrigger.refresh(); });
  }
  // a composed px size is stale after a width change: recompose on resize
  let raf = 0;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => refit());
  });

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  gsap.from('.quote cite', {
    y: 18, opacity: 0, duration: 1, ease: E.out, delay: 0.3,
    scrollTrigger: { trigger: '.quote', start: 'top 74%', once: true },
  });
  // the type drifts against the field so it never feels pasted on
  gsap.to('.quote blockquote', {
    yPercent: -7, ease: 'none',
    scrollTrigger: { trigger: '.quote', start: 'top bottom', end: 'bottom top', scrub: 0.8 },
  });
}
