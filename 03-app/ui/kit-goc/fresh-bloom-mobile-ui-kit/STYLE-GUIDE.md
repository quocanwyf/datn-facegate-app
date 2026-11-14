# "Fresh Bloom" UI Kit — Style Guide

Reverse-engineered from 4 mobile screens of a food-scanning app (home / scan camera / composition breakdown / search home). Only the **style** is kept: no logos, copy, photos or illustrations are reused. Target application: **a hotel/stay booking marketplace (web, responsive)**.
Values marked *(est.)* were read off a compressed screenshot and may be off by ±2px or ±1 shade.

---

## 1. Visual analysis

| | |
|---|---|
| **Style keywords** | soft-tactile minimal · warm-neutral monochrome + one lime accent · oversized radii · photo-forward · subtle "bloom" gradients |
| **What "soft" means here** | radius ≥ 16px on everything interactive; shadows ≤ 8% opacity; surfaces separated by **tone** (white on warm gray), not by borders |
| **Mood / audience** | Fresh, healthy, calm, friendly. Consumer app, 20–40 y/o, mobile-first. |
| **Density** | Spacious: ~24px screen padding, 16–24px gaps, 1–2 focal elements per viewport. |
| **Mode** | Light only in reference (dark mode is derived in tokens). |
| **Shared patterns across screens** | Floating 56px rounded-square icon buttons in the top corners; large two-tone headline; full-bleed food photo as hero; 3-up metric tiles (icon + value + label); white chip pills with tiny colored icons. |
| **Variations** | Screen 2 uses a gray→white vertical gradient behind the photo; screen 3 uses a multi-color radial "petal" chart; screens 1/4 put cards on a slightly darker gray rail. |

---

## 2. Design tokens

### 2.1 Color

| Role | Token | Hex | Notes |
|---|---|---|---|
| Primary (lime / "leaf") | `leaf-400` | `#A3D853` *(est.)* | Scan frame, active nav, selection. **Fill only — never text on white (1.7:1).** |
| Primary text/icon on light | `leaf-700` / `leaf-800` | `#4F7C20` / `#3B5D1C` | 4.96:1 on white / 6.2:1 on bg |
| Secondary (forest) | `forest-700` | `#2E5E14` *(est.)* | Hero/backdrop gradient, marketing surfaces |
| Accent (amber) | `amber-500` | `#F5A00A` *(est.)* | 2nd metric, rating stars, bloom center. Text version: `amber-700 #A9610C` |
| Accent 2 (berry/tomato) | `berry-500` | `#D92D2F` *(est.)* | 3rd metric, destructive. Text on bg: `berry-600 #B5241F` |
| Inverse | `stone-900` | `#1A1A18` | Black circular CTA (capture button), primary pill buttons |

Full 50–900 scales are in `design-tokens.json` / `tailwind.config.js`.

**Neutrals (warm stone):** `0 #FFFFFF` · `25 #F7F6F4` · `50 #F1F0ED` (surface) · `100 #EAE8E4` (app bg) · `200 #DDDAD5` (border) · `300 #C7C4BE` · `400 #A3A09A` · `500 #85827C` · `600 #66635E` · `700 #4A4844` · `800 #2E2D2A` · `900 #1A1A18` · `950 #0F0F0E`

| Semantic | Text-safe hex | Surface |
|---|---|---|
| success | `#2F7A1F` (5.35:1 white) | `leaf-50` |
| warning | `#94570B` (4.73:1 bg) | `amber-50` |
| error | `#B5241F` (5.3:1 bg) | `berry-50` |
| info | `#2569B5` (5.58:1 white) | `#EAF2FB` |

**Gradients**
- `backdrop`: `linear-gradient(160deg, #2E5E14, #A8C957)` — marketing/hero only.
- `bloom`: `radial-gradient(#FFB547 → #FFE07A 45% → #C9EE8A 75% → transparent)` — data-viz petals, highlight halos.
- `scan`: lime 0 → 40% opacity overlay — "selected / analysing" media state.
- `media-fade`: image bottom fades into `bg`.

**WCAG AA check (measured)**

| Pair | Ratio | Result |
|---|---|---|
| Reference gray label `#8A8A86` on bg `#EAE8E4` | 2.83 | ❌ fails → **replaced by `#66635E` = 4.89** ✅ |
| text-primary on bg | 14.24 | ✅ |
| ink on lime button | 10.38 | ✅ (white on lime would fail) |
| lime on white (as text) | 1.68 | ❌ → use `leaf-700` 4.96 ✅ |
| amber-500 on white (as text) | 2.12 | ❌ → use `amber-700` 4.77 ✅ |
| leaf-700 on bg | 4.05 | ⚠️ large text only → `leaf-800` 6.2 ✅ |
| Dark: text / text-2 / lime on dark bg | 16.5 / 7.04 / 11.1 | ✅ |

### 2.2 Typography
- **Detected:** a neutral geometric-grotesk with tight tracking, close to **SF Pro Display / Inter Display** *(est.)*.
- **Free alternatives (Google Fonts):** **Inter** (closest, has Display optical size) · **Manrope** (rounder, friendlier) · bonus: Plus Jakarta Sans.
- **Pairing rule:** one family. Headings = Display cut, semibold 600, negative tracking. Body = text cut, regular 400.
- **Two-tone headline habit:** line 1 in `text-primary`, line 2 in `text-secondary` (e.g. "Find your / next stay").
- **Numbers:** `tabular-nums`, value semibold, unit in lighter weight (`320 g` → value + muted unit). Use locale decimals.
- **Casing:** Sentence case / Title Case for names. No ALL-CAPS anywhere.

| Token | Size / line-height | Weight | Tracking | Use |
|---|---|---|---|---|
| display | 56 / 1.05 | 600 | -0.03em | landing hero |
| h1 | 40 / 1.1 | 600 | -0.025em | page title (mobile: 32) |
| h2 | 32 / 1.15 | 600 | -0.02em | detail title ("Tomato Paste" size) |
| h3 | 24 / 1.25 | 600 | -0.015em | section title |
| h4 | 20 / 1.3 | 600 | -0.01em | card title |
| h5 | 18 / 1.35 | 500 | -0.005em | list item title |
| h6 | 16 / 1.4 | 600 | 0 | small heading |
| body-lg / md / sm | 18/1.55 · 16/1.5 · 14/1.45 | 400 | 0 | text |
| caption | 12 / 1.35 | 400 | +0.01em | meta, chip values |
| label | 13 / 1.2 | 500 | +0.005em | form labels, chips |
| button | 15 / 1 | 600 | -0.005em | buttons |
| metric | 22 / 1.1 | 600 | -0.01em | stat tiles (tabular) |

### 2.3 Spacing & layout
- **Base unit:** 4px (most gaps land on 8/12/16/24).
- **Scale:** 0, 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96.
- **Rhythm:** 8px inside chips · 12px between tiles · 16px card padding (mobile) / 24px (desktop) · 24px screen gutter · 40–64px between page sections.
- **Grid:** mobile 4 col / 16px gutter / 20–24px margin · tablet 8 col / 20px · desktop 12 col / 24px gutter, max-width **1280px**, text max 720px.
- **Breakpoints:** 640 / 768 / 1024 / 1280 / 1440.

### 2.4 Shape
| Token | px | Use |
|---|---|---|
| xs | 8 | tiny tags, image thumbnails in tables |
| sm | 12 | inputs (compact), tooltips |
| md | 16 | icon buttons (small), menu items |
| lg | 24 | stat tiles, cards, list rows, inputs (default) *(est. 20–24)* |
| xl | 32 | sheets, modals, large media |
| 2xl | 44 | page-level containers, device frame, hero panels *(est.)* |
| full | 9999 | chips, pills, avatars, circular CTA |

Rule: **nested radius = outer radius − padding** (a 24px card with 8px padding holds 16px images).

### 2.5 Elevation
| Level | Value | Use |
|---|---|---|
| 0 | none — tone change only | tiles on surface |
| 1 | `0 1px 2px rgb(26 26 24/.05)` | chips, inputs |
| 2 | `0 2px 6px /.04, 0 8px 24px -4px /.06` | cards, floating icon buttons |
| 3 | `0 12px 32px -8px /.06, 0 24px 64px -12px /.08` | modals, sticky booking panel, popovers |
| ring | `0 0 0 4px lime/35%` | focus |

Borders are rare: separation comes from white-on-gray tone. Use a 1px `border` only in dark mode, on tables, or when two whites touch.

### 2.6 Motion (inferred)
- Durations: fast 120ms (hover/press) · base 200ms (toggle, tab) · slow 320ms (sheet, modal) · scan loop 1.6s.
- Easing: standard `cubic-bezier(.2,0,0,1)` · emphasized (slight overshoot) `(.3,0,0,1.2)` for pop-ins · exit `(.4,0,1,1)`.
- Hover: surface lightens one step (stone-50 → white) + shadow 1→2. Press: `scale(.97)`. Selection: lime fill/outline fades in with emphasized easing.
- Honor `prefers-reduced-motion` (durations → 0).

---

## 3. Iconography
- **Style:** two families.
  - **Navigation / UI icons:** outline, 1.75–2px stroke, rounded caps & joins, 24px grid, `text-secondary` color.
  - **Data/metric icons:** small **filled** glyphs (leaf, drop, cube) in category colors, 16–20px.
- **Closest open-source set:** **Phosphor** — has matching *Regular* (outline) and *Fill* weights of the same glyph, rounded geometry, and both a leaf and drop. Fallback: Lucide (outline only; pair with Phosphor Fill for metrics).
- **Spacing:** icon→text 8px (buttons), 4–6px (chips), 12px (list rows).
- **Color per state:** default `text-secondary` · hover `text-primary` · active/selected `primary-strong` (or lime dot indicator under nav icon) · disabled `text-disabled`.
- **Containers:** 56×56 white rounded-square (radius 18–20 *(est.)*, shadow 1) for top-bar actions; 40px circle for avatar; notification = 8px amber dot top-right.

---

## 4. Component inventory

All interactive components: focus = `shadow-ring` · disabled = 40% opacity, no shadow · loading = spinner replaces icon, width locked.

| Component | Anatomy & variants | Sizes | States / tokens |
|---|---|---|---|
| **Button** | primary (lime bg, ink text) · inverse (black bg, white text — main CTA) · secondary (white bg, shadow-1) · ghost (text-secondary) · destructive (berry-600) | sm 36h · md 44h · lg 52h; radius full; px 16/20/24 | hover: 1 step lighter/darker + shadow-2; active: scale .97 |
| **Circular CTA** | 72px black disc with 4px white inner ring (capture-button pattern) → use for "Search" on mobile hero or map FAB | 56 / 72 | press scale .94 |
| **Icon button** | white rounded-square, centered 24px icon | 40 / 48 / 56 | hover shadow-2; selected: lime bg |
| **Input / Search bar** | white pill, leading search icon (stone-500), placeholder text-secondary, optional trailing filter icon-button (separate 56px square, as in reference) | 48 / 56h, radius full or lg | focus: ring + border lime-500; error: border berry-600 + helper text |
| **Select / date / guest picker** | input anatomy + chevron; dropdown = surface-raised, radius lg, shadow-3, 8px padding, items radius md | same as input | selected item: leaf-50 bg + check in leaf-700 |
| **Checkbox / radio** | 20px, radius 6 / full, border stone-300 | — | checked: lime fill + ink check |
| **Switch** | 44×26 track, full radius | — | on: lime track, white thumb with shadow-1 |
| **Stat tile** | white tile, radius lg, centered: colored icon (20) → metric value → muted label | 1/3 of row, 12px gap | static; clickable variant gets hover lift |
| **Card (listing)** | radius lg/xl, white, image on top (radius = card − 8) or image overflowing outside the card edge (reference "plate breaking out"), title h4, meta row of chips | compact / default / featured | hover shadow 2→3, image scale 1.03 |
| **Chip / badge** | pill, stone-50 or white bg, 4px gap leading filled icon + caption value | 24 / 28 / 32h | filter chip selected: ink bg + white text, or lime bg |
| **Tabs / segmented** | pill track on stone-50, active pill = white + shadow-1 | 36 / 44 | 200ms slide |
| **Bottom nav (mobile)** | white bar, radius xl top, 3–4 outline icons, active = colored filled icon + 4px dot; can host a black circular primary action at one end | 72h | — |
| **Top bar** | 56px icon-button left (back/menu), right (bookmark/notification + avatar) | — | bookmark active: amber fill |
| **Avatar** | circle, 2px white ring | 32 / 40 / 56 | — |
| **List row** | thumbnail 72–88 in tinted rounded square (lime-50 / amber-50 bg), title + trailing muted value, chips row below | — | hover surface-25 |
| **Modal / sheet** | surface-raised, radius xl (sheet: top only), 24–32 padding, shadow-3, scrim stone-900/40 + 8px blur | sm 400 / md 560 / lg 720 | pop-in 200ms |
| **Toast** | inverse pill, white text, leading semantic icon | auto | slide-up 200ms, 4s |
| **Pagination** | row of 40px circular buttons, active = ink fill | — | — |
| **Breakdown / donut chart** | "petal" radial segments with bloom gradient, % value h6 + label caption in each petal, image or total in center | — | for rating breakdowns, price composition |
| **Empty state** | centered illustration slot in a bloom-gradient circle, h4 title, body-sm text, primary button | — | — |
| **Table** | no vertical borders, row separators stone-200, header label style, rows 56h, first cell has thumbnail | — | hover row surface-25 |

---

## 5. Layout templates

1. **Home / discovery** — top bar (avatar + bell) → two-tone h1 → search pill + filter square → section header ("Popular stays" + "See all" link) → horizontal carousel of tall cards (image breaking out of top) → bottom nav. Whitespace: 24 / 16 / 32 / 16.
2. **Hero media / capture** — full-width media on gray→white vertical gradient, overlay corner brackets or lime scan sheen on the active item, centered title h2 + muted subtitle, 3-up stat tiles, single circular CTA at bottom.
3. **Detail / breakdown** — floating back + bookmark buttons on top of the page, centered visualization (petal chart / gallery), centered title + muted meta, white sheet (radius xl top) with list rows.
4. **Dashboard / recents** — menu button → two-tone headline → search → "Last …" section → card rail.
- **Image treatment:** subject cut-outs or round "plate" crops, white rim, soft drop shadow; photos 4:3 or 1:1 inside cards, 16:9 heroes; radius = container − padding; no dark overlays (use `media-fade` to bg instead).
- **Web adaptation:** keep the same blocks; desktop puts search + filters in a 56px pill bar under the headline, results in a 12-col grid (3–4 cards), and a sticky radius-xl booking panel at shadow-3 on detail pages.

---

## C. Do / Don't

**Do**
- Separate layers by tone (white on `#EAE8E4`) before reaching for borders.
- Use lime as a *fill/highlight*, ink as text on it; `leaf-700/800` for green text.
- Keep one focal element per view; let photos carry color.
- Use two-tone headlines and muted units next to bold numbers.
- Use pill shapes for anything you tap that is short (chips, buttons, search).
- Pair each metric with a small filled color icon (consistent category → color mapping).

**Don't**
- Put white text on lime or lime/amber text on white.
- Use pure gray `#888`-style labels (fails AA) — use `stone-600`.
- Mix sharp (<8px) corners with the soft radius scale.
- Use heavy shadows (>10% opacity) or dark image overlays.
- Introduce extra brand colors; beyond lime/amber/berry, use neutrals.
- Use ALL-CAPS labels or more than 2 font weights on one screen.

---

## D. Generation prompt (paste into any AI UI tool)

```
Design a {SCREEN} for {PRODUCT} in a soft, warm-minimal, photo-forward style.
Background warm light gray #EAE8E4; surfaces white #FFFFFF and #F1F0ED, separated by tone, almost no borders.
One accent: lime #A3D853 used only as fills/highlights with ink #1A1A18 text on it; secondary accents amber #F5A00A and tomato #D92D2F only for small data icons. Green text uses #3B5D1C. Secondary text #66635E.
Font: Inter (Display for headings), semibold 600 headings with -2% tracking, regular 400 body. Headlines are two-tone: line 1 #1A1A18, line 2 #66635E. Numbers tabular, bold value + muted unit.
Radii: 24px cards and tiles, 32–44px large panels, fully rounded pills for buttons, chips and search. Shadows very soft (≤8% opacity, large blur).
Icons: Phosphor — outline 2px for UI, small filled colored glyphs for metrics. Top-corner actions are 56px white rounded-square icon buttons.
Primary CTA: black pill or black circular button. Generous spacing (4px grid, 24px gutters, 1–2 focal elements per view). Images: rounded, soft-shadowed, can break out of their card edge; fade into background instead of dark overlays.
Light mode, WCAG AA contrast, desktop {WIDTH}px.
```

---

## E. Example prompts for the booking marketplace

**1. Search results page**
> Design a **search results page** for **a hotel & homestay booking marketplace**, using the style above, desktop 1440px. Top: logo-free top bar with 56px icon buttons (menu left; bookmark, bell, avatar right). Two-tone headline "Stays in Đà Lạt / 128 places found". A 56px white pill search bar (destination · dates · guests) with a separate square filter button. Row of filter chips (Price, Rating 8+, Free cancellation, Breakfast) — selected chips ink-filled. Left: 3-column grid of listing cards (radius 24, photo 4:3 with 16px radius, title h4, muted location, chips with small filled icons for rating ★ amber, distance, breakfast leaf green; price as bold tabular number + muted "/night"). Right: sticky rounded-32 map panel with black pill price markers, selected marker lime. Pagination as 40px circles.

**2. Property detail page**
> Design a **property detail page** for **a hotel & homestay booking marketplace**, style above, desktop 1440px. Floating back and bookmark buttons over a large rounded-44 photo gallery (1 large + 4 small, 16px gaps). Below: two-tone title "Pine Hill Villa / Đà Lạt, Lâm Đồng". Three stat tiles (rating 9.2 with amber star, 2 bedrooms with leaf icon, 1.2 km to center with tomato pin). A "Guest review breakdown" petal-shaped radial chart using the lime→amber bloom gradient with % labels (Cleanliness, Location, Staff, Value, Comfort). Amenities as chip grid, room options as white list rows with tinted thumbnail squares. Right column: sticky white booking panel, radius 32, shadow level 3, date + guest selects, price breakdown, black pill "Reserve" button.

**3. Checkout page**
> Design a **checkout page** for **a hotel & homestay booking marketplace**, style above, desktop 1440px. Two-tone headline "Confirm and pay / 3 nights · 2 guests". Left (8 cols): stacked white cards radius 24 — Guest details (pill inputs, 56px tall, lime focus ring), Payment method (segmented pill tabs: Card / E-wallet / Bank transfer; selected = white pill with soft shadow), Cancellation policy with a leaf-50 success notice. Right (4 cols): sticky summary card with property thumbnail breaking out of the top edge, chips for dates and guests, line items with tabular numbers and muted labels, total in metric style, black pill "Pay now" button, small trust badges in muted caption text. Include error state on one input (tomato #B5241F helper text).
