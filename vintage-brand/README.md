# VINTAGE — Premium Tanzanian Juice Brand Rebuild

A complete concept redesign for the juice business in the supplied Google Maps / menu photos. It keeps the recognisable **Vintage**, cup and black/gold equity while making the system calmer, more consistent and more premium for Dar es Salaam.

## Preview

From this folder:

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

Then open:

- `http://localhost:8000/index.html` — landing page
- `http://localhost:8000/menu.html` — full printable menu
- `http://localhost:8000/brand-kit.html` — full brand presentation

## Main files

| File | What it is |
|---|---|
| `index.html` | Responsive landing page with hero, story, menu tabs, packaging and visit section. |
| `menu.html` | Full print-friendly menu with every blend from the reference photo. |
| `brand-kit.html` | Visual brand guidelines, assets, colour/type, menu, packaging, Maps cleanup and Flow prompts. |
| `styles.css` | Shared design system, self-hosted fonts, print stylesheet. |
| `app.js` | Menu category tabs, copy-prompt buttons, footer year. |
| `BRAND_GUIDELINES.md` | Written strategy, naming, voice, palette, typography, usage rules. |
| `GOOGLE_BUSINESS_PROFILE.md` | Exact cleanup checklist for the Maps listing. |
| `GOOGLE_FLOW_PROMPTS.md` | Copy-paste Google Flow / Veo scene prompts. |
| `flow-master-prompt.txt` | One 30-second master video prompt, ready to paste. |
| `menu-data.json` | Structured menu data for a future app / CMS. |
| `assets/` | Logos, SVG sources, PNG exports, pattern, label, menu board, photography. |
| `fonts/` | Cormorant Garamond + Manrope WOFF2 files (self-hosted, no CDN). |
| `flow-inputs/` | Ten ready-to-upload reference and style frames for Google Flow. |
| `vintage-brand-assets.zip` | Everything above in one ~7 MB download (build artifact, ignored by Git). Rebuild with the `zip` command in `.gitignore`. |

## Finished, composited assets

These are real composites of the vector artwork onto the generated photography, not mock overlays:

| File | Use |
|---|---|
| `assets/packaging-labelled.jpg` | Bottle + cup + tub with the real round label, shaded to sit in the brass light. Product/Maps/Instagram. |
| `assets/social-post-branded.jpg` | 1080×1080 Instagram post: roselle juice, kanga shadow, logo + `Asili safi. Ladha ya kisasa.` |
| `assets/social-story-branded.jpg` | 1080×1920 story / WhatsApp status: hero still life, logo, tagline, service line. |
| `assets/gbp-cover-branded.jpg` | 1600×900 Google Business Profile cover: three juices, logo, tagline, `FRESHLY BLENDED · TAKEAWAY · DAR ES SALAAM`. |
| `assets/brand-sheet.png` / `.jpg` | 1600×2520 one-page brand sheet: logo, palette, packaging, label, board, type and the publish checklist. Send this to the owner. |

Also finished: `assets/menu-board.png` (1080×1440 print board), `assets/label-round.png` (600×600 packaging label), `assets/logo-primary-on-ink.png`, `assets/logo-experience-on-ink.png`, `assets/brand-pattern.png`.

Every SVG uses **Cormorant Garamond** and **Manrope** by name, so the files stay editable in Figma/Illustrator/Inkscape and match the website exactly. The PNGs were rasterised with those fonts loaded.

## Google Flow upload pack

`flow-inputs/` contains exactly the ten files `GOOGLE_FLOW_PROMPTS.md` asks for:

**Original references** — `reference-01-menu.jpg`, `reference-02-products.jpg`, `reference-03-listing.jpg`
**New style frames** — `style-hero-juices.jpg`, `style-packaging.jpg`, `style-storefront.jpg`, `style-social-rose.jpg`, `style-menu-board.png`, `style-label.png`, `style-pattern.png`

Upload them as **style references only**. Never ask Flow to read or reproduce text from them.

## Replace before publishing

Every `REPLACE` marker in the HTML, plus:

- `+255 XXX XXX XXX` — real phone / WhatsApp
- `hello@vintage.co.tz` — real email and domain
- `@vintagejuicepoint` — real Instagram / social handle
- `Add opening hours before publishing`
- `Add verified website / menu URL`
- Confirm all menu prices and the ambiguous ingredient spellings from the original photo.

The plus code `58F5+24 Dar es Salaam` came from the supplied Maps screenshot and should be checked too.

## Brand decision

- **Visual logo:** `VINTAGE · JUICE POINT`
- **Existing Google listing:** keep `Vintage Experience` until the owner confirms the trading name, so the existing reviews are preserved.
- **Campaign line:** `THE VINTAGE EXPERIENCE`
- **Tagline:** `Asili safi. Ladha ya kisasa.` — confirm Kiswahili copy with the owner.

## Video

No video is rendered here. Use `GOOGLE_FLOW_PROMPTS.md` or `flow-master-prompt.txt` in Google Flow, upload the files in `flow-inputs/` as references, and add the real logo/text overlays in post-production. Do not let the video model generate readable text.

## Note on sources

The original menu prices, plus code, service attributes and review count were read from the screenshots supplied. A public web search did not produce verified contact details for this specific juice business; unrelated businesses using the word “Vintage” were deliberately not used. No phone number, email, domain, hours or social handle has been invented as fact.
