# "Canopy" Web UI Kit — Style Guide

Reverse-engineered from 4 desktop screens of a project-management SaaS (project detail with events + calendar, reports table, project overview with map, sign-up/onboarding). Only the **style** is kept: no logo, product name, photos, maps or copy are reused. Target application: **the web side of a booking marketplace (partner/admin dashboard + account flows)**.
Values marked *(est.)* were read off compressed screenshots (±2px / ±1 shade).

---

## 1. Visual analysis

| | |
|---|---|
| **Style keywords** | light enterprise SaaS · soft glassmorphism frame · nature-teal accent · filled (borderless) controls · calm data density |
| **"Soft glass" defined** | The whole app sits in a 12px translucent frame (white 70% → sky 50% → olive 40% gradient, `backdrop-blur 24px`, radius 28) on a sky/landscape canvas. Inside the frame everything is opaque and flat. |
| **"Calm" defined** | One saturated color (teal) per screen, used only for primary action, active tab and sidebar. Everything else = white + 2 grays + pastel status pills. |
| **Mood / audience** | Trustworthy, eco/outdoor, professional. B2B operators and admins, 25–50 y/o. |
| **Density** | Comfortable: 48–50px table rows, 40–44px controls, 24–32px panel padding. |
| **Mode** | Light (dark derived in tokens). |
| **Shared patterns** | 64px header with filled search (scope dropdown + input + icon); 64px teal icon rail with a white active tile; breadcrumb on top of a banner; full-width equal-width tabs with teal underline; label-inside filled inputs; pastel status pills; 3-up "value + label" info tiles. |
| **Variations** | Banner is a photo (detail page) or a soft illustrated mist gradient (list page); overview page has no banner and uses a big h1 instead. Auth screens drop the shell and show floating glass cards. |

---

## 2. Design tokens

### 2.1 Color

| Role | Token | Hex | Use |
|---|---|---|---|
| Primary | `teal-600` | `#0E7C74` *(est.)* | Primary buttons, active tab text + 2px underline, checkboxes, progress |
| Primary hover | `teal-700` | `#0A5F59` | hover/pressed, text on soft teal |
| Primary soft | `teal-100` | `#DDF1EE` | Secondary button ("New sheet" style), selected chip, "New" tint |
| Sidebar | gradient `teal-500 → #0B7E73` | `#12A08F` *(est.)* | Icon rail |
| Secondary | `sky-300` | `#8CC8F2` *(est.)* | Canvas/backdrop sky, info accents, charts |
| Notification dot | — | `#E5484D` | 6px dot on bell |

**Neutrals (cool, slightly green-tinted):** `0 #FFFFFF` · `25 #FAFAFA` · `50 #F4F5F4` (filled inputs, table header, tiles) · `100 #EDEFEE` (dividers) · `200 #E3EBE9` (selected row) · `300 #D3D9D7` · `400 #A9B0AD` · `500 #828A87` · `600 #5F6865` (secondary text) · `700 #46504D` · `800 #2C3836` · `900 #1B2B2A` (primary text, greenish black) · `950 #0E1A19`.

**Status pills (bg / text):**

| Status | Example | bg | fg (AA-fixed) | Ratio |
|---|---|---|---|---|
| new | New | `#DFF5F8` | `#0A6670` | 5.89 |
| progress | In development, Draft, Pending | `#FCEFB4` | `#7A5B00` | 5.46 |
| success | Approved, Active, Confirmed | `#DDF6DF` | `#256B2F` | 5.69 |
| info | In review | `#E3F2FD` | `#1767AD` | 5.14 |
| error | Overdue, Cancelled | `#FDECEB` | `#B42318` | ≈6 |
| neutral | Inactive, counts | `#EDEFEE` | `#46504D` | ✅ |

**Gradients:** `sidebar` (180°, #12A08F → #0B7E73) · `glass-frame` (see §1) · `header` (180°, #EAF6F4 → white, very subtle under the top bar) · `hero-mist` (teal-200 80% → teal-50 90%, over banner art for title legibility).

**WCAG AA check (measured):**

| Pair | Ratio | Result |
|---|---|---|
| white on teal-600 button | 5.06 | ✅ |
| teal-600 on teal-100 (secondary button as seen) | 4.31 | ❌ → text `teal-700` = **6.4** ✅ |
| reference placeholder `#9AA19E` on white | 2.64 | ❌ → `#6A726F` = **4.52** on input ✅ |
| secondary text `#6B7471` on input bg (as seen) | 4.41 | ❌ → `#5F6865` = **5.26** ✅ |
| status text as seen (green / blue / yellow) | 3.58 / 3.92 / 4.38 | ❌ → darkened, see table above ✅ |
| white icons on light sidebar teal | 3.26 | ✅ for icons (≥3:1); never put body text there |
| dark: text / text-2 / teal | 15.4 / 6.6 / 8.2 | ✅ |

### 2.2 Typography
- **Detected:** headings and wordmark in a geometric sans with round "a"/"e" → **Poppins Medium** *(est.)*; UI/body in a neo-grotesk → **Inter** *(est.)*.
- **Free alternatives:** headings → *Plus Jakarta Sans* or *Outfit*; body → *Manrope* or *DM Sans*.
- **Pairing rule:** Poppins 500 only for page titles, card titles, big numbers (h1–h4, metric). Inter for everything functional (tabs, tables, inputs, buttons). Never Poppins below 16px.
- **Habits:** Sentence case everywhere; UPPERCASE only for tiny step labels ("STEP 1. …", overline 11px +4% tracking). Counts are appended in lighter gray ("Reports **16**" → number in `text-secondary`). Numbers `tabular-nums`; dates `dd.mm.yyyy`.

| Token | Size / LH | Weight | Tracking | Family | Use |
|---|---|---|---|---|---|
| display | 48 / 1.1 | 500 | -0.02em | Poppins | auth hero |
| h1 | 36 / 1.15 | 500 | -0.015em | Poppins | page title, "Create account" |
| h2 | 28 / 1.2 | 500 | -0.01em | Poppins | detail title in content panel |
| h3 | 22 / 1.3 | 500 | -0.005em | Poppins | section ("Location") |
| h4 | 18 / 1.35 | 500 | 0 | Poppins | card title, overlay card |
| h5 / h6 | 16 · 14 / 1.4 | 600 | 0 | Inter | sub-sections, list titles |
| body-lg / md / sm | 16 · 14 · 13 | 400 | 0 | Inter | text |
| table | 13 / 1.4 | 500 | 0 | Inter | table cells (name column), header 12/500 |
| label | 12 / 1.3 | 400 | +0.005em | Inter | floating input labels, tile captions |
| caption | 12 / 1.35 | 400 | +0.01em | Inter | meta, IDs |
| overline | 11 / 1.3 | 500 | +0.04em | Inter | step labels (UPPERCASE) |
| button | 14 / 1 | 500 | 0 | Inter | buttons, tabs |
| metric | 28 / 1.15 | 500 | -0.01em | Poppins | KPI values (tabular) |

### 2.3 Spacing & layout
- **Base unit:** 4px. **Scale:** 0, 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80.
- **Shell:** header 64px · icon rail 64px · content gutter 24–32px · panels separated by 16–24px.
- **Grid:** 12 columns, 24px gutter, content max-width **1440px** (inside the rail). Common splits: **5/7 master-detail** (events), **8/4 main + side rail** (overview), **full-width table** (reports). Forms max 480px.
- **Breakpoints:** 640 / 768 / 1024 / 1280 / 1536. Under 1024 the rail becomes an off-canvas drawer and master-detail stacks.

### 2.4 Shape
| Token | px | Use |
|---|---|---|
| xs | 4 | checkbox |
| sm | 6 | status pills, tags *(est.)* |
| md | 8 | inputs, small buttons, table rows, calendar day cells |
| lg | 12 | buttons, icon buttons, sidebar active tile, info tiles |
| xl | 16 | cards, tab panel, overlay info card, map |
| 2xl | 20 | banner, large panels |
| 3xl | 28 | glass app frame, auth cards |
| full | 9999 | avatars, notification dot |

Differs from the mobile kit: **no pill buttons** — web controls are rounded-rectangles (8–12px).

### 2.5 Elevation
| Level | Value | Use |
|---|---|---|
| 0 | flat, tone only | tiles on panels, filled inputs |
| 1 | `0 1px 2px /.04` | segmented-control active item, social buttons |
| 2 | `0 2px 4px /.04, 0 8px 20px -6px /.06` | floating info card over banner, dropdowns |
| 3 | `0 4px 8px /.04, 0 16px 40px -12px /.08` | date-picker popover, modals |
| frame | `0 30px 80px -20px rgb(14 59 92/.15)` + inset 1.5px white 60% | glass app frame |

Borders are almost absent: separation = white panel on `#F7F9F8` bg, gray fills inside white panels, a single `#EDEFEE` divider under tabs and between master/detail.

### 2.6 Motion (inferred)
- fast 120ms (hover, checkbox) · base 180ms (tab underline slide, dropdown, row select) · slow 280ms (drawer, modal).
- Easing: standard `cubic-bezier(.2,0,0,1)`; exit `(.4,0,1,1)`.
- Hover: buttons darken one step; rows/tiles go `surface-muted`; icon buttons gain shadow-1. Press: no scale (enterprise feel) — darken only. Tab ink slides between tabs.

---

## 3. Iconography
- **Style:** outline, 1.5px stroke, rounded caps/joins, 20px in controls / 24px in rail, simple geometry. Rail icons are **filled/solid** white glyphs (dashboard, calendar, documents, building).
- **Closest set:** **Lucide** for outline (stroke matches, has search, filter-funnel, bell, external-link, map-pin, pencil, eye) + **Phosphor Fill** or **Material Symbols Rounded (filled)** for the rail. Alternative single set: **Phosphor** (Light/Regular for UI, Fill for rail).
- **Spacing:** icon→text 8px in buttons; 6px for inline icons after values ("4029 ↗", "Location ⌖"); icon-only buttons 40×40 with 20px glyph.
- **Colors:** default `text-secondary` · hover `text-primary` · active `primary` · on primary button white · rail inactive white 85% · rail active = teal glyph on a 40px white tile (radius 12).
- **Containers:** icon buttons = 40px `surface-muted` rounded-12 (filter, kebab, view toggle); social/login buttons = full-width `surface-muted` tiles with brand icon centered (brand logos are third-party — use official assets).

---

## 4. Component inventory

Global states: focus = `shadow-ring` (3px teal-400 40%) · disabled = 40% opacity · loading = inline spinner, width locked · error = 1px `status-error-fg` border + 12px helper text.

| Component | Variants & anatomy | Sizes | Notes / tokens |
|---|---|---|---|
| **Button** | primary (teal bg, white) · soft (teal-100 bg, teal-700 text) · neutral (surface-muted, text-primary) · ghost · danger. Optional trailing chevron for split/menu ("Create ⌄") | sm 32 · md 40 · lg 44 (auth full-width); radius 12 (lg) / 8 (sm) | hover → teal-700 / teal-200 |
| **Icon button** | neutral filled, ghost | 32 / 40 | radius 12 |
| **Search (global)** | filled `surface-muted` bar: scope select ("All ⌄", white inner chip) + input + trailing search icon | 44h, 400–480w | radius 12 |
| **Search (local)** | filled input + trailing icon; adjacent filter icon-button | 40h | radius 8 |
| **Text field (floating label)** | `surface-muted` fill, no border, label 12px on top, value 16px below, optional trailing action (eye) | 56h, padding 12/16 | radius 8; focus = white fill + ring |
| **Select** | text-field anatomy + chevron; status-select uses pill colors ("In development ⌄") | 32 / 40 / 56 | menu = surface, radius 12, shadow-2 |
| **Checkbox** | 18px, radius 4, border gray-300; checked teal fill + white check; indeterminate dash | — | header checkbox controls bulk select |
| **Radio / switch** | radio 18px; switch 36×20 teal when on | — | — |
| **Segmented control** | `surface-muted` track, active segment white + shadow-1 ("Project ops / Verification") | 36h | radius 10/8 |
| **Tabs (page)** | equal-width, 48h, text-secondary; active = teal text + 2px teal underline full tab width; divider below | — | `animate-tab-ink` |
| **Filter chips** | neutral pill `surface-muted` + count in lighter weight ("Ongoing 16") | 28h, radius 8 | selected = teal-100 / teal-700 |
| **Status pill** | see status table; optional dropdown chevron when editable | 22–28h, padding 6/10, radius 6 | 12–13px medium |
| **Info tile** | value (14–16 semibold) + optional trailing icon, caption label below; tiles on `surface-muted` or separated by vertical dividers inside a white card | 64–80h | radius 12 |
| **Overlay info card** | white card on banner, bottom-left, title h4 + pill row + info tiles row | ~440w | radius 16, shadow-2 |
| **Banner / page hero** | breadcrumb (icon + "Parent / Current") top-left, optional "Edit cover" ghost top-right; photo or hero-mist gradient; h1 + count | 160–280h | radius 20 |
| **Sidebar rail** | teal gradient, icons stacked 24px apart, active white tile, collapse toggle at bottom | 64w | — |
| **Top bar** | logo · global search · spacer · bell (with dot) · avatar 40 (radius 10) + name/role two-line + chevron | 64h | header gradient |
| **Data table** | header row `surface-muted` radius 8, 12px/500 labels + sort icon; rows 48–50h, radius 8, alternating none; selected rows `surface-selected`; first column = checkbox + 32px file thumbnail + bold name | — | hover row `surface-muted` |
| **List card (master list)** | white or `surface-muted` card: title 14/500 (2 lines), status pill, avatar stack (24px, -6px overlap), meta right (dates stacked in a gray pill, counter with icon); selected = 3px teal-400 left bar + white | radius 12 | — |
| **Date range picker** | popover radius 16, shadow-3; two months side by side; header month + chevron; weekday 12px gray; day cell 40×40 radius 8; selected start = **amber fill** `#F5A30B` *(est.)* with dark text, range = gray-100 | — | close icon top-right |
| **Map card** | teal-tinted map, radius 16, floating location chip top-left (white, radius 12), zoom control stack right, dark pin | — | use any map lib with a custom teal style |
| **Folder card (side rail)** | `surface-muted` card with stacked preview images peeking above, title + "123 files", chevron | radius 16 | hover shadow-2 |
| **Avatar** | radius 10 (user) / full (stack) | 24 / 32 / 40 | initials fallback on teal-100 |
| **Stepper (onboarding)** | thin 4px progress bar teal on gray-100, overline "STEP 1. …" | — | — |
| **Divider w/ text** | "Or continue with" centered between 1px lines | — | — |
| **Modal / toast / pagination / empty state** *(implied)* | modal = surface radius 20 shadow-3, 24–32 padding; toast = gray-900 bg white text radius 12; pagination = 32px neutral buttons, active teal; empty state = hero-mist illustration area + h4 + body + primary button | — | — |

---

## 5. Layout templates

1. **App shell** — canvas (sky gradient / landscape photo, optional) → glass frame (radius 28, 12px padding) → header 64 → rail 64 + content area (`bg`) with 24–32px padding.
2. **Detail with tabs (master-detail)** — banner 280 with breadcrumb + overlay info card → tabs panel (white, radius 16) → split 5/7: left = search + filter + create, segmented control, filter chips, list cards; right = h2 title, status row, 3 info tiles, contextual panel/popover.
3. **List / table page** — short banner (160) with breadcrumb + "Title Count" → white panel: toolbar (search, filter | soft button, primary split button) → data table → pagination.
4. **Overview** — tabs at top → 8/4 split: left = h1 title + pills + info tiles → sections ("Location" map card, "Emission/metrics" KPI card with chart) each with h3 + edit pencil; right = stacked folder cards.
5. **Auth / onboarding** — no shell; full-bleed landscape canvas; centered glass card (max 480, radius 28) with h1, floating-label fields, full-width primary, divider, 3 social tiles, footnote links (underlined text-secondary). Multi-step = stacked offset cards with stepper.
- **Image treatment:** wide landscape photos (≈ 5:1 banner, 16:9 tiles), radius = container radius, no dark scrims (use `hero-mist` or a white overlay card for text). Previews of documents are stacked/fanned with 8–12px offsets.
- **Whitespace rhythm:** 8 inside groups · 16 between controls · 24 between groups · 40 between sections.

---

## C. Do / Don't

**Do**
- Keep teal for: primary button, active tab, rail, checkbox — nothing else saturated.
- Use filled `surface-muted` controls with labels *inside*; no outlined inputs.
- Show status only through the pastel pill set, with the AA-fixed text colors.
- Put text on photos only inside a white overlay card or over `hero-mist`.
- Append counts in a lighter gray next to titles and chips.
- Use Poppins for titles/numbers ≥16px and Inter for every functional label.

**Don't**
- Use pill-shaped buttons (that's the mobile kit) or radii below 4px.
- Add borders around cards or inputs — use tone.
- Use teal-600 text on teal-100 (4.3:1) — use teal-700.
- Use more than one primary button per toolbar; pair it with a soft button.
- Put dark gradients/scrims on banners or color the canvas inside the frame.
- Use red/yellow for decoration — they are reserved for status.

---

## D. Generation prompt (paste into any AI UI tool)

```
Design a {SCREEN} for {PRODUCT}, desktop {1440}px, light mode, calm enterprise SaaS style.
Shell: 64px top bar (logo, filled search with "All" scope dropdown, bell with red dot, avatar + name/role), 64px left icon rail in teal gradient #12A08F→#0B7E73 with white solid icons and a white rounded-12 active tile. The app sits in a soft glass frame (radius 28, translucent white border, backdrop blur) over a sky/landscape canvas.
Colors: primary teal #0E7C74 (white text) only for primary buttons, active tab underline, checkboxes; soft button #DDF1EE with #0A5F59 text; page bg #F7F9F8, panels white, inputs/table headers/tiles #F4F5F4, selected rows #E3EBE9; text #1B2B2A and #5F6865. Status pills radius 6: green #DDF6DF/#256B2F, yellow #FCEFB4/#7A5B00, blue #E3F2FD/#1767AD, cyan #DFF5F8/#0A6670.
Type: Poppins 500 for titles and big numbers, Inter for UI (14px body, 13px tables, 12px labels). Sentence case; counts in lighter gray.
Shapes: buttons 12px radius, inputs 8px filled borderless with label inside (56px), cards 16px, banners 20px. Shadows minimal; separation by tone, not borders. Icons: Lucide outline 1.5px.
Wide landscape banner with breadcrumb and a white overlay info card; equal-width tabs with 2px teal underline. 4px grid, 24px gaps, WCAG AA.
```

---

## E. Example prompts for the booking marketplace (web)

**1. Partner dashboard — Bookings table**
> Design a **"Bookings" list page for the partner dashboard of a hotel & homestay booking marketplace**, using the prompt above. Short banner with breadcrumb "Dashboard / Bookings" and title "Bookings **248**" on the hero-mist gradient. White panel: toolbar with search + filter icon button on the left, soft "Export" and primary "New booking ⌄" on the right; filter chips "Upcoming 32 · Checked-in 6 · Completed 198 · Cancelled 12". Data table with checkbox, guest avatar + name, property thumbnail + name, dates (dd.mm.yyyy, tabular), guests, total price (right-aligned), status pills (Confirmed = green, Pending = yellow, In review = blue, Cancelled = red), and a kebab menu. Two selected rows tinted #E3EBE9. Pagination at the bottom.

**2. Property overview (host side)**
> Design a **property overview page for a host on a hotel & homestay booking marketplace**, using the prompt above. Full-width landscape photo banner of the property with breadcrumb "Properties / Pine Hill Villa" and "Edit cover" ghost button; white overlay card bottom-left with title, status pill "Listed ⌄", tag "Villa", ID caption, and 3 info tiles (Rating 9.2 · 2 bedrooms · Đà Lạt, Lâm Đồng with pin icon). Tabs: Overview, Rooms, Calendar, Bookings, Reviews, Payouts, Photos (Overview active). 8/4 split: left = "Location" map card (teal map style, location chip, zoom controls) and "Revenue" KPI card with two big Poppins numbers (This month / This year) and a small bar chart; right = folder cards "Photos 48 files", "Documents 12 files", "Reviews 230".

**3. Partner sign-up (onboarding)**
> Design a **two-step partner sign-up flow for a hotel & homestay booking marketplace**, using the prompt above, no app shell. Full-bleed landscape canvas (green hills, blue sky). Front glass card "Create account": floating-label filled fields (Full name, E-mail, Phone number, Password with eye toggle), "Remember me" checkbox, full-width primary "Create an account", "Or continue with" divider, 3 neutral social login tiles, footnote "Already have an account? Log in" and terms link. Behind it, offset card "STEP 1. PROPERTY INFORMATION" with a 4px teal progress bar, h3 "Property information", fields (Property name, Email, Phone), a "Location" map picker, and footer buttons soft "Skip" + primary "Continue".
