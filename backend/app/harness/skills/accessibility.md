# Accessibility

This is not a check to run at the end; it is the difference between a block that
works for somebody who cannot see it, cannot use a mouse, or cannot read a moving
target.

- **Contrast**: 4.5:1 for text, 3:1 for large text and for the boundaries somebody
  needs to find a control. Muted greys are where this fails, and a "soft" palette
  is the usual way a block loses it. Test the pairs you actually use, on the
  background they actually sit on.
- **Structure**: one `h1` if the block owns the page's heading, and headings in
  order below it. Sections are `section`, lists are `ul`/`ol`, a set of links is
  `nav`. A heading made with bold text is not a heading.
- **Controls**: `button` for actions, `a` for destinations, a `label` for every
  input (visible, or `sr-only` when the placeholder is doing the talking). Never a
  `div` with an `onClick`: that is a control nobody can reach from a keyboard.
- **Names**: an icon-only control needs `aria-label`; a picture that carries
  meaning needs `alt` that says it; a picture that is decoration takes `alt=""`.
  A link's text has to make sense read on its own.
- **Focus**: visible, and never removed without a replacement. Tailwind's
  `focus-visible:outline-*` is the default answer, and the focus ring has to be
  visible against the element's own background.
- **Motion**: everything that moves has to be optional — the rule is in `motion`.
  A block whose content only appears once an animation has run is invisible to
  somebody with reduced motion on, and that is a defect, not a preference.
- **Updates**: if the block changes its own text (a counter, a confirmation, a
  filter result), say so with a live region, or the change is silent.
