# What a block is here

You are building one entry of GenBlocks: a block that somebody copies into their
own project and keeps. Everything below is a constraint on the artifact, not a
style suggestion.

- **A project, not a file.** `src/Block.tsx` is the entry point: it has to exist,
  and the page imports its default export. You may add other files under `src/`
  and import them — split when a file gets long, when a piece repeats, or when a
  part has its own concern (a form's field, a card's footer).
- **React, Tailwind, and the packages on the shelf** (`dependencies`). Nothing
  else: an import outside the shelf does not build, and if it did, the person
  copying the block could not install it.
- **Generic Tailwind utilities only.** No classes and no design tokens from
  another application. A `<style>` block inside your component is fine for
  keyframes you need, because it travels with the block.
- **It carries its chrome and borrows its pictures.** Icons and primitives are
  packages; photographs are assets of our library, handed to you as URLs. A URL to
  anything else is a picture that will not arrive. Cloudinary answers a transform
  in the path (`/upload/w_1200/...`) if you need a size. This is checked before the
  block is built: every `src`, `srcset`, `poster`, stylesheet link, CSS `url()` and
  `@import` must be relative, a `data:` URL, or one of our hosts. A font imported
  from Google is a stylesheet that does not travel.
- **No network, no strings run as code.** A block is markup: it does not `fetch`,
  open sockets, `eval`, build functions from strings, `document.write` or inject
  HTML. The page you are inside owns its data, and those are the ways a block stops
  being a block and becomes a script.
- **Every picture is its own subject.** One prompt per picture, and a different
  scene in each: the same prompt asked twice comes back nearly the same
  photograph, and a row of nearly identical photographs is a defect a judge will
  name. Three pictures in a band are three scenes, described three ways.
- **Both grounds.** The registry switches the whole library between light and dark
  by putting `dark` on the page, and `dark:` answers to that class — never to
  `prefers-color-scheme`, which would ignore the switch. Write every colour as a
  pair: `bg-white dark:bg-neutral-950`, `text-neutral-900 dark:text-neutral-100`,
  `border-neutral-200 dark:border-neutral-800`. The dark page is a near-black
  ground with light text, so a section that paints no background is showing the
  host's. Both grounds are photographed and judged: a block that is only right on
  one of them is half a block.
- **Ask for pictures late, and give them their box first.** If the brief wants a
  photograph, build and look at the block with the space it will fill — a box with
  the final proportions — and ask for the picture once the layout holds. The box is
  what keeps the swap from moving anything, and a picture asked for early is asked
  for twice.
- **Responsive by default**, at 390, 834, 1024 and 1440. Nothing may overflow its
  width at any of them — the four layout checks are a gate, not advice — and the
  phone layout is the one to design first.
- **Usable with a thumb and a keyboard**: every control at least 24×24px on a
  phone, a visible focus ring on every interactive element, and no control that
  is a `div` with an `onClick`.
- **One block, not a page.** No `html`, `head` or `body`; no navbar plus footer; no
  component that only makes sense inside a layout it does not own.
- **Verbatim copy.** The block is published as the files you leave behind, so what
  you leave has to be what you would ship: no `TODO`, no unused file, no comment
  explaining what you were about to do.
