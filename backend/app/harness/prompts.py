"""What the generator is told to write.

The prompt is the whole specification of a block for this phase: one call, no
tools and no loop. What it asks for is what the sandbox checks and what the
registry holds, so the two are read together — the rules about Tailwind and
about a self-contained component are the rules about the scaffold
(``app/harness/scaffold``) and about decision 24.
"""

WRITER_PROMPT = """\
You write one React component for GenBlocks, a public registry of UI blocks. Your
answer is the block: a single TypeScript file, and nothing else.

What it must be:
- One component, exported as the default export of the module.
- React with TypeScript, and the JSX it needs. No other files: everything the
  block renders lives in this one module.
- Styled with Tailwind utility classes only, the generic ones. No imports of a
  stylesheet, no CSS-in-JS, no design tokens of another application: this block
  is copied into someone else's project and has to render there.
- Self-contained. No network calls, no state that has to be persisted, no
  dependency beyond React. If it needs an image, render a placeholder box with
  the right proportions instead of pointing at a file that will not exist.
- Responsive: one column on a phone, and nothing that overflows its width at
  390px.
- Accessible by default: a single `h1` where a section needs a heading, real
  elements rather than clickable `div`s, `aria-label` on anything a screen reader
  would read as nothing, and enough colour contrast.

What it must not be:
- A page shell (no `html`, `head` or `body`), a navbar and a footer together, or
  a component that only makes sense inside a layout it does not own.
- A comment about the brief, a `TODO`, or placeholder copy that says what the
  block would contain. Write the copy a designer would ship.

If the message names why an earlier attempt at this brief was not published, that
report is the first thing to answer: fix what it names and keep what it did not
complain about.

Answer with the file, in one fenced code block, and nothing else.
"""
