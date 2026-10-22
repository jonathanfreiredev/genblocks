---
version: "1.0"
name: "GenBlocks"
description: "A shadcn/ui shell around a wall of generated work: a quiet neutral system, one thin header, a full-height sidebar, square preview tiles, and an item page that puts the picture first and the evidence beside it."
colors:
  background: "#ffffff"
  foreground: "#0a0a0a"
  card: "#ffffff"
  card-foreground: "#0a0a0a"
  popover: "#ffffff"
  popover-foreground: "#0a0a0a"
  primary: "#171717"
  primary-foreground: "#fafafa"
  secondary: "#f5f5f5"
  secondary-foreground: "#171717"
  muted: "#f5f5f5"
  muted-foreground: "#737373"
  accent: "#f5f5f5"
  accent-foreground: "#171717"
  destructive: "#e7000b"
  border: "#e5e5e5"
  input: "#e5e5e5"
  ring: "#a3a3a3"
  sidebar: "#fafafa"
  sidebar-foreground: "#0a0a0a"
  sidebar-primary: "#171717"
  sidebar-primary-foreground: "#fafafa"
  sidebar-accent: "#f5f5f5"
  sidebar-accent-foreground: "#171717"
  sidebar-border: "#e5e5e5"
  sidebar-ring: "#a3a3a3"
  pass: "#047857"
  pass-soft: "rgb(16 185 129 / 0.10)"
  fail: "#e7000b"
  fail-soft: "rgb(231 0 11 / 0.10)"
  dark-background: "#0a0a0a"
  dark-foreground: "#fafafa"
  dark-card: "#171717"
  dark-muted: "#262626"
  dark-muted-foreground: "#a3a3a3"
  dark-border: "rgb(255 255 255 / 0.10)"
  dark-sidebar: "#171717"

typography:
  sans: Geist
  mono: Geist Mono
  page-title:
    fontFamily: Geist
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  section-label:
    fontFamily: Geist
    fontSize: 0.75rem
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.05em"
    textTransform: uppercase
  body:
    fontFamily: Geist
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  row-label:
    fontFamily: Geist
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  row-value:
    fontFamily: Geist
    fontSize: 0.875rem
    fontWeight: 500
    lineHeight: 1.5
  small:
    fontFamily: Geist
    fontSize: 0.75rem
    fontWeight: 400
    lineHeight: 1.4
  code:
    fontFamily: Geist Mono
    fontSize: 0.75rem
    fontWeight: 400
    lineHeight: 1.6
  score:
    fontFamily: Geist
    fontSize: 1.125rem
    fontWeight: 600
    lineHeight: 1
    fontFeature: "tnum"

rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "14px"
  2xl: "18px"
  3xl: "22px"
  4xl: "26px"

spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
  3xl: "40px"

components:
  header:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    height: 56px
    border: "1px {colors.border}"
  sidebar:
    backgroundColor: "{colors.sidebar}"
    textColor: "{colors.sidebar-foreground}"
    width: 256px
    width-collapsed: 48px
    width-mobile: 288px
  sidebar-button:
    textColor: "{colors.sidebar-accent-foreground}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    height: 32px
    padding: 8px
  breadcrumb-band:
    backgroundColor: "color-mix(in oklab, {colors.muted} 40%, transparent)"
    textColor: "{colors.muted-foreground}"
    height: 36px
    padding: 8px 12px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    height: 32px
    padding: 10px
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    border: "1px {colors.border}"
    rounded: "{rounded.lg}"
    height: 32px
  input:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    border: "1px {colors.input}"
    rounded: "{rounded.lg}"
    height: 32px
    padding: 10px
  search-button:
    backgroundColor: "{colors.background}"
    textColor: "{colors.muted-foreground}"
    border: "1px {colors.border}"
    rounded: "{rounded.lg}"
    height: 32px
    width: 224px
  grid-tile:
    backgroundColor: "{colors.background}"
    border: "1px {colors.border}"
    rounded: "{rounded.xl}"
    padding: 8px
  grid-tile-hover:
    backgroundColor: "color-mix(in oklab, {colors.muted} 30%, transparent)"
    translateY: -2px
  item-frame:
    backgroundColor: "color-mix(in oklab, {colors.muted} 20%, transparent)"
    border: "1px {colors.border}"
    rounded: "{rounded.xl}"
    padding: 8px
    maxHeight: 58svh
  code-block:
    backgroundColor: "color-mix(in oklab, {colors.muted} 20%, transparent)"
    textColor: "{colors.foreground}"
    typography: "{typography.code}"
    rounded: "{rounded.lg}"
    lineNumbers: true
  file-rail:
    backgroundColor: "color-mix(in oklab, {colors.muted} 30%, transparent)"
    textColor: "{colors.muted-foreground}"
    rounded: "{rounded.md}"
    width: 176px
    width-collapsed: 40px
  evidence-panel:
    backgroundColor: "{colors.card}"
    textColor: "{colors.card-foreground}"
    border: "1px {colors.border}"
    rounded: "{rounded.xl}"
    padding: 16px
    width: 320px
  score-readout:
    textColor: "{colors.foreground}"
    typography: "{typography.score}"
    trackColor: "{colors.muted}"
    trackWidth: 56px
  verdict-pass:
    backgroundColor: "{colors.pass-soft}"
    textColor: "{colors.pass}"
    rounded: "{rounded.md}"
    padding: "2px 8px"
  verdict-fail:
    backgroundColor: "{colors.fail-soft}"
    textColor: "{colors.fail}"
    rounded: "{rounded.md}"
    padding: "2px 8px"
  avatar-button:
    backgroundColor: "{colors.background}"
    border: "1px {colors.border}"
    rounded: "9999px"
    size: 36px
  assistant-dialog:
    backgroundColor: "{colors.popover}"
    textColor: "{colors.popover-foreground}"
    border: "1px {colors.border}"
    rounded: "{rounded.xl}"
    width: 768px
    height: 760px
  user-bubble:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.xl}"
    padding: "8px 12px"
  assistant-composer:
    backgroundColor: "{colors.background}"
    border: "1px {colors.input}"
    rounded: "{rounded.xl}"
    padding: 12px
---

## Overview

GenBlocks is a public wall of UI blocks and stock images, each one generated from a prompt and scored by a judge that did not write it. The interface exists to get out of the way of the work: the pictures are the argument, and the evidence is one click behind them.

The system is **shadcn/ui on the neutral base theme**. It is deliberately quiet: white and near-black, one thin header, a full-height sidebar, square previews, and a single accent that belongs to the artifacts rather than to the chrome. There is no editorial display face, no coral taxonomy, no green or navy bands, no monospaced uppercase labels everywhere, and no pill buttons. Those belonged to the previous system and are retired.

**This document is the source of truth for visual decisions.** `app/globals.css` implements its tokens and `components/ui/` implements its primitives. When a token or a component changes, change this document first, then update the code. If they disagree, fix the drift in the same change rather than treating either side as the winner by default.

## Foundations

### Color

All color is semantic. Components use `bg-background`, `text-foreground`, `text-muted-foreground`, `border-border`, `bg-muted`, `bg-card`, `bg-sidebar` and their siblings; they never use a raw hex, a named Tailwind palette color, or a manual `dark:` override.

- **Background / foreground** — white and near-black in light, near-black and near-white in dark.
- **Primary** — near-black in light (the one filled action), near-white in dark.
- **Muted** — the quiet surface for insets, file rails, code backgrounds and alternate rows.
- **Muted foreground** — metadata, labels, captions and the author under a tile.
- **Border / input** — one hairline for every boundary.
- **Sidebar** — a slightly off-white surface in light (`#fafafa`), a step above the page in dark (`#171717`).
- **Destructive** — failures, rejected verdicts and destructive actions. Nothing else.
- **Pass** — a small emerald pair used only for a passing verdict. It is functional, not brand.
- **Charts** — available from the theme, not used by the shell today.

Dark mode is a full tonal inversion driven by the `.dark` class. Every surface is defined twice; a component that needs a different dark value is a component that should use a token.

### Typography

Two faces, both Geist:

- **Geist** — everything that is read: titles, body, labels, buttons.
- **Geist Mono** — code, file paths, install lines and any figure that should line up.

The scale is short and intentional:

- **Page title** — 24px, semibold, tight tracking. One per page: visible on an item, `sr-only` on the wall and the task list.
- **Section label** — 12px, medium, uppercase, wide tracking, muted. Used for `JUDGE`, `HARNESS`, `Browse`, `Categories`, `Files`.
- **Body / row text** — 14px. Labels are muted and regular; values are foreground and medium.
- **Small** — 12px, for status words, counts and secondary hints.
- **Code** — 12px mono with 1.6 line height.
- **Score** — 18px semibold, tabular numerals.

Do not introduce a display face, a third family, or a second type scale. Headings are not all caps; all caps belongs to the 12px section labels only.

### Radius

`--radius: 0.625rem` (10px). The scale derives from it:

- `sm` 6px — tiny controls, inline tags.
- `md` 8px — menu items, file buttons, badges.
- `lg` 10px — buttons, inputs, the search field.
- `xl` 14px — cards, dialogs, the item frame, the evidence panel.
- `2xl` 18px — larger surfaces.
- `3xl` 22px, `4xl` 26px — reserved; not used by the shell.

Buttons and inputs are `rounded-lg`, not pills. The account avatar and the chat's 32px message avatars are the circles; nothing else is.

### Spacing and layout

A 4px base. The practical steps are 4, 8, 12, 16, 24, 32 and 40.

- **Content padding** — 12px on a phone, 16px on a laptop.
- **Grid gap** — 12px.
- **Card padding** — 16px.
- **Section gap** — 24px in the evidence panel, 16–24px between the parts of an item page.
- **Line length** — body copy stays under ~72ch; the item description is short by construction.

### Elevation and motion

Flat by default. Borders and muted surfaces do the separating; shadows belong to overlays only, as shadcn ships them.

Motion is functional and brief:

- Hovering a tile lifts it 2px and fades in the author; 150–200ms, ease-out.
- Tabs, menus and dialogs use shadcn's own transitions.
- Nothing bounces, nothing animates on entry, nothing reveals on scroll.
- New motion should respect `prefers-reduced-motion`.

## The shell

### Sidebar — laptop

A real shadcn `Sidebar` (`collapsible="icon"`), full viewport height, its content scrollable.

- **Width** 16rem expanded, 3rem collapsed.
- **Header** 56px tall, matching the app header: the mark and `GenBlocks` on the left, the collapse button on the right.
- Collapsed, the header stacks the mark over the button and the width falls to 48px.
- **Ask AI** is the first item under the header: a full-width primary button that opens the one assistant. Collapsed, it is a single sparkle icon with an accessible name.
- **Browse** holds Blocks and Images, each with an icon and an active state.
- **Agents** holds `Connect`, the page that tells a client how to reach the MCP
  server. It is not part of the taxonomy, so it sits above `Categories`.
- **Operate** appears only for an operator: Items, Reports and Users. It is a
  separate group and never mixes with the public navigation.
- **Categories** lists `All` and the level-2 types of the section on screen. The list is long by nature; it scrolls.
- **Footer** holds the theme toggle and a quiet Source link. Collapsed, only the toggle remains.

The sidebar is the only navigation. There is no home page and no kind switch in the page body.

### Header — laptop

A 56px strip that starts where the sidebar ends and spans the rest of the width.

- **Right side**: the search affordance, then the account.
- Logged out: `Log in` (ghost) and `Sign up` (secondary).
- Logged in: the avatar menu, unchanged.
- **Search** looks like an input but is a button: a magnifier and the lowercase word `search`, 224px wide, `rounded-lg`. It opens a dialog with the real field.

The header is sticky and slightly translucent (`bg-background/80` plus backdrop blur) so the wall keeps moving underneath it.

### Header — phone

The header spans the full width and is a three-part strip:

- **Left**: a burger that opens the navigation.
- **Center**: the mark and `GenBlocks`, absolutely centered so neither side control can push it off the middle.
- **Right**: a magnifier button, then `Log in` when logged out or the avatar when logged in. No sign-up on the phone header.

There is no search field in the mobile header: the magnifier opens the same dialog.

### Sidebar — phone

The same sidebar becomes a **full-height** sheet from the very top of the screen (`top: 0`, `100dvh`), covering the header while it is open. It has its own header row: `MENU` on the left and a close button on the right. Links close the sheet when tapped. The footer keeps the theme toggle. The assistant is **not** in this sheet on a phone; it is the floating button below.

### Breadcrumb band

A muted strip directly under the header (`bg-muted/40`, 1px bottom border, 8px by 12px padding).

- `/blocks` → `Blocks`; `/blocks/hero` → `Blocks / Hero`.
- `/blocks/<id>` → `Blocks` only; the page's h1 names the item, and repeating it in the band would be the same word twice.
- `/images` → `Images`; `/tasks` → `Your tasks`; a task detail appends the short id; `/profile` → `Profile`; `/mcp` → `Connect an agent`.

There is no `Home` crumb. The section is the root.

## The assistant

The vault has one conversation. On a laptop it opens from **Ask AI** in the sidebar; on a phone it opens from a floating primary button at the bottom-left, above the safe area and outside the navigation sheet. It answers
questions about blocks and pictures, and it can prepare a brief for a task. A
brief is only queued when the person confirms it. The surface is the shadcn chat
set, not a hand-rolled scroll box.

- **Entry** — one `AgentChatProvider` owns the transcript and the dialog; the
  sidebar button and the phone's floating button are two triggers for the same
  conversation, not two dialogs. The phone button is `position: fixed`, bottom-left,
  offset by `env(safe-area-inset-bottom)`, and the mobile sheet hides its copy.
- **Frame** — `Dialog` at `sm:max-w-3xl`, 760px tall on a laptop, full height on
  a phone. The header is the product mark (`app/icon.png`), the title `Ask AI`,
  one line of scope, a new-chat button and the close button.
- **Welcome** — centered when there are no turns: the product mark, `Ask about
  anything in the vault`, one supporting line, and four prompt chips (overview,
  find a block, look at pictures, build). A visitor sees the same welcome and a
  sign-in footer instead of the composer.
- **Transcript** — `MessageScroller` with `Message`, `MessageAvatar`,
  `MessageHeader` and `Bubble`. The user's turn is right-aligned in a primary
  bubble; the assistant's is left, full width, in a ghost bubble. Every turn has
  a small name and a 32px circular avatar; the assistant's is a sparkle, the
  user's is their initials.
- **Activity** — a `Trace` above the assistant's words. Each tool is a
  `TraceLine`: `Spinner` plus a running phrase while it works, `Check` plus the
  past-tense phrase when it is done. The labels are human (`Searching the
  blocks`, `Preparing the brief`), never the tool's Python name. While nothing
  has happened yet, a `Marker` with a spinner says `Thinking…`.
- **Answers** — streamed as Markdown and rendered by Streamdown under a ghost
  bubble: bold names, short lists, links and fenced code arrive as themselves,
  not as asterisks. It is streaming-aware, so an unfinished emphasis or fence
  stays readable while the answer arrives. The user's own turn stays plain text.
  Streamdown's stylesheet is imported in the root layout and its classes are
  scanned from `node_modules/streamdown/dist` in `globals.css`.
- **Suggestions** — the cards the tools found belong to the turn that found them,
  in a horizontal rail under the answer. The tools only offer a result close
  enough to be the thing asked for; a weak nearest is not a card. Each card
  opens its item page (by slug) and closes the dialog.
- **Proposal card** — a brief the agent prepared is shown as a bordered card
  inside the turn: `Ready to build`, the brief, and one primary `Queue block`
  button. The model cannot press it. The button is the only path from the
  conversation to a task; after it succeeds the card is replaced by the task card.
- **Task card** — when the person confirms a brief and a task is queued, it becomes
  a bordered card inside the same turn: heading (`Building the block`,
  `Block published`, `The build stopped`, `Already in the registry`), the brief, a
  status badge, one `TraceLine` per step with its elapsed time, and `Follow the
  task` / `Open the block`. The card polls while the task is live; the composer
  stays available, because the chat does not end when a build starts.
- **Composer** — `InputGroup` with `InputGroupTextarea` (two rows, capped), a
  send button (`ArrowUp`), a stop button while a turn is streaming, and the hint
  `Enter to send · Shift+Enter for a new line`. Enter sends; Shift+Enter breaks
  the line; IME composition is respected.
- **New chat** — the labelled button in the header, next to the close. It aborts
  the turn in flight, clears the transcript and the task cards, and rotates the
  thread id. The label is the affordance; a bare plus next to the close was not.
- **Continuity** — the thread id lives in `localStorage` under
  `genblocks-chat-thread`. It is the only thing kept between visits: the
  transcript is React state, and the agent's memory is on the server. Closing the
  dialog keeps the conversation; reloading the page starts a fresh transcript
  with the same thread.
- **Type** — 14px for messages, trace lines and task steps; 12px for the section
  label `ALREADY IN THE REGISTRY` and status badges; 18px only for scores. The
  names above each turn are 12px muted.

Do not build a second chat surface with raw `div`s: the scroller, message, bubble,
marker and trace primitives already own alignment, scroll following, the
jump-to-latest button and the streaming states.

## The wall

The gallery is a wall of pictures, not a list of records.

- **Full width** minus 12–16px of padding. No max-width, no centred column.
- **Grid**: 2 columns on a phone, 3 on a small tablet, 4 on a laptop, 5 on a wide screen; 12px gap.
- **Cell**: a square (`aspect-square`) `rounded-xl` frame with a 1px border and 8px of padding. The thumbnail fills its box and is cropped to it (`object-cover`), so the wall reads as one surface. It is a separate render at phone width (390px), not the judge's desktop screenshot: at card width a block is compact and nearly square, so the crop does not cut the composition. The item page shows the uncropped desktop artifact.
- **Nothing on the tile** except the picture. On hover the picture lifts 2px, the frame takes a faint muted wash, and the maker's name (`author`, or `GenBlocks` when nobody claimed it) fades in centred at the bottom.
- **No title, slug, date or category** on the wall. The accessible name is the item's title; the visual text is only the author on hover.
- **Above the grid**: one small line with the count (`7 blocks`) and, when searching, `for “query”` plus a `Clear search` link. No section title and no description.
- **Pagination**: two outline buttons and a small `Page x of y`, below the grid.

Loading and missing assets are honest: the `AssetPlate` shows a muted frame with `Awaiting asset` and what is known (model or dimensions) rather than a broken image.

## The item page

Opening a tile is a navigation, not a dialog: `/blocks/<slug>` or `/images/<slug>`.

Top to bottom:

1. **The render** — inside a muted, bordered frame with 8–12px padding. No tab, no `Render` label, no controls. The frame is capped at `58svh` (images at `60svh`) and centred; the whole artifact is contained, never cropped. A block's title is not above it.
   - **A block runs.** The frame is a sandboxed iframe on the built page, sized by the page itself up to the `58svh` cap (past that it scrolls). A visitor can press, type, submit a form and watch an animation; nothing they do leaves the page. There is no `live`/`still` switch and no reload button — the block is simply live.
   - **One line of honesty** sits under the frame, 12px muted: `Interactive preview, sandboxed: nothing you type leaves this page.` It is the only copy the render gets.
   - An image keeps the static render; so do the gallery, the task result and the evidence panel.
2. **Two columns** below, aligned at the top:
   - **Left, flexible**: the `code` and `prompt` tabs for a block; the prompt card for an image.
   - **Right, 20rem (22rem on a wide screen)**: the evidence.

### Code tab

- The project as it was stored: the file rail on the left (a strip above the code on a phone), always visible, always collapsible. It starts open.
- The rail lists every path, highlights the current one and truncates long paths. On a phone it scrolls horizontally.
- Collapsing it leaves a 40px rail with the reopen button; the code takes the width.
- The code itself is shadcn's `CodeBlock`: a bordered, `rounded-lg`, monospaced surface with line numbers, horizontal scroll and a copy action that appears on hover, focus or touch. Inside the tab card it is flush (`rounded-none border-0`) with a faint muted background.
- The lines are syntax-highlighted by shiki through shadcn's `useHighlightedCode` hook: `github-light` and `github-dark`, chosen from the file extension (`.tsx`, `.ts`, `.js`, `.json`, `.css`, `.py`, `.sh`, `.sql`, `.md`, `.yml`). An unknown extension stays plain; the highlighter loads the grammar on first use rather than in the first paint.
- An item is addressed by its slug, not its id: `/blocks/proof-sheet-hero`, `/images/stone-harbour`. An old id link redirects to the slug; the page's canonical URL and its `generateMetadata` title/description use the slug.
- A line with a package to install sits under the code as a mono command with its own copy button. React and React DOM are implied and never listed.
- The `code` and `prompt` labels are lowercase.

### Prompt tab

The delivery prompt as body copy, with a copy button in the tab header. The image item uses the same shape as a single prompt card.

### Evidence column

A bordered `rounded-xl` card, 16px padding, 24px between groups. The order is fixed:

1. **Title** on a block: the page h1, 16px semibold, at the top of the column. The
   render is first and the prompt tab already carries the brief, so repeating
   either above the picture would be a second copy. An image keeps its category
   above the render and has no title here.
2. **Category, date, model, source and trace** as a definition list. Labels 14px muted; values 14px medium and truncated. The source reads `AI-generated` when the artifact carries C2PA provenance and `Not recorded` otherwise. The trace is a link when a Langfuse host is configured and `Not recorded` otherwise.
3. **Judge** — the score rows. Label 14px muted on the left, score on the right: 18px semibold tabular numerals over a 56px, 4px-high muted track. One row per rubric dimension.
4. **Harness** — one row per check, label 14px, state 12px (`ok` muted, `failed` destructive). A failed check may carry the sandbox's own sentence underneath. Accessibility violations follow as 14px lines with id, impact and node count.

The panel narrows rather than widening the page: never give the evidence more than 22rem. On a phone it stacks under the tabs.

### Block and image differences

- A block has a title, a project, a delivery prompt, an attempt and harness checks. Its title is the h1 at the top of the evidence column; the render is first on the page.
- An image has no code and no separate prompt section; its category is the h1 above the render, the prompt is the left card, and the evidence keeps the same order without a harness or title.

## Tasks and account

- **Tasks list**: the visible heading is gone; an `sr-only` h1 keeps the page named. The brief, status badge and timestamp form a rule-separated list. The empty state offers the generator.
- **Task detail**: unchanged in structure. The brief is the heading; status, queue time, finish time and trace sit in a bordered definition row; the checklist is a bordered table; the result is the render plus the evidence panel with its verdict and model.
- **Profile and auth**: shadcn cards and fields on the same neutral tokens. Auth pages have no shell chrome; they are centred on the canvas.
- **Connect an agent**: a short guide, not a settings form. An endpoint card states the mode (`Local` or `Production`) and carries the URL with a copy button; three numbered parts follow — add the server (one tab per client), approve the first call, ask for something. The endpoint comes from the request host locally and from `MCP_URL` on a deployment, so no command ever points at the wrong server.

## Components

- **Button** — shadcn's default. Primary is near-black, outline is a hairline on the canvas, secondary is muted, ghost is text with a hover wash. Heights 24/28/32/36px by size; `rounded-lg`; icons via `data-icon` and no manual sizing.
- **Input / Textarea** — 32px high, transparent, 1px input border, `rounded-lg`, a 3px ring on focus.
- **InputGroup** — the search field: a magnifier addon, the input, and an inline `Search` button.
- **Search dialog** — a title, one sentence of scope, the input group. Submit on Enter. It searches the section on screen and keeps the current category.
- **Tabs** — shadcn's line variant. Triggers live inside a `TabsList`; the active line is the foreground.
- **CodeBlock** — shadcn's component: header/actions/content/footer, line numbers, copy button, horizontal scroll, and shiki highlighting through `useHighlightedCode`.
- **Dialog / Sheet / Dropdown** — shadcn defaults. Overlays are the only place a shadow appears. Every dialog and sheet has a title (visually hidden when needed).
- **Badge** — status words and verdicts. `secondary` for running, `destructive` for failed, `outline` for queued or done; verdicts use the functional emerald/destructive pairs.
- **Sidebar** — the real shadcn sidebar with menu buttons, group labels, tooltips in icon mode and a sheet on mobile.
- **Empty / Alert** — the shadcn primitives, not bespoke markup.
- **Chat** — `MessageScroller` + `Message` + `Bubble` + `Marker` + `Trace`; the assistant surface is a composition of these, not a new widget.
- **ScoreReadout** — the product's one custom data component: 18px semibold tabular number over a 56px track. No donuts, rings or gauges.
- **AssetPlate** — the product's one media component: a Cloudinary id, a transform width, `object-cover` in the gallery, `object-contain` on the item page, and an honest muted fallback.

## Do's and Don'ts

Do:

- Do start from `background`, `foreground`, `muted`, `border`, `card` and `sidebar`; use the semantic token that names the role.
- Do reach for a shadcn component before writing markup. Add it with `pnpm dlx shadcn@latest add <component>`.
- Do keep the shell thin: 56px header, 16rem sidebar, 12px content padding.
- Do keep the wall textless until hover, and keep the author the only label.
- Do keep the evidence column narrow and its type scale consistent: 12px section labels, 14px labels and values, 18px scores.
- Do keep the assistant's activity visible while it works, and keep the composer after a task is queued.
- Do persist the conversation id, not the transcript.
- Do keep the file rail visible and collapsible, with the file list on the left on a laptop and above the code on a phone.
- Do cap renders at 58–60svh and contain them.
- Do use `gap-*`, `size-*`, `truncate`, `cn()` and `data-icon`.
- Do give every icon-only button an `aria-label`.
- Do keep one h1 per page; use `sr-only` where the visible title was removed on purpose.
- Do respect dark mode through tokens and check both themes.

Don't:

- Don't use the old `type-*` utilities, `text-ink*`, `bg-panel*`, `border-rule`, coral, bands or pill buttons. They are gone.
- Don't use raw hex, named palette colors or manual `dark:` overrides in components.
- Don't put a section title, a description, a count hero or a breadcrumb inside the page body; the band and the sidebar already said it.
- Don't put text on a gallery tile other than the author on hover.
- Don't make the render taller than the viewport or crop the artifact to fill a square.
- Don't make the evidence panel wider than 22rem or let its labels and values drift to different sizes.
- Don't hide the file rail; collapse it.
- Don't add shadows to cards, gradients, glass or glow. Only overlays lift.
- Don't animate entrances, bounces or scroll reveals. Hover lifts and fades are enough.
- Don't uppercase body copy; reserve uppercase for the 12px section labels.
- Don't build a custom dialog, menu, tab or field when shadcn already ships one.
- Don't hand-roll chat bubbles, auto-scroll or "thinking" states; compose the chat primitives.
- Don't clear the conversation when the dialog closes, and don't store the transcript beside the thread id.

## Implementation notes

- Tokens live in `frontend/app/globals.css`: the neutral oklch values, the derived radius scale and `--header-height: 3.5rem`.
- Components live in `frontend/components/ui/` and are added with the shadcn CLI. `components.json` pins `base-nova`, neutral, Geist and Lucide.
- The shell lives in `components/shell/`; the wall in `components/vault/`.
- Routes are `/blocks`, `/blocks/<type-or-slug>`, `/images`, `/images/<type-or-slug>`, `/tasks`, `/tasks/<id>`, `/profile`, `/mcp` and `/oauth/consent`. Operators also get `/admin/items`, `/admin/reports` and `/admin/users`. `/` redirects to `/blocks`.
- The file rail is always rendered, even for a one-file project, because the list is part of understanding the project.
- `lib/vault/links.ts` owns the URL shape; `lib/breadcrumbs.ts` owns the trail.
- When the code and this document disagree, the visual decision in this document wins. Update the code in the same change, or change this document first if the decision itself is moving.
