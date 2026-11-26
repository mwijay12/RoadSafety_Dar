# VINTAGE — Brand Rebuild Guidelines

**Working brand:** `VINTAGE JUICE POINT`  
**Google Maps listing:** `VINTAGE EXPERIENCE`  
**Location:** Dar es Salaam, Tanzania  
**Category:** Juice shop / fresh juice bar  
**Status:** Concept redesign — replace all contact placeholders before publishing.

> I did not find verified phone, email, hours, or social handles for this specific juice business in the supplied screenshots or public snippets. Do not copy phone numbers or emails from unrelated businesses that happen to use the word “Vintage”.

---

## 1. Strategy

### The problem
The current materials have strong local recognition — a black/gold cup, fruit colours, a busy handwritten menu — but they do not read as premium:

- The menu board mixes script fonts, all-caps ingredient strings, clipart fruit and inconsistent prices.
- “Vintage Juice Point Natural”, “Vintage Experience” and “Summer Wavy” compete with each other.
- Product photos are inconsistent: different bottles, caps, labels and backgrounds.
- The Google listing has no phone, hours, website or menu link in the screenshots supplied.
- The visual world feels more like a poster than a crafted hospitality brand.

### The opportunity
Keep the equity people already recognise — **VINTAGE**, the cup, black and gold, Tanzanian fruit — then remove the noise.

### Positioning
> A premium everyday juice point in Dar es Salaam: local fruit, coastal warmth and quietly modern craft.

Not a generic smoothie chain. Not a loud nightlife brand. Not a luxury import that ignores Tanzania.

### Recommended naming system
| Use | Name |
|---|---|
| Visual logo / packaging / menu | **VINTAGE · JUICE POINT** |
| Existing Google Maps listing | **Vintage Experience** — keep until the owner confirms the trading name, so existing reviews are not lost |
| Experience / campaign line | **THE VINTAGE EXPERIENCE** |
| Location descriptor | **DAR ES SALAAM · TANZANIA** |

Do not add keywords such as “best juice”, “fresh juice”, or “Dar es Salaam” to the Google business name itself. Put those in the description, category and website instead.

---

## 2. Voice and copy

**Tone:** warm, calm, confident, Kiswahili-first with light English support.

### Primary tagline
**Asili safi. Ladha ya kisasa.**  
*Clean origin. Modern taste.*

### Secondary line
**Chukua ladha ya mji wako.**  
*Carry the taste of your city.*

### Short description
> Freshly blended fruit, signature mixes and takeaway cups, made with the character of Dar es Salaam.

### Longer description
> Vintage is a Dar es Salaam juice point built around local fruit: roselle, tamarind, mango, pineapple, passion fruit, avocado, watermelon, grapes and baobab. Clean blends, quiet brass details and a warm Swahili-coast welcome — premium without losing the everyday feel.

> Confirm the Kiswahili lines with a native-speaking owner before final print.

---

## 3. Visual identity

### Palette
| Name | Hex | Use |
|---|---:|---|
| Vintage Ink | `#0D1512` | Primary background, menus, labels |
| Deep Olive | `#131D19` | Secondary surfaces |
| Warm Brass | `#C9A45B` | Rules, monogram, accents |
| Light Brass | `#E7C77A` | Highlights, prices, foil |
| Ivory | `#F7F1E3` | Wordmark, body text on dark |
| Stone | `#CFC5B2` | Secondary text |
| Terracotta | `#B85C38` | Walls, packaging plinths, social backdrops |
| Roselle | `#6E1B2E` | Roselle juice, accent only |
| Mango Gold | `#E9A23B` | Mango/passion juice accent |
| Avocado Green | `#8FA65B` | Avocado blend accent |

### Typography
- **Display / wordmark:** Cormorant Garamond, 600. Elegant serif with wide tracking.
- **UI / menu / labels:** Manrope, 400 / 600 / 700. Clean geometric sans.
- **Fallback in vector exports:** DejaVu Serif + DejaVu Sans.

Never use cursive script, simulated foil bevels, outline text, or more than two typefaces in one layout.

### Logo system
Files in `assets/`:

- `logo-primary-dark.svg` / `.png` — cream + brass lockup for dark backgrounds.
- `logo-primary-light.svg` / `.png` — ink + brass lockup for light backgrounds.
- `logo-experience-dark.svg` / `.png` — alternate for the “Vintage Experience” listing/campaign.
- `logo-mark.svg` / `.png` — circular cup monogram for stickers, favicons and caps.
- `label-round.svg` / `.png` — round packaging label.
- `pattern.svg` / `brand-pattern.png` — subtle Swahili-coast geometric texture.

**Mark idea:** a simplified cup and straw inside a double brass circle, with two quiet horizon arcs referencing the coast. It keeps the old cup memory without copying the old logo.

### Clear space
Keep at least the height of the circular monogram around the logo on all sides. Minimum monogram size: 32 px digital / 12 mm print.

### Do not
- Do not stretch, rotate, recolour, or add a drop shadow to the logo.
- Do not place the cream logo on a light background.
- Do not recreate the old “Summer Wavy” script.
- Do not add fruit clipart inside the logo circle.
- Do not invent a founding year, phone number, email, or address.

---

## 4. Menu redesign

### Changes made
- One clear hierarchy: category → blend name → ingredients → price.
- Prices formatted as `1,000`, `2,000`, `3,000–5,000` with a single “PRICES IN TSH” note instead of repeating `=` on every line.
- Light English glosses for visitors: Roselle, Tamarind, Mango, Pineapple.
- Spelling cleaned where the photo was ambiguous: `ubuyu`, `aloe vera`, `apple/pears`.
- Ingredients moved to a smaller secondary line so the board breathes.
- Full blend list separated into `menu.html` / `menu-data.json`; the printed board stays curated.

> Prices and ingredient lists were transcribed from the reference photo. Confirm every price and the ambiguous `peas/apple`, `ubuvu/ubuyu`, `alozera/aloe vera` entries with the owner before printing.

### Board asset
`assets/menu-board.png` is a ready-to-print 3:4 board. The editable source is `assets/menu-board.svg`.

---

## 5. Packaging

- Clear cylindrical bottle, matte black cap, one round brass-foil label.
- Clear smoothie cup with domed lid, same label system.
- Small clear dessert/tub container with the same label.
- No script lettering, no mixed cap colours, no busy sticker collage.
- Use `label-round.svg` on the blank gold circles of the packaging set; the finished composite is `packaging-labelled.jpg`.

---

## 6. Photography

Use `assets/gbp-cover-branded.jpg`, `packaging-labelled.jpg`, `storefront.jpg` and `social-post-branded.jpg` as the new direction:

- Dark stone or charcoal plaster.
- Warm Dar es Salaam late-afternoon light.
- Brass and terracotta as quiet accents.
- Real fruit as still life, not illustrated clipart.
- Generous negative space for copy.
- Condensation, texture, hands, shadows — tactile and human.
- No readable text or logos generated inside the photo; overlay real vector type afterwards.

---

## 7. Digital / Google Business Profile

See `GOOGLE_BUSINESS_PROFILE.md`. The priority is to add the missing phone, hours, website, menu link and social handle, then replace the low-resolution menu photos with `menu-board.png`.

Known attributes from the supplied listing, to keep if still true:

- Takeaway
- Casual, trendy
- Popular for solo dining
- Groups, good for kids
- Credit cards, debit cards, NFC mobile payments
- Plus code: `58F5+24 Dar es Salaam`

---

## 8. Placeholders to replace

| Field | Placeholder used |
|---|---|
| Phone / WhatsApp | `+255 XXX XXX XXX` |
| Email | `hello@vintage.co.tz` *(placeholder domain)* |
| Instagram | `@vintagejuicepoint` *(placeholder handle)* |
| Hours | `Add opening hours before publishing` |
| Website | `Add verified website / menu URL` |
| Address line | `58F5+24 Dar es Salaam` from the supplied Maps screenshot |

Anything marked `REPLACE` in the HTML must be edited before the site goes live.

---

## 9. Deliverables

- `index.html` — responsive landing page.
- `menu.html` — full printable menu.
- `brand-kit.html` — visual presentation of the whole system.
- `GOOGLE_FLOW_PROMPTS.md` / `flow-master-prompt.txt` — video prompts.
- `GOOGLE_BUSINESS_PROFILE.md` — Maps cleanup checklist.
- `menu-data.json` — structured menu content.
- `assets/` — logos, pattern, label, menu board, photography.
- `assets/packaging-labelled.jpg`, `assets/social-post-branded.jpg`, `assets/gbp-cover-branded.jpg` — finished, composited brand images.
- `fonts/` — Cormorant Garamond and Manrope web fonts.
- `flow-inputs/` — reference photos and style frames to upload into Google Flow.
- `vintage-brand-assets.zip` — single-file download of the whole pack.
