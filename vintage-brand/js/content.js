/* ============================================================
   Vintage Juice Point — content contract
   The single source of truth for everything editable: board cards,
   flavour switcher, visit details, quote, hero copy.

   Storage is localStorage, so edits stay on the device that made them.
   That is deliberate for a static site with no backend — publish exports
   JSON that can be committed to js/content-data.js for everyone.

   Nothing here may throw: a malformed blob must fall back to DEFAULTS,
   otherwise the whole site loses its motion.
   ============================================================ */

export const KEY = 'vjp:content:v1';

export const DEFAULTS = {
  hero: {
    kicker: 'Dar es Salaam · Tanzania',
    since: 'Est. the coast',
    titleA: 'Asili',
    titleB: 'safi.',
    ledeEm: 'Ladha ya kisasa.',
    lede: 'Clean origin, modern taste — pressed the same morning, poured over a brass counter.',
    meta: 'Takeaway · Card & NFC · Good for kids',
  },
  quote: {
    text: 'Cold, clean, and honest about where it came from.',
    cite: 'the house line',
  },
  numbers: {
    title: 'Everything you need to know before you walk up to the brass.',
    blends: 22,
    from: 1000,
    mornings: 6,
    seconds: 90,
    note: 'Fruit is bought that morning, so the board changes with what is ripe. Every price on this site was transcribed from the counter board.',
  },
  visit: {
    where: '58F5+24, Dar es Salaam',
    hours: 'Add opening hours',
    phone: '+255 XXX XXX XXX',
    pay: 'Card · NFC · Cash',
    goodFor: 'Takeaway · Kids',
    listing: 'Vintage Experience',
    fine: 'Concept redesign. Hours, phone and email are placeholders — no verified details were supplied by the business.',
  },
  cards: [
    { n: '01', name: 'Rozela', sub: 'Roselle', copy: 'Deep crimson, steeped not sweetened. The one people come back for.', price: '1,000', kind: 'slab' },
    { n: '02', name: 'Embe', sub: 'Mango', copy: 'Thick as custard in season, loosened with a little lime.', price: '1,000' },
    { n: '03', name: 'Nado', sub: 'House signature', copy: 'Parachichi, nanasi, embe, passion. Avocado gives it the body.', price: '2,000' },
    { n: '04', name: 'Angel', sub: 'Coast blend', copy: 'Rozela, tangawizi, ndimu, ubuyu, ukwaju. Sour, warm, cold all at once.', price: '3,000' },
    { n: '05', name: 'Nado Rich', sub: 'Meal in a glass', copy: 'Parachichi, ndizi, tende, embe, yogurt. Breakfast for people in a hurry.', price: '4,000' },
  ],
  menu: [
    {
      "id": "fresh",
      "title": "Fresh Juice",
      "subtitle": "Single-note blends, freshly made",
      "items": [
        {
          "name": "Rozela",
          "english": "Roselle",
          "price": "1,000"
        },
        {
          "name": "Ukwaju",
          "english": "Tamarind",
          "price": "1,000"
        },
        {
          "name": "Embe",
          "english": "Mango",
          "price": "1,000"
        },
        {
          "name": "Nanasi",
          "english": "Pineapple",
          "price": "1,000"
        },
        {
          "name": "Parachichi / Tangawizi",
          "english": "Avocado / Ginger",
          "price": "1,000"
        },
        {
          "name": "Bungo",
          "english": null,
          "price": "2,000"
        }
      ]
    },
    {
      "id": "signature",
      "title": "Vintage Signature",
      "subtitle": "House blends with local fruit",
      "items": [
        {
          "name": "Vintage Nado",
          "english": "",
          "price": "2,000"
        },
        {
          "name": "Nado Rich",
          "english": "",
          "price": "4,000"
        },
        {
          "name": "Vintage Diatta",
          "english": "",
          "price": "2,000"
        },
        {
          "name": "Diatta Plus",
          "english": "",
          "price": "4,000"
        },
        {
          "name": "Vintage Bonzy Plus",
          "english": "",
          "price": "2,000"
        },
        {
          "name": "Bonzy Spice",
          "english": "",
          "price": "3,000"
        },
        {
          "name": "Vintage Gamers",
          "english": "",
          "price": "2,000"
        },
        {
          "name": "Gamers Plus",
          "english": "",
          "price": "3,000"
        },
        {
          "name": "Vintage Tropical",
          "english": "",
          "price": "4,000"
        },
        {
          "name": "Tropical Light",
          "english": "",
          "price": "3,000"
        },
        {
          "name": "Guava Sunset",
          "english": "",
          "price": "3,000"
        },
        {
          "name": "Vintage Angel",
          "english": "",
          "price": "3,000"
        },
        {
          "name": "Aloe Calm",
          "english": "",
          "price": "2,000"
        }
      ]
    },
    {
      "id": "movie-box",
      "title": "Vintage Movie Box",
      "subtitle": "Layered cups and richer blends",
      "items": [
        {
          "name": "Mango Milk",
          "english": "",
          "price": "2,000"
        },
        {
          "name": "Movie Box Deluxe",
          "english": "",
          "price": "3,000–5,000"
        }
      ]
    }
  ],
  flavours: [
    { name: 'Rozela', eng: 'Roselle', field: '#6E1B2E', ink: 'ivory', price: '1,000',
      note: 'Sour cherry-deep, steeped from dried calyces the same morning. Poured cold, never sweetened.' },
    { name: 'Ukwaju', eng: 'Tamarind', field: '#B85C38', ink: 'ink', price: '1,000',
      note: 'Sticky, brown-sugar tart. The one that makes you close one eye.' },
    { name: 'Embe', eng: 'Mango', field: '#E9A23B', ink: 'ink', price: '1,000',
      note: 'Thick as custard in season, loosened with a little lime so it drinks.' },
    { name: 'Nanasi', eng: 'Pineapple', field: '#E7C77A', ink: 'ink', price: '1,000',
      note: 'Sharp, sunny, pressed with the core for the bite it carries.' },
    { name: 'Parachichi', eng: 'Avocado', field: '#8FA65B', ink: 'ink', price: '1,000',
      note: 'Green and buttery, whipped with a little ginger so it stays savoury.' },
    { name: 'Vintage Angel', eng: 'Coast blend', field: '#C9A45B', ink: 'ink', price: '3,000',
      note: 'Rozela, tangawizi, ndimu, ubuyu, ukwaju. Sour, warm, cold all at once.' },
  ],
};

/* shape guards ---------------------------------------------------------- */
const str = (v, fallback) => (typeof v === 'string' && v.trim() ? v : fallback);
const obj = (v) => (v && typeof v === 'object' && !Array.isArray(v) ? v : {});

/** Deep-merge saved content over DEFAULTS, dropping anything malformed. */
export function normalise(raw) {
  const r = obj(raw);
  const out = {
    hero: { ...DEFAULTS.hero, ...obj(r.hero) },
    quote: { ...DEFAULTS.quote, ...obj(r.quote) },
    numbers: { ...DEFAULTS.numbers, ...obj(r.numbers) },
    visit: { ...DEFAULTS.visit, ...obj(r.visit) },
    cards: [],
    menu: [],
    flavours: [],
  };
  for (const k of Object.keys(DEFAULTS.hero)) out.hero[k] = str(out.hero[k], DEFAULTS.hero[k]);
  for (const k of Object.keys(DEFAULTS.quote)) out.quote[k] = str(out.quote[k], DEFAULTS.quote[k]);
  for (const k of Object.keys(DEFAULTS.visit)) out.visit[k] = str(out.visit[k], DEFAULTS.visit[k]);
  for (const k of Object.keys(DEFAULTS.numbers)) {
    if (k === 'title' || k === 'note') out.numbers[k] = str(out.numbers[k], DEFAULTS.numbers[k]);
    else out.numbers[k] = Number.isFinite(+out.numbers[k]) ? Math.max(0, Math.round(+out.numbers[k])) : DEFAULTS.numbers[k];
  }

  (Array.isArray(r.cards) ? r.cards : DEFAULTS.cards).forEach((c, i) => {
    const d = DEFAULTS.cards[i] || DEFAULTS.cards[0];
    const card = obj(c);
    out.cards.push({
      n: str(card.n, String(i + 1).padStart(2, '0')),
      name: str(card.name, d.name),
      sub: str(card.sub, d.sub),
      copy: str(card.copy, d.copy),
      price: str(card.price, d.price),
      kind: card.kind === 'slab' ? 'slab' : '',
    });
  });

  (Array.isArray(r.menu) ? r.menu : DEFAULTS.menu).forEach((c, i) => {
    const d = DEFAULTS.menu[i] || DEFAULTS.menu[0];
    const cat = obj(c);
    out.menu.push({
      id: str(cat.id, d.id),
      title: str(cat.title, d.title),
      subtitle: str(cat.subtitle, d.subtitle),
      items: (Array.isArray(cat.items) ? cat.items : []).map((it, k) => {
        const item = obj(it);
        const fallback = d.items[k] || d.items[0];
        return {
          name: str(item.name, fallback.name),
          english: typeof item.english === 'string' ? item.english : fallback.english,
          price: str(item.price, fallback.price),
        };
      }),
    });
  });

  (Array.isArray(r.flavours) ? r.flavours : DEFAULTS.flavours).forEach((f, i) => {
    const d = DEFAULTS.flavours[i] || DEFAULTS.flavours[0];
    const fl = obj(f);
    out.flavours.push({
      name: str(fl.name, d.name),
      eng: str(fl.eng, d.eng),
      field: /^#[0-9a-f]{6}$/i.test(fl.field || '') ? fl.field : d.field,
      ink: fl.ink === 'ivory' ? 'ivory' : 'ink',
      price: str(fl.price, d.price),
      note: str(fl.note, d.note),
    });
  });

  return out;
}

/** Content baked into the repo by a publish (optional, may not exist). */
export function baked() {
  try { return normalise(window.__VJP_CONTENT__); } catch { return null; }
}

/** Whatever the visitor should see: device edits, else baked, else defaults. */
export function load() {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved) return normalise(JSON.parse(saved));
  } catch { /* private mode, quota, bad JSON — fall through */ }
  return baked() || normalise(DEFAULTS);
}

export function save(data) {
  try {
    localStorage.setItem(KEY, JSON.stringify(data));
    return true;
  } catch { return false; }
}

export function clear() {
  try { localStorage.removeItem(KEY); } catch { /* nothing to do */ }
}
