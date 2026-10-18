# What you may import, and when

The shelf is small on purpose. Reach for a package when it answers a real
problem; a block that needs nothing installs anywhere, and that is worth a lot.

- **CSS and Tailwind first.** A hover state, a focus ring, a colour that changes,
  a one-shot entrance: `transition-*`, `duration-*`, `ease-*`, `group-hover`,
  `peer-*`, `data-*` variants and an inline `<style>` for keyframes. No package
  earns its place for a colour that changes when the pointer arrives.
- **`motion`** (`motion/react`) — movement that has to be *run*: entrances to the
  page, exits, a list reordering, springs, sequences, anything that needs to know
  when it finished. `import { motion, AnimatePresence, useReducedMotion } from
  "motion/react"`.
- **`@base-ui/react`** — behaviour you should not write by hand: dialog, popover,
  tabs, accordion, menu, tooltip, switch, checkbox, select, slider, progress.
  It is unstyled, it handles focus and keyboard for you, and the look stays yours.
  Prefer it over a `div` with an `onClick`, every time.
- **`lucide-react`** — icons: `import { ArrowRight } from "lucide-react"`. Size
  them with Tailwind, and hide them from screen readers when the text beside them
  already says what they mean.
- **`clsx` + `tailwind-merge`** — the `cn` helper, for classes that depend on
  state: `cn("inline-flex items-center", isActive && "bg-neutral-900")`. Do not
  build class strings by concatenation, and do not let two conflicting classes
  fight: `cn` is what resolves them.
- **`class-variance-authority`** — when the block really has variants (a button
  that is primary, secondary or ghost). For two variants, a record of class
  strings is quieter than a factory.

What not to import: `react-dom`, a router, a state manager, a form library, a CSS
framework, a charting library, an icon set other than Lucide, or anything that
brings its own look. Charts are drawn: an SVG with a real viewBox beats a library
that draws one for you and brings a DOM, a theme and 200 KB with it.
