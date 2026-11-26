/* ============================================================
   Vintage Juice Point — v2 motion
   GSAP 3.15 core + ScrollTrigger + SplitText + Observer
   (vendored locally, no CDN at runtime)
   ============================================================ */
import { gsap } from '../vendor/gsap/gsap-core.js';
import { CSSPlugin } from '../vendor/gsap/CSSPlugin.js';
import { ScrollTrigger } from '../vendor/gsap/ScrollTrigger.js';
import { SplitText } from '../vendor/gsap/SplitText.js';

gsap.registerPlugin(CSSPlugin, ScrollTrigger, SplitText);

const root = document.documentElement;
root.classList.add('js');
window.__vjpMotion = true;

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const isTouch = window.matchMedia('(hover: none)').matches;

/* ---------- shared easings ---------- */
const E = {
  out: 'power3.out',
  inOut: 'power2.inOut',
  expo: 'expo.out',
};

let splits = [];
const trackSplit = (s) => {
  splits.push(s);
  return s;
};

/* ============================================================
   1. HERO — masked line reveal, slow push-in, scroll-out
   ============================================================ */
function hero() {
  // .line wraps .ln in the markup so overflow-hidden masking never clips the type
  const tl = gsap.timeline({ defaults: { ease: E.expo } });

  tl.set('.hero__media img', { scale: 1.16 })
    .to('.hero__media img', { scale: 1, duration: 2.6, ease: 'power2.out' }, 0)
    .from('.hero__title .ln', { yPercent: 118, duration: 1.35, stagger: 0.09 }, 0.15)
    .from('.hero__eyebrow', { opacity: 0, y: 18, duration: 1, clearProps: 'opacity' }, 0.45)
    .from('.hero__sub', { opacity: 0, y: 20, duration: 1.1 }, 0.65)
    .from('.hero__foot > *', { opacity: 0, y: 22, duration: 1, stagger: 0.12 }, 0.8)
    .from('.nav > *', { opacity: 0, y: -14, duration: 0.9, stagger: 0.08, clearProps: 'opacity' }, 0.2);

  // scroll: hero content lifts, photo parallax, frame fades
  gsap.timeline({
    scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 0.6 },
  })
    .to('.hero__inner', { yPercent: -18, opacity: 0.15, ease: 'none' }, 0)
    .to('.hero__media img', { yPercent: 9, ease: 'none' }, 0)
    .to('.hero__foot', { opacity: 0, ease: 'none' }, 0);
}

/* ============================================================
   2. MARQUEE — infinite drift, speed/direction reacts to scroll
   ============================================================ */
function marquee() {
  const track = document.querySelector('[data-marquee]');
  if (!track) return;

  // the markup holds exactly two copies of the run; one copy is one loop length
  const half = track.scrollWidth / 2;
  if (!half) return;

  let speed = 1;
  const state = { x: 0 };

  gsap.ticker.add((time, deltaTime) => {
    state.x -= (deltaTime / 1000) * 42 * speed;
    if (state.x <= -half) state.x += half;
    if (state.x > 0) state.x -= half;
    track.style.transform = `translate3d(${state.x}px,0,0)`;
  });

  ScrollTrigger.create({
    trigger: '.strip',
    start: 'top bottom',
    end: 'bottom top',
    onUpdate: (self) => {
      // scroll velocity pushes the belt faster, and flips it when you scroll back
      const v = gsap.utils.clamp(-1, 1, self.getVelocity() / 2600);
      const target = v < -0.02 ? -Math.min(4, Math.abs(v) * 4) : 1 + Math.min(3, Math.abs(v) * 3);
      speed += (target - speed) * 0.12;
    },
  });
}

/* ============================================================
   3. MANIFESTO — word-by-word light-up + parallax photo
   ============================================================ */
function manifesto() {
  const para = document.querySelector('.manifesto__text');
  if (para) {
    // word-level scrub: the sentence lights up as you read past it
    // build nodes instead of an innerHTML string: joining spans without
    // whitespace collapses the sentence, so keep a real text node between them
    const words = para.textContent.trim().split(/\s+/);
    para.textContent = '';
    words.forEach((word, i) => {
      const span = document.createElement('span');
      span.className = 'w';
      span.textContent = word;
      para.appendChild(span);
      if (i < words.length - 1) para.appendChild(document.createTextNode(' '));
    });

    gsap.fromTo(
      '.manifesto__text .w',
      { opacity: 0.12 },
      {
        opacity: 1,
        stagger: 0.4,
        ease: 'none',
        scrollTrigger: {
          trigger: para,
          start: 'top 80%',
          end: 'bottom 62%',
          scrub: 0.45,
        },
      }
    );
  }

  gsap.utils.toArray('[data-reveal]').forEach((el) => {
    if (el.closest('.hero') || el.closest('.visit')) return;
    gsap.fromTo(
      el,
      { y: 26, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 1.1,
        ease: E.out,
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      }
    );
  });

  gsap.utils.toArray('[data-parallax]').forEach((el) => {
    const img = el.querySelector('img') || el;
    const depth = parseFloat(el.dataset.parallax) || 12;
    // images are oversized by ~18–28% of their own height, so stay inside that
    const travel = Math.min(depth, 9);
    gsap.fromTo(
      img,
      { yPercent: -travel },
      {
        yPercent: travel,
        ease: 'none',
        scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: 0.8 },
      }
    );
  });
}

/* ============================================================
   4. BOARD — pinned section, disc rotates in, rows stagger
   ============================================================ */
function board() {
  const head = document.querySelector('.board__head .display');
  if (head) {
    const split = trackSplit(SplitText.create(head, { type: 'lines', mask: 'lines', linesClass: 'sl' }));
    gsap.from(split.lines, {
      yPercent: 110,
      duration: 1.2,
      stagger: 0.08,
      ease: E.expo,
      scrollTrigger: { trigger: '.board__head', start: 'top 82%', once: true },
    });
  }

  const rows = gsap.utils.toArray('.row');
  gsap.fromTo(
    rows,
    { y: 26, opacity: 0 },
    {
      y: 0,
      opacity: 1,
      duration: 0.85,
      stagger: 0.075,
      ease: E.out,
      scrollTrigger: { trigger: '.rows', start: 'top 82%', once: true },
    }
  );

  const disc = document.querySelector('.board__disc img');
  if (disc) {
    gsap.fromTo(
      disc,
      { scale: 1.25, rotate: -8 },
      {
        scale: 1,
        rotate: 0,
        ease: 'none',
        scrollTrigger: { trigger: '.board', start: 'top bottom', end: 'top 25%', scrub: 0.7 },
      }
    );
    gsap.to(disc, {
      scale: 1.09,
      ease: 'none',
      scrollTrigger: { trigger: '.board', start: 'top 20%', end: 'bottom top', scrub: 1 },
    });
  }

  // row hover: the row nudges toward the price column
  rows.forEach((row) => {
    const nudge = gsap.quickTo(row, 'x', { duration: 0.55, ease: 'power3' });
    row.addEventListener('pointerenter', () => nudge(10));
    row.addEventListener('pointerleave', () => nudge(0));
  });
}

/* ============================================================
   5. RANGE — horizontal pin-driven scroll (desktop only)
   ============================================================ */
function range() {
  const section = document.querySelector('.range');
  const track = document.querySelector('.range__track');
  if (!section || !track) return;

  ScrollTrigger.matchMedia({
    '(min-width: 961px)': () => {
      const distance = () => track.scrollWidth - window.innerWidth;

      const tween = gsap.to(track, {
        x: () => -distance(),
        ease: 'none',
        scrollTrigger: {
          trigger: section,
          start: 'top top',
          end: () => `+=${distance() + window.innerHeight * 0.4}`,
          pin: true,
          scrub: 0.9,
          anticipatePin: 1,
          invalidateOnRefresh: true,
        },
      });

      // panels ease in slightly as they enter the viewport
      gsap.utils.toArray('.panel--photo img').forEach((img) => {
        gsap.fromTo(
          img,
          { scale: 1.14, xPercent: 4 },
          {
            scale: 1,
            xPercent: 0,
            ease: 'none',
            scrollTrigger: {
              trigger: img,
              containerAnimation: tween,
              start: 'left right',
              end: 'right left',
              scrub: 0.8,
            },
          }
        );
      });

      return () => {
        ScrollTrigger.getAll().forEach((st) => st.kill());
      };
    },
  });
}

/* ============================================================
   6. STATEMENT — quote splits in, image drifts
   ============================================================ */
function statement() {
  const q = document.querySelector('.statement__quote [data-split]');
  if (!q) return;
  const split = trackSplit(SplitText.create(q, { type: 'lines', mask: 'lines', linesClass: 'sl' }));
  gsap.from(split.lines, {
    yPercent: 112,
    duration: 1.35,
    stagger: 0.1,
    ease: E.expo,
    scrollTrigger: { trigger: '.statement__quote', start: 'top 85%', once: true },
  });

  gsap.from('.statement__quote cite', {
    opacity: 0,
    y: 14,
    duration: 1,
    delay: 0.35,
    scrollTrigger: { trigger: '.statement__quote', start: 'top 78%', once: true },
  });
}

/* ============================================================
   7. VISIT + FOOTER
   ============================================================ */
function visit() {
  const h = document.querySelector('.visit .display');
  if (h) {
    const split = trackSplit(SplitText.create(h, { type: 'lines', mask: 'lines', linesClass: 'sl' }));
    gsap.from(split.lines, {
      yPercent: 110,
      duration: 1.25,
      stagger: 0.08,
      ease: E.expo,
      scrollTrigger: { trigger: h, start: 'top 86%', once: true },
    });
  }

  gsap.utils.toArray('.visit [data-reveal]').forEach((el, i) => {
    gsap.fromTo(
      el,
      { y: 22, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.9,
        delay: (i % 3) * 0.06,
        ease: E.out,
        scrollTrigger: { trigger: el, start: 'top 92%', once: true },
      }
    );
  });

  gsap.from('.foot > *', {
    opacity: 0,
    y: 24,
    duration: 1,
    stagger: 0.1,
    scrollTrigger: { trigger: '.foot', start: 'top 92%', once: true },
  });
}

/* ============================================================
   8. Chrome: scroll progress + retract nav
   ============================================================ */
function chrome() {
  const bar = document.querySelector('.scroll-progress i');
  if (bar) {
    gsap.to(bar, {
      scaleX: 1,
      ease: 'none',
      scrollTrigger: { trigger: document.documentElement, start: 'top top', end: 'bottom bottom', scrub: 0.3 },
    });
  }

  const nav = document.getElementById('nav');
  let last = 0;
  ScrollTrigger.create({
    start: 'top -120',
    end: 'max',
    onUpdate: (self) => {
      const y = self.scroll();
      if (nav) {
        nav.style.transform = y > last && y > 260 ? 'translateY(-108%)' : 'translateY(0)';
        nav.classList.toggle('is-solid', y > window.innerHeight * 0.6);
      }
      last = y;
    },
  });
}

/* ============================================================
   boot
   ============================================================ */
function boot() {
  gsap.config({ nullTargetWarn: false });
  if (reduced) {
    root.classList.add('reduced');
    document.querySelectorAll('[data-reveal]').forEach((el) => {
      el.style.opacity = 1;
      el.style.transform = 'none';
    });
    return;
  }
  hero();
  marquee();
  manifesto();
  board();
  range();
  statement();
  visit();
  chrome();

  // fonts land late → re-measure every scroll-driven layout
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => {
      splits.forEach((s) => s && s.revert && s.revert());
      splits = [];
      ScrollTrigger.refresh();
    });
  }
  window.addEventListener('load', () => ScrollTrigger.refresh());
  let rAF;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(rAF);
    rAF = requestAnimationFrame(() => ScrollTrigger.refresh());
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
