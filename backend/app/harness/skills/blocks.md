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
  in the path (`/upload/w_1200/...`) if you need a size.
- **Every picture is its own subject.** One prompt per picture, and a different
  scene in each: the same prompt asked twice comes back nearly the same
  photograph, and a row of nearly identical photographs is a defect a judge will
  name. Three pictures in a band are three scenes, described three ways.
- **Ask for pictures late, and give them their box first.** If the brief wants a
  photograph, build and look at the block with the space it will fill — a box with
  the final proportions — and ask for the picture once the layout holds. The box is
  what keeps the swap from moving anything, and a picture asked for early is asked
  for twice.
- **Responsive by default**, from a 390px phone up. Nothing may overflow its width
  at any size the registry renders.
- **One block, not a page.** No `html`, `head` or `body`; no navbar plus footer; no
  component that only makes sense inside a layout it does not own.
- **Verbatim copy.** The block is published as the files you leave behind, so what
  you leave has to be what you would ship: no `TODO`, no unused file, no comment
  explaining what you were about to do.
