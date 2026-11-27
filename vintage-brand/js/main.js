/* ============================================================
   Vintage Juice Point — v3 motion
   GSAP core + ScrollTrigger + SplitText, vendored in /vendor/gsap.
   No CDN, no paid plugins (ScrollSmoother is commercial).
   ============================================================ */
import { gsap } from '../vendor/gsap/gsap-core.js';
import { CSSPlugin } from '../vendor/gsap/CSSPlugin.js';
import { ScrollTrigger } from '../vendor/gsap/ScrollTrigger.js';
import { init as renderContent } from './render.js';
import { load } from './content.js';
import { quote } from './quote.js';

gsap.registerPlugin(CSSPlugin, ScrollTrigger);

/* Cards and editable copy must exist before ScrollTrigger measures the rail
   or the pinned board, so this runs first, at module scope. */
const CONTENT = renderContent() || load();

const root = document.documentElement;
root.classList.add('js');
window.__vjpMotion = true;

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const E = { expo: 'expo.out', out: 'power3.out' };

/* Wrap each .ln in an inner span so a masked reveal never clips the type,
   and give the heading a real accessible name (the clones are aria-hidden). */
function prepareLines(container) {
  if (!container) return [];
  // Read the sentence from the line elements before wrapping them: joining the
  // raw textContent would run the lines together ("Threewaystotake it").
  const label = gsap.utils
    .toArray('.ln', container)
    .map((ln) => ln.textContent.replace(/\s+/g, ' ').trim())
    .filter(Boolean)
    .join(' ');

  const lines = gsap.utils.toArray('.ln', container);
  lines.forEach((ln, i) => {
    if (ln.firstElementChild && ln.children.length === 1) return; // already wrapped
    const inner = document.createElement('span');
    while (ln.firstChild) inner.appendChild(ln.firstChild);
    // A real space after every line but the last. The line boxes are block
    // level, so screen readers, search engines and copy/paste otherwise see
    // "Threewaystotake it" — the space collapses visually but survives in the
    // text content.
    if (i < lines.length - 1) inner.appendChild(document.createTextNode(' '));
    ln.appendChild(inner);
  });
  if (label && !container.hasAttribute('aria-label')) {
    container.setAttribute('aria-label', label);
  }
  return lines.map((ln) => ln.firstElementChild).filter(Boolean);
}

/* ============================================================
   01 · HERO
   ============================================================ */
function hero() {
  const lines = prepareLines(document.querySelector('.hero__title'));
  const tl = gsap.timeline({ defaults: { ease: E.expo } });

  tl.set('.hero__media img', { scale: 1.18 })
    .to('.hero__media img', { scale: 1, duration: 2.4, ease: 'power2.out' }, 0)
    .from(lines, { yPercent: 116, duration: 1.4, stagger: 0.1 }, 0.1)
    .from('.hero__top > *', { opacity: 0, y: 16, duration: 1, stagger: 0.1 }, 0.35)
    .from('.hero__lede', { opacity: 0, y: 24, duration: 1.1 }, 0.55)
    .from('.hero__foot > *', { opacity: 0, y: 18, duration: 1, stagger: 0.1 }, 0.7)
    .from('.nav > *', { opacity: 0, y: -12, duration: 0.9, stagger: 0.07 }, 0.2);

  gsap.timeline({
    scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 0.5 },
  })
    .to('.hero__mid', { yPercent: -14, opacity: 0.1, ease: 'none' }, 0)
    .to('.hero__media img', { yPercent: 10, ease: 'none' }, 0)
    .to('.hero__foot', { opacity: 0, ease: 'none' }, 0);
}

/* ============================================================
   02 · MARQUEE — one belt, reacts to scroll velocity
   ============================================================ */
function marquee() {
  const track = document.querySelector('[data-marquee]');
  if (!track) return;
  const half = track.scrollWidth / 2;
  if (!half) return;

  const state = { x: 0, speed: 1 };
  gsap.ticker.add((time, delta) => {
    state.x -= (delta / 1000) * 54 * state.speed;
    if (state.x <= -half) state.x += half;
    if (state.x > 0) state.x -= half;
    track.style.transform = `translate3d(${state.x}px,0,0)`;
  });

  ScrollTrigger.create({
    trigger: '.marquee',
    start: 'top bottom',
    end: 'bottom top',
    onUpdate: (self) => {
      const v = gsap.utils.clamp(-1, 1, self.getVelocity() / 2400);
      const target = v < -0.02 ? -Math.min(4, Math.abs(v) * 4) : 1 + Math.min(3, Math.abs(v) * 3);
      state.speed += (target - state.speed) * 0.12;
    },
  });
}

/* ============================================================
   03 · SECTION HEADLINES — masked line reveals on scroll
   ============================================================ */
function headlines() {
  gsap.utils.toArray('[data-spread]').forEach((el) => {
    if (el.closest('.hero')) return; // hero owns its own timeline
    const lines = prepareLines(el);
    if (!lines.length) return;
    gsap.from(lines, {
      yPercent: 112,
      duration: 1.25,
      stagger: 0.08,
      ease: E.expo,
      scrollTrigger: { trigger: el, start: 'top 88%', once: true },
    });
  });
}

/* ============================================================
   04 · STATEMENT — words ignite as you read
   ============================================================ */
function statement() {
  const para = document.querySelector('[data-words]');
  if (!para) return;

  const words = para.textContent.trim().split(/\s+/);
  para.textContent = '';
  words.forEach((word, i) => {
    const span = document.createElement('span');
    span.className = 'w';
    span.textContent = i < words.length - 1 ? `${word} ` : word;
    para.appendChild(span);
  });
  para.setAttribute('aria-label', words.join(' '));

  gsap.fromTo('.statement__text .w',
    { opacity: 0.16 },
    {
      opacity: 1,
      stagger: 0.4,
      ease: 'none',
      scrollTrigger: { trigger: para, start: 'top 82%', end: 'bottom 58%', scrub: 0.4 },
    });

  const fig = document.querySelector('.statement__fig img');
  if (fig) {
    gsap.fromTo(fig, { yPercent: -5 }, {
      yPercent: 5, ease: 'none',
      scrollTrigger: { trigger: '.statement__fig', start: 'top bottom', end: 'bottom top', scrub: 0.8 },
    });
  }
}

/* ============================================================
   05 · BOARD — pinned, rail slides sideways while the mega
        heading stays put; cards stagger on entry
   ============================================================ */
function board() {
  const section = document.querySelector('.board');
  const rail = document.querySelector('[data-rail]');
  if (!section || !rail) return;

  const mm = gsap.matchMedia();

  // pin only where there is room for a heading *and* a card rail; short
  // laptops get a plain collapsing column instead (see the max-height rule)
  mm.add('(min-width: 961px) and (min-height: 701px)', () => {
    const distance = () => Math.max(0, rail.scrollWidth - rail.clientWidth);

    const slide = gsap.to(rail, {
      x: () => -distance(),
      ease: 'none',
      scrollTrigger: {
        trigger: section,
        start: 'top top',
        end: () => `+=${distance() + window.innerHeight * 0.6}`,
        pin: true,
        scrub: 0.7,
        anticipatePin: 1,
        invalidateOnRefresh: true,
      },
    });

    // the slab card drifts against the rail so the field feels layered
    gsap.to('.card--slab h3', {
      xPercent: -12,
      ease: 'none',
      scrollTrigger: { trigger: section, start: 'top top', end: () => `+=${distance()}`, scrub: 1 },
    });

    return () => { slide.scrollTrigger && slide.scrollTrigger.kill(); };
  });

  gsap.fromTo('.card',
    { y: 34, opacity: 0 },
    {
      y: 0, opacity: 1, duration: 0.85, stagger: 0.07, ease: E.out,
      scrollTrigger: { trigger: '.board', start: 'top 88%', once: true },
    });
}

/* ============================================================
   05b · THE PULSE — numbers count up once, when the field arrives
   ============================================================ */
function pulse() {
  const section = document.querySelector('.pulse');
  if (!section) return;
  const numbers = gsap.utils.toArray('.pulse [data-count]');
  if (!numbers.length) return;

  numbers.forEach((el) => {
    const target = Number(el.dataset.count) || 0;
    const suffix = el.dataset.suffix || '';
    if (reduced) {
      el.textContent = target.toLocaleString('en-US') + suffix;
      return;
    }
    const state = { n: 0 };
    el.textContent = '0' + suffix;
    gsap.to(state, {
      n: target,
      duration: 1.5,
      ease: 'power2.out',
      scrollTrigger: { trigger: section, start: 'top 76%', once: true },
      onUpdate() {
        el.textContent = Math.round(state.n).toLocaleString('en-US') + suffix;
      },
      onComplete() {
        el.textContent = target.toLocaleString('en-US') + suffix;
      },
      // a background tab throttles rAF; never leave a truncated number behind
      onInterrupt() {
        el.textContent = target.toLocaleString('en-US') + suffix;
      },
    });
  });

  // the lede rides up with the field, so the cut does not feel static
  if (!reduced) {
    gsap.from('.pulse__h, .pulse__note', {
      y: 30, opacity: 0, duration: 1.1, stagger: 0.12, ease: E.out,
      scrollTrigger: { trigger: section, start: 'top 72%', once: true },
    });
    gsap.from('.pulse__stat', {
      y: 26, opacity: 0, duration: 0.9, stagger: 0.08, ease: E.expo,
      scrollTrigger: { trigger: '.pulse__stats', start: 'top 86%', once: true },
    });
  }
}

/* ============================================================
   06 · FLAVOUR SWITCHER — colour field, word, note and price swap
   ============================================================ */
const FLAVOURS = CONTENT.flavours; // editable in /admin.html

function flavour() {
  const stage = document.querySelector('[data-flavour]');
  if (!stage) return;

  const word = stage.querySelector('[data-flavour-word]');
  const eng = stage.querySelector('[data-flavour-eng]');
  const note = stage.querySelector('[data-flavour-note]');
  const price = stage.querySelector('[data-flavour-price]');
  const img = stage.querySelector('[data-flavour-img]');
  const dots = gsap.utils.toArray('[data-flavour-list] button');

  let current = 0;
  let busy = false;

  // "Rozela" and "Vintage Angel" cannot share one font-size; measure and fit.
  function fitWord() {
    word.style.fontSize = '';
    const avail = stage.clientWidth - parseFloat(getComputedStyle(stage).paddingLeft) * 2;
    const natural = word.scrollWidth;
    if (!avail || !natural) return;
    if (natural > avail) {
      const base = parseFloat(getComputedStyle(word).fontSize);
      word.style.fontSize = `${Math.floor(base * (avail / natural) * 0.98)}px`;
    }
  }
  window.addEventListener('resize', fitWord);

  if (reduced) return; // leave the default flavour readable, no swapping

  const paint = (i, first) => {
    const f = FLAVOURS[i];
    if (!f) return;
    stage.style.background = f.field;
    stage.style.color = f.ink === 'ivory' ? '#F7F1E3' : '#0D1512';
    word.textContent = f.name;
    fitWord();
    eng.textContent = f.eng;
    note.textContent = f.note;
    price.textContent = f.price;
    dots.forEach((b, bi) => b.classList.toggle('is-live', bi === i));
    if (first) return;
    gsap.fromTo([word, eng, note], { yPercent: 26, opacity: 0 }, {
      yPercent: 0, opacity: 1, duration: 0.85, stagger: 0.05, ease: E.expo, overwrite: true,
    });
    if (img) {
      gsap.fromTo(img, { scale: 1.12, opacity: 0.5 }, {
        scale: 1, opacity: 0.85, duration: 1.1, ease: E.expo, overwrite: true,
      });
    }
  };

  paint(0, true);

  const go = (i) => {
    if (busy || i === current || !FLAVOURS[i]) return;
    busy = true;
    current = i;
    // collapse the old word upward, paint, bring the new one in
    gsap.to([word, eng, note], {
      yPercent: -22, opacity: 0, duration: 0.34, stagger: 0.03, ease: 'power2.in',
      onComplete: () => { paint(i, false); busy = false; },
    });
  };

  dots.forEach((btn, i) => btn.addEventListener('click', () => go(i)));

  // pointer position nudges the word — the field feels alive under the cursor
  const xTo = gsap.quickTo(word, 'x', { duration: 1.1, ease: 'power3' });
  const yTo = gsap.quickTo(word, 'y', { duration: 1.1, ease: 'power3' });
  stage.addEventListener('pointermove', (e) => {
    const r = stage.getBoundingClientRect();
    xTo(((e.clientX - r.left) / r.width - 0.5) * 34);
    yTo(((e.clientY - r.top) / r.height - 0.5) * 22);
  });
  stage.addEventListener('pointerleave', () => { xTo(0); yTo(0); });
}

/* ============================================================
   07 · RANGE — horizontal photos, desktop only
   ============================================================ */
function range() {
  const section = document.querySelector('.range');
  const track = document.querySelector('[data-range-track]');
  if (!section || !track) return;

  const mm = gsap.matchMedia();
  mm.add('(min-width: 961px)', () => {
    const distance = () => Math.max(0, track.scrollWidth - window.innerWidth);

    const tween = gsap.to(track, {
      x: () => -distance(),
      ease: 'none',
      scrollTrigger: {
        trigger: section,
        start: 'top top',
        end: () => `+=${distance() + window.innerHeight * 0.4}`,
        pin: true,
        scrub: 0.8,
        anticipatePin: 1,
        invalidateOnRefresh: true,
      },
    });

    gsap.utils.toArray('.panel--shot img').forEach((img) => {
      gsap.fromTo(img, { scale: 1.16, xPercent: 4 }, {
        scale: 1, xPercent: 0, ease: 'none',
        scrollTrigger: { trigger: img, containerAnimation: tween, start: 'left right', end: 'right left', scrub: 0.8 },
      });
    });
  });
}

/* ============================================================
   08 · CHROME
   ============================================================ */
function chrome() {
  const bar = document.querySelector('.scroll-progress i');
  if (bar) {
    gsap.to(bar, {
      scaleX: 1, ease: 'none',
      scrollTrigger: { trigger: document.documentElement, start: 'top top', end: 'bottom bottom', scrub: 0.3 },
    });
  }

  const nav = document.getElementById('nav');
  let last = 0;
  if (!nav) return;
  ScrollTrigger.create({
    start: 0,
    end: 'max',
    onUpdate: (self) => {
      const y = self.scroll();
      nav.style.transform = y > last && y > 280 ? 'translateY(-110%)' : 'translateY(0)';
      nav.classList.toggle('is-solid', y > window.innerHeight * 0.55);
      last = y;
    },
  });
}

/* ============================================================ */
function boot() {
  gsap.config({ nullTargetWarn: false });
  if (reduced) {
    root.classList.add('reduced');
    document.querySelectorAll('[data-reveal],.card,.w').forEach((el) => {
      el.style.opacity = 1; el.style.transform = 'none';
    });
    document.querySelectorAll('.ln').forEach((ln) => {
      const inner = ln.firstElementChild;
      if (inner) inner.style.transform = 'none';
    });
    return;
  }
  hero();
  marquee();
  quote(CONTENT); // compose the field first: headlines() reveals its rows
  headlines();
  statement();
  board();
  flavour();
  range();
  pulse();
  chrome();

  window.addEventListener('load', () => ScrollTrigger.refresh());
  let raf;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => ScrollTrigger.refresh());
  });
}

const start = () => boot();
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start, { once: true });
} else {
  start();
}
