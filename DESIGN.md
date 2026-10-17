---
version: "alpha"
name: "GenBlocks"
description: "Editorial command center — a white editorial canvas, monumental display type, deep green and navy evidence bands, coral taxonomy and rule-driven lists, for a public registry of prompt-generated UI components and the verdicts of the judge that scored them."
colors:
  canvas: "#ffffff"
  stone: "#eeece7"
  stone-soft: "#f7f6f2"
  wash-green: "#edfce9"
  wash-blue: "#f1f5ff"
  ink: "#212121"
  ink-strong: "#17171c"
  ink-muted: "#6b6b7a"
  hairline: "#d9d9dd"
  hairline-soft: "#e5e7eb"
  primary: "#17171c"
  primary-foreground: "#ffffff"
  coral: "#ff7759"
  coral-soft: "#ffad9b"
  on-coral: "#17171c"
  link: "#1863dc"
  band: "#003c33"
  band-alt: "#071829"
  band-foreground: "#ffffff"
  focus: "#4c6ee6"
  verdict-pass: "#12684f"
  verdict-pass-soft: "#e2f1ea"
  verdict-retry: "#8a5c14"
  verdict-retry-soft: "#f6ecd6"
  verdict-fail: "#b30000"
  verdict-fail-soft: "#f8e3e3"

typography:
  display:
    fontFamily: Space Grotesk
    fontSize: 4.5rem
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "-0.03em"
  display-sm:
    fontFamily: Space Grotesk
    fontSize: 2.5rem
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  title:
    fontFamily: Hanken Grotesk
    fontSize: 1.5rem
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  subtitle:
    fontFamily: Hanken Grotesk
    fontSize: 1.125rem
    fontWeight: 400
    lineHeight: 1.4
  body:
    fontFamily: Hanken Grotesk
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.4
  micro:
    fontFamily: Hanken Grotesk
    fontSize: 0.75rem
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: Space Mono
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.02em"
  code:
    fontFamily: Space Mono
    fontSize: 0.8125rem
    fontWeight: 400
    lineHeight: 1.6
  score:
    fontFamily: Space Mono
    fontSize: 1.75rem
    fontWeight: 500
    lineHeight: 1
    fontFeature: "tnum"

rounded:
  none: "0px"
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "22px"
  xl: "30px"
  pill: "9999px"

spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
  4xl: "96px"

components:
  nav-bar:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    height: 68px
  hairline:
    backgroundColor: "{colors.hairline}"
    height: 1px
  divider-soft:
    backgroundColor: "{colors.hairline-soft}"
    height: 1px
  focus-outline:
    backgroundColor: "{colors.focus}"
    height: 2px
    width: 2px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: 24px
    height: 44px
  button-primary-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.primary-foreground}"
  button-outline:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-strong}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: 24px
    height: 44px
  field:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.sm}"
    padding: 12px
    height: 44px
  card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: 24px
  card-stone:
    backgroundColor: "{colors.stone}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: 24px
  dark-band:
    backgroundColor: "{colors.band}"
    textColor: "{colors.band-foreground}"
    rounded: "{rounded.none}"
    padding: 64px
  dark-band-navy:
    backgroundColor: "{colors.band-alt}"
    textColor: "{colors.band-foreground}"
    rounded: "{rounded.none}"
    padding: 64px
  wash-band:
    backgroundColor: "{colors.wash-green}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: 64px
  wash-band-alt:
    backgroundColor: "{colors.wash-blue}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: 64px
  console-panel:
    backgroundColor: "{colors.ink-strong}"
    textColor: "{colors.band-foreground}"
    typography: "{typography.code}"
    rounded: "{rounded.md}"
    padding: 16px
  code-block:
    backgroundColor: "{colors.stone-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.code}"
    rounded: "{rounded.sm}"
    padding: 16px
  category-chip:
    backgroundColor: "{colors.coral}"
    textColor: "{colors.on-coral}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: 8px
  category-chip-quiet:
    backgroundColor: "{colors.stone-soft}"
    textColor: "{colors.ink-strong}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: 8px
  highlight:
    backgroundColor: "{colors.coral-soft}"
    textColor: "{colors.on-coral}"
    typography: "{typography.body-sm}"
    padding: 2px
  link:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.link}"
    typography: "{typography.body-sm}"
    padding: 2px
  verdict-stamp:
    backgroundColor: "{colors.verdict-pass-soft}"
    textColor: "{colors.verdict-pass}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: 4px
  stamp-retry:
    backgroundColor: "{colors.verdict-retry-soft}"
    textColor: "{colors.verdict-retry}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: 4px
  stamp-fail:
    backgroundColor: "{colors.verdict-fail-soft}"
    textColor: "{colors.verdict-fail}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: 4px
  ledger-row:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: 16px
  ledger-row-alt:
    backgroundColor: "{colors.stone-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: 16px
  caption-text:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.micro}"
    padding: 4px
  dialog:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: 24px
---

## Overview

An editorial command center for a registry. The page opens on white, states its case in monumental display type, then steps back into restrained UI: thin rules, coral taxonomy, and lists that read like a research index rather than a wall of cards. Where the system needs weight, it does not add a shadow — it changes the surface to deep green or navy and lets the content go white.

GenBlocks is a public record of prompt-generated UI components and the verdicts a judge gave each attempt. The design borrows the register of a research publication: **taxonomy you can filter**, **evidence you can read**, and **numbers that line up**. It is a system with a point of view — monumental type, flat surfaces, one warm accent — not a neutral UI kit.

- Density: 4/10 — Airy in the marketing shell, dense only where the data is
- Variance: 5/10 — Centered statements alternating with full-width bands and rule-driven lists
- Motion: 3/10 — Quiet and functional; nothing bounces

## Colors

A white canvas, one near-black, and color that arrives with intent.

**Surfaces**

- **Canvas (#ffffff):** the default page. Most of the product lives here.
- **Stone (#eeece7):** warm secondary surface for product cards, quiet blocks and forms sitting on dark bands.
- **Stone Soft (#f7f6f2):** inset wells, alternate table rows, code backgrounds.
- **Wash Green (#edfce9) / Wash Blue (#f1f5ff):** pale section backdrops behind dark panels and media. They are the only place a large field of tint is allowed.

**Text and rules**

- **Ink (#212121):** default body text.
- **Ink Strong (#17171c):** headlines, the primary pill, the footer. The near-black is the brand anchor.
- **Ink Muted (#6b6b7a):** secondary text, metadata, captions. Measured AA on canvas. _(The upstream reference used a lighter grey that fails AA — this value is deliberately darker.)_
- **Hairline (#d9d9dd) / Hairline Soft (#e5e7eb):** rules and borders. Rules are structure in this system, not decoration.

**Accents**

- **Accent — Coral (#ff7759):** taxonomy only. Category chips, active filters and small warm markers. **Never text on canvas** (2.6:1). As a fill it takes `accent-foreground`, which is near-black, at 7:1.
- **Accent Soft (#ffad9b):** chip borders and pale warm fills.
- **Link (#1863dc):** editorial links and secondary emphasis. 5.4:1 on canvas.
- **Focus (#4c6ee6):** the keyboard ring, and nothing else.

**Bands**

- **Band Green (#003c33) / Band Alt Navy (#071829):** full-width evidence sections. The only dark surfaces besides the footer. Text inverts to `band-foreground`. Cards inside a band use translucent white surfaces, never stone.

**Verdict — functional, never brand**

- **Pass (#12684f) / Retry (#96651a) / Fail (#b30000)**, each with a soft tint for stamped backgrounds. These stay separate from the coral and the blue on purpose: a rejected component must never look like a filter chip or a link.

Rules of use: coral is taxonomy, blue is navigation, and neither is ever a surface. The verdict triad appears only where a verdict exists. If a screen has no verdict, that screen has no triad color.

**Dark mode** is a derived tonal inversion kept in `frontend/app/globals.css`: canvas becomes near-black, stone becomes `#17171c`, ink inverts, hairlines become translucent, and the primary pill inverts to white-on-dark. The bands stay green and navy; the accents lift one step to hold AA. It is derived from these tokens, not authored here.

## Typography

Three roles, and the split is the point — collapsing them into one sans is the fastest way to make this system look generic.

- **Space Grotesk** — display only, and sparingly. It carries the one monumental declaration a page is allowed. Tight, slightly mechanical, almost monospaced in spirit.
- **Hanken Grotesk** — body, UI and every heading that is not the display. Neutral, quiet, not the default system face.
- **Space Mono** — technical labels, metadata, scores, code. Uppercase for category and system markers.

Discipline:

- **Avoid heavy weights.** Display and body sit at 400, buttons and titles at 500. Hierarchy comes from size, tracking and surface contrast. If something needs to shout, make it bigger, not bolder.
- **Keep display type tight.** Negative tracking (−0.02 to −0.03em) and a line height of 1.0; hero copy should feel carved, not airy.
- **One oversized headline per page.** After the display, settle into 14–24px UI copy.
- **Uppercase mono labels** (14px, 0.02em) mark category and system states.
- **Tabular numerals everywhere a figure appears.** Scores, counts, dates.
- Headlines are never all caps. All caps belongs to mono labels.
- Line length caps at ~72ch.
- Fallbacks if the webfonts are unavailable: Space Grotesk → system grotesque; Hanken Grotesk → Inter, Arial; Space Mono → ui-monospace, Menlo.

## Layout

- **8px base.** Practical steps run 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96.
- **Max width 1200px**, centered, 24px side padding.
- **Two shells.** The marketing shell is centered and airy: statement, proof, product, CTA, separated by large intervals of empty space. The registry shell is a ruled index: a filter row, then rows or a 3-column grid.
- **Three-zone navigation:** mark left, links centered, action right.
- **Rows over cards.** For lists of components, attempts and research, use rule-separated rows with columns for category, score and date. Reach for a card only when an item is genuinely a self-contained object.
- **Whitespace is a trust signal.** Big empty intervals separate the claim, the proof and the action. Dense content appears only where the information architecture demands it.
- **Sections alternate surfaces**, not shadows: canvas → wash → band → canvas.

Responsive: nav collapses to the sheet below 768px; hero media stacks; grids go 3 → 2 → 1; form rows stack; research rows keep the rule but push metadata below the title; nothing overflows horizontally.

## Elevation & Depth

Flat, on purpose. Depth is surface alternation, contrast and thin borders — not shadow.

- **Flat:** canvas and band sections. No shadow, ever.
- **Bordered:** 1px hairline (or translucent white inside a band) for cards, forms, rows and wells.
- **Media lift:** a rounded media card over a contrasting section is the only "raised" object in the marketing shell. Its radius is 16–22px.
- Exactly **one shadow token** exists, for transient overlays (dialogs, menus, sheets, toasts): `0 8px 24px rgb(23 23 28 / 0.10)`. Nothing else casts.
- **No glow, no blur, no glass.** Nothing is translucent except white-on-band surfaces.
- Motion is functional and brief: 120–200ms, ease-out, opacity and transform only. No entrance animations, no hover lift, no scroll reveals.

## Shapes

Rounded, but not cute.

- **Radius scale:** 4px (utility, thumbnails) · 8px (inputs, small cards, chips-outline) · 16px (cards, dialogs) · 22px (signature media cards, toasts) · 30px (filters) · **pill** (primary and outline buttons, category chips).
- **Buttons are pills.** The primary CTA is a near-black pill; the secondary is either an outlined pill or an underlined text link. A squared button is wrong here.
- Media and major cards never go below 8px, and the signature media radius is 22px.
- Rules are 1px and visible. A boundary drawn with a rule beats a corner or a shadow.

## Components

- **Primary button.** Near-black pill (or white on a dark band), 14px label at weight 500, 24px horizontal padding, 44px tall. Hover darkens or lightens by one step; no shadow, no lift.
- **Secondary button.** Outlined pill: canvas fill, 1px hairline, near-black text. Ghost is text with a rule underline. One primary action per view.
- **Link.** `link` blue, underlined on hover. Never coral.
- **Input.** Canvas fill, 1px hairline, 8px radius, 44px tall. Label above is an uppercase mono label; helper and error text are mono. Focus is the `focus` ring — one treatment on every focusable element.
- **Category chip.** Pill. Active: coral fill with near-black text. Quiet: stone fill or a coral hairline with near-black text. Coral is for taxonomy, so a chip is the only place a large coral area is allowed.
- **Index card.** Canvas surface, 1px hairline, 16px radius, generous padding. Carries a mono accession mark, a title and a metadata row. In a grid these are 3-up on desktop.
- **Stone card.** Same geometry on the warm stone surface, for product and model summaries. Never used on a band.
- **Dark band.** Full-width green or navy section with white text. Cards inside it use translucent white surfaces and hairline borders. Used for evidence: the trace, the scores, the attempt history.
- **Console panel.** Near-black panel with mono text and small status chips — the running task, the trace, the code. This is the "agent console" of the product.
- **Verdict stamp.** Small 4px-radius chip, uppercase mono, hairline border in the verdict color over its soft tint. `PASS` / `RETRY` / `REJECTED`. Not a pill, not an icon.
- **Attempt ledger.** Rule-separated table: `№`, timestamp, score (tabular), verdict stamp. Rows are tall and open; alternate rows use stone-soft. This table is a first-class surface — it is the product's argument.
- **Score readout.** The judge's number in mono, tabular, right-aligned, over a thin hairline bar showing the value on the track. Data, not a donut.
- **Highlight.** Coral-soft marker behind near-black text, inline only. Flags the winning attempt or a key figure.
- **Research row.** The list form: title left, category chips centered, date right, separated by hairlines. No boxing.
- **Navigation / footer.** Canvas nav with a hairline beneath; near-black footer with white labels and muted links.

**States:** hover darkens or lightens one step; focus is the shared ring; pressed nudges 1px; disabled drops to 45% opacity with a not-allowed cursor. Every component defines all four.

## Do's and Don'ts

Do:

- Do start from the white canvas; introduce green or navy only as full-width bands.
- Do keep primary CTAs pill-shaped and near-black.
- Do use 16–22px radius on cards and media; keep inputs at 8px.
- Do use coral for taxonomy and small warm accents, never as the CTA system.
- Do let one monumental display line carry a page, then settle down.
- Do use rules and open rows instead of wrapping every item in a card.
- Do set every figure in tabular mono.
- Do check WCAG AA on every text/background pair, including coral and the verdict tints.

Don't:

- Don't put coral or blue text on the canvas — use near-black or `link` blue only.
- Don't turn coral or blue into broad decorative surfaces.
- Don't add drop shadows to cards. Depth is surface and rule.
- Don't use saturated gradients or glow as a UI background.
- Don't make every section card-based; unframed rows and open space are the default.
- Don't use squared buttons or radii below 4px.
- Don't replace the display / body / mono split with one generic sans.
- Don't reuse a brand accent for a verdict — pass, retry and fail stay functional.
- Don't use emoji as icons, or an icon set that carries its own color.
- Don't write "Elevate", "Seamless", "Unleash", "Next-Gen", or lorem ipsum — including in empty states.
- Don't fake depth, motion or polish to make an empty collection feel full.
