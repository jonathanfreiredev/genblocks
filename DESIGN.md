---
version: "alpha"
name: "GenBlocks"
description: "Overprint — a risograph-proof design system for a public registry of prompt-generated UI components and the verdicts of the judge that scored them."
colors:
  paper: "#F1ECDF"
  panel: "#FAF6EC"
  panel-sunken: "#E3DBC8"
  ink: "#17150F"
  on-ink: "#FAF6EC"
  ink-soft: "#4C4739"
  ink-faint: "#5F5A4C"
  rule: "#CFC7B4"
  rule-strong: "#A79E88"
  primary: "#CE2B6B"
  primary-hover: "#B0245C"
  on-primary: "#FFFFFF"
  secondary: "#16695B"
  accent: "#D9A020"
  focus: "#17150F"
  pass: "#2C6A3A"
  pass-soft: "#DEE7D8"
  retry: "#8A5A0C"
  retry-soft: "#EDE3CB"
  fail: "#A03028"
  fail-soft: "#EEDAD4"

typography:
  display:
    fontFamily: Bricolage Grotesque
    fontSize: 2.5rem
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  title:
    fontFamily: Bricolage Grotesque
    fontSize: 1.375rem
    fontWeight: 600
    lineHeight: 1.25
  body:
    fontFamily: Bricolage Grotesque
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.55
  body-sm:
    fontFamily: Bricolage Grotesque
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: Space Mono
    fontSize: 0.75rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.06em"
  meta:
    fontFamily: Space Mono
    fontSize: 0.8125rem
    fontWeight: 400
    lineHeight: 1.4
  code:
    fontFamily: Space Mono
    fontSize: 0.8125rem
    fontWeight: 400
    lineHeight: 1.6
  score:
    fontFamily: Space Mono
    fontSize: 1.75rem
    fontWeight: 700
    lineHeight: 1
    fontFeature: "tnum"

rounded:
  none: "0px"
  sm: "2px"
  md: "4px"
  lg: "6px"
  full: "9999px"

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
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    height: 56px
  hairline:
    backgroundColor: "{colors.rule}"
    height: 1px
  divider-strong:
    backgroundColor: "{colors.rule-strong}"
    height: 1px
  focus-outline:
    backgroundColor: "{colors.focus}"
    height: 2px
    width: 2px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.sm}"
    padding: 10px
    height: 40px
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.sm}"
    padding: 10px
    height: 40px
  field:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.sm}"
    padding: 10px
    height: 40px
  index-card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: 16px
  ink-block:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-ink}"
    rounded: "{rounded.md}"
    padding: 16px
  code-block:
    backgroundColor: "{colors.panel-sunken}"
    textColor: "{colors.ink}"
    typography: "{typography.code}"
    rounded: "{rounded.sm}"
    padding: 16px
  highlight:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    padding: 2px
  ledger-row:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    rounded: "{rounded.none}"
    padding: 12px
  ledger-row-alt:
    backgroundColor: "{colors.panel-sunken}"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    rounded: "{rounded.none}"
    padding: 12px
  link:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.secondary}"
    typography: "{typography.body-sm}"
    padding: 2px
  stamp-pass:
    backgroundColor: "{colors.pass-soft}"
    textColor: "{colors.pass}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 4px
  stamp-retry:
    backgroundColor: "{colors.retry-soft}"
    textColor: "{colors.retry}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 4px
  stamp-fail:
    backgroundColor: "{colors.fail-soft}"
    textColor: "{colors.fail}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 4px
  caption-text:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.meta}"
    padding: 4px
  meta-text:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-faint}"
    typography: "{typography.meta}"
    padding: 4px
  dialog:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: 24px
---

## Overview

A risograph proof sheet, not a landing page. The product shows *attempts* and the verdict a judge gave each one — which is exactly what a print proof is: flat spot inks laid down one pass at a time, and the registration between them deciding whether the sheet is good. The published component is the overprint.

So the interface borrows the register of a print studio and a museum accession record: bone paper, flat ink, visible rules, tabular figures, and a strict typographic hierarchy. Nothing glows, nothing blurs, nothing gradients. Where a lesser system reaches for a gradient, this one reaches for a second ink pass.

Color behaves like ink: opaque, countable, one pass at a time. It is not decoration. Each spot ink has exactly one surface where it belongs.

- Density: 7/10 — Compact, catalogued
- Variance: 2/10 — Columns, rules and index rails, not free composition
- Motion: 2/10 — Functional only; a proof does not perform

## Colors

Paper stock and one black plate carry the whole surface. Three spot inks carry the identity. A separate functional triad carries the verdict.

**Stock**

- **Paper (#F1ECDF):** the page ground — warm bone, never pure white.
- **Panel (#FAF6EC):** content surfaces and cards. The step from paper to panel replaces shadow as the way to lift a surface.
- **Panel Sunken (#E3DBC8):** wells, code blocks, alternate ledger rows. The only permitted depth cue besides rules.
- **Rule (#CFC7B4) / Rule Strong (#A79E88):** the workhorses. 1px rules are the system's edges, dividers and grid.
- **Ink (#17150F):** the black plate — all body text, and the fill of the primary *structural* elements. It also fills isolated **ink blocks** (the code and preview panes), where text is `on-ink`. It is also the source of the dark theme: dark mode is a *derived tonal inversion* of these tokens, kept in `frontend/app/globals.css`, not a second authored set. There the ink becomes the paper and the paper the ink, and the spot inks and verdict triad lift just enough to stay legible on the dark ground.
- **Ink Soft (#4C4739) / Ink Faint (#5F5A4C):** secondary and tertiary text. Both clear WCAG AA on paper and panel.

**Spot inks — each belongs to one surface**

- **Primary (#CE2B6B), magenta:** the action ink. Fills buttons, links, active states. It is a *fill*: magenta text on paper is only AA at large sizes, so on light surfaces it appears as a block of ink with `on-primary` (white) text — 5.0:1 — never as small body text.
- **Secondary (#16695B), verdigris:** the *on-paper* ink. It is the one spot that works as text on the light ground (5.6:1), so it carries links, inline references and quiet emphasis.
- **Accent (#D9A020), ochre:** the *on-dark* ink, and the highlighter. On the light ground it fails as text (2.0:1) and is used only as a marker behind ink text (7.8:1). On an ink block it becomes a first-class accent (7.8:1).

**Verdict triad — functional, never brand**

- **Pass (#2C6A3A) / Retry (#8A5A0C) / Fail (#A03028)**, each with a soft tint for stamped backgrounds. These are separate from the brand inks on purpose: a rejected component must never look like the magenta of the primary action. If a screen has no verdict, that screen has no triad color.

The rule of allocation: **one spot ink per screen.** Paper is the field; ink is the text; a single spot supplies the tension. Two spots on the same screen is a signal that the layout is doing two jobs.

## Typography

Two families. No third, ever.

- **Bricolage Grotesque** carries voice and reading: display, titles, body. A contemporary grotesque with real character and an optical-size axis — it reads as *designed*, never as a default system font, and it gives the proof a print-studio accent.
- **Space Mono** carries everything that is *data*: uppercase labels, metadata, scores, accession marks, code. Its typewriter lineage sits perfectly inside the print metaphor.

Discipline:

- **Uppercase Space Mono labels** (12px, 0.06em tracking) sit above every section and metadata group. They are the system's eyebrows and its clearest signature.
- **Tabular numerals everywhere a figure appears** — scores, attempt counts, dates, dimensions. `font-feature-settings: "tnum"`. Figures must align in columns or the ledger reads as prose.
- **Two weights per screen, maximum.** Bricolage runs 400 and 600; Space Mono has only 400 and 700. Hierarchy comes from size, tracking and position.
- Use Bricolage's optical size deliberately: large display settings tighter, small body settings open. Never fake it with tracking alone.
- Headlines cap at weight 600 and are never all caps. All caps is reserved for mono labels.
- Line length caps at ~72ch. Long-form reading is 16px/1.55.
- Fallbacks: Bricolage Grotesque → a neutral grotesque (Public Sans), then system sans. Space Mono → ui-monospace, Menlo.

## Layout

A 12-column grid with a visible structure, not a hidden one.

- **Max width 1280px**, centered, 24px side padding. On wide screens the record stays a document rather than stretching to fill.
- **The index rail.** List and gallery surfaces reserve a left column for accession marks (sequence numbers, slugs). The rail is structure, not decoration: it makes the registry scannable and gives every item a fixed address.
- **Rules over boxes.** Sections are separated by a 1px rule and major breaks by a double rule (1px, 8px gap, 1px). Cards are cells inside that structure, not floating tiles.
- **Density is deliberate.** Metadata rows run at 12px padding; a list of forty items should read as a ledger, not as forty hero cards.
- **Asymmetry over centering.** The item view is a two-pane split — specimen and evidence. The gallery leads with a filter rail, not a centered hero.
- Spacing follows the 4px scale: section rhythm 48–96px, within a component 4–16px.

Responsive: below 1024px the index rail collapses to an inline prefix; below 768px every multi-column region stacks, the metadata table becomes label/value pairs, and nothing may produce horizontal overflow.

## Elevation & Depth

Depth is expressed with **tone and rules**, not with shadow.

- Flat by default. A surface sits above another because its tone is lighter (panel over paper), separated by a 1px hairline.
- Exactly **one shadow token** exists, reserved for transient overlays (dialogs, menus, the task drawer): `0 1px 0 {rule}, 0 8px 24px rgba(23,21,15,0.12)`. A document lifting off a desk, once — not a motif.
- **No glow, no blur, no glass.** Nothing is translucent. An ink block is solid ink, not a frosted panel.
- Motion is mechanical and brief: 120–200ms, standard ease-out, opacity and transform only. State changes transition; content does not float in on scroll.
- A running operation is shown by an animated 1px rule or a mono caret — never a spinner with a halo.

## Shapes

Right angles, mostly.

- Base corner radius is **2px** (`sm`) on buttons, inputs and stamps. Cards use 4px (`md`). The largest is 6px (`lg`).
- **Full radius (9999px) is reserved** for status dots and avatars — never buttons, never badges.
- The primary separator is a **1px hairline**. If a boundary can be drawn with a rule, it is not drawn with a corner or a shadow.
- The shape language should read as cut paper and ruled ledger stock: precise, flat, a little institutional.

## Components

- **Primary button.** Magenta fill, white text, 2px radius, 40px tall, sentence case. Hover steps the ink darker; no lift, no shadow, no glow. One primary action per view.
- **Secondary button.** Panel fill, ink text, 1px rule border, same geometry. Ghost variant is text with a rule underline.
- **Link.** Verdigris text on the panel ground — the one spot ink safe as text on light. Underline on hover.
- **Input.** Panel fill, 1px rule border, 2px radius. Uppercase mono label above; helper and error text below in mono. Focus is a 2px ink outline at 2px offset — identical on every focusable element.
- **Index card.** A bordered cell (1px rule) on panel, 4px radius, with an accession mark in mono at the top, the specimen title, and a one-line meta row. Cards align to the grid and share baselines; they do not float or stagger.
- **Ink block.** Solid ink surface with `on-ink` text — the code and preview panes, and dark callouts. Ordered, never a full section band unless it is the only dark object on the screen.
- **Verdict stamp.** Uppercase mono, 1px border in the verdict color, soft tint fill, 2px radius. `PASS` / `RETRY` / `REJECTED`. A rubber stamp, not a pill, and it never carries an icon.
- **Attempt ledger.** A ruled table, one row per attempt: `№`, timestamp (mono), score (tabular), verdict stamp. Alternate rows use panel-sunken. This table is a first-class surface — it is the product's argument.
- **Score readout.** The judge's number in `score` (Space Mono, tabular, 1.75rem), right-aligned, with a thin hairline bar under it showing the value on the 0–100 track. Data — not a donut, not a ring, not a gauge.
- **Highlight.** An ochre marker behind ink text, used to flag the winning attempt or a key figure. Inline, never a full-width band.
- **Code block.** Panel-sunken, Space Mono, 1px rule, no window chrome, no rainbow syntax — a single muted keyword tint at most.
- **Tabs.** Underline tabs carried by the hairline: active is ink with a 2px ink underline; inactive is ink-soft with no chrome.
- **Navigation.** Paper background, 1px rule beneath, mono labels for utility items. Active state is an ink underline, never a filled pill.
- **Dialog.** Panel surface, 4px radius, the single shadow token.

## Do's and Don'ts

Do:

- Do let each spot ink belong to its surface: magenta as fill, verdigris as on-paper text, ochre as marker and on-ink accent.
- Do keep one spot ink per screen. Paper and ink carry everything else.
- Do use white text on magenta and on verdigris fills; use ink text on ochre.
- Do set every number in tabular Space Mono, aligned in columns.
- Do surface the score and the attempt history on the item itself — the ledger is the point.
- Do keep radii at 2–6px and edges hairline-thin.
- Do verify WCAG AA on every text/background pair, including the verdict tints.

Don't:

- Don't put magenta or ochre as small text on the paper ground — they fail AA there.
- Don't reuse a brand ink for a verdict. Pass/retry/fail stay functional.
- Don't show magenta, verdigris and ochre together on one screen.
- Don't use gradients, glassmorphism, backdrop blur, or glow. Anywhere.
- Don't use drop shadows for depth that a rule or a tone step can do.
- Don't use pill shapes for buttons or badges — full radius belongs to status dots and avatars only.
- Don't center a hero, don't stagger cards, don't float content in on scroll.
- Don't use more than two typefaces or more than two weights per screen.
- Don't use emoji as icons, and don't ship an icon set that carries its own color.
- Don't write "Elevate", "Seamless", "Unleash", "Next-Gen", or lorem ipsum — including in empty states and demos.
