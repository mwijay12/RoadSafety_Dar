/**
 * Featured Stat Card — count-up animation
 *
 * Animates any element with [data-count-up] from 0 → value on first paint.
 * No dependencies. Respects prefers-reduced-motion.
 *
 * Behavior:
 *   - Reads the integer from the data-count-up attribute
 *   - Animates the text content of the .featured-stat-card__value child
 *   - Duration scales with magnitude (max 1.6s)
 *   - Easing: ease-out cubic
 *   - On prefers-reduced-motion: jumps straight to final value
 *   - On no <picture> / hidden tab: still animates on visibility change
 */
(function () {
  "use strict";

  const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /** Linear → ease-out cubic for that satisfying deceleration */
  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  /**
   * Animate a single card.
   * @param {HTMLElement} card - element with [data-count-up] attribute
   */
  function animateCard(card) {
    const target = parseInt(card.getAttribute("data-count-up"), 10);
    if (isNaN(target)) return;

    const valueEl = card.querySelector(".featured-stat-card__value");
    if (!valueEl) return;

    // Always start at 0 on first paint (deterministic — no flash of final value)
    valueEl.textContent = "0";

    if (REDUCED_MOTION) {
      valueEl.textContent = formatNumber(target);
      return;
    }

    // Duration scales logarithmically — 1,500 for huge numbers, 800 for small
    const duration = Math.min(1600, 700 + Math.log10(Math.max(target, 10)) * 220);
    const start = performance.now();

    function tick(now) {
      const elapsed = now - start;
      const t = Math.min(1, elapsed / duration);
      const eased = easeOutCubic(t);
      const current = Math.round(target * eased);
      valueEl.textContent = formatNumber(current);
      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        // Ensure final value is exact (no rounding drift)
        valueEl.textContent = formatNumber(target);
      }
    }
    requestAnimationFrame(tick);
  }

  /** 1234 → "1,234" (locale-aware) */
  function formatNumber(n) {
    try {
      return n.toLocaleString();
    } catch (_) {
      return String(n);
    }
  }

  /**
   * Use IntersectionObserver so cards animate when they scroll into view,
   * not all at once on page load.
   */
  function init() {
    const cards = document.querySelectorAll("[data-count-up]");
    if (!cards.length) return;

    if (!("IntersectionObserver" in window)) {
      // Fallback for ancient browsers — just animate everything now
      cards.forEach(animateCard);
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCard(entry.target);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.3, rootMargin: "0px 0px -10% 0px" }
    );

    cards.forEach((card) => io.observe(card));
  }

  // Run after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
