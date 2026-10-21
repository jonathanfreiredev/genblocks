# Composition

The judge scores what it sees. What it is looking for is decisions, not
decoration.

- **Hierarchy**: one thing wins, and the rest is quiet about it. Size, weight,
  colour and space are the four levers. Pulling all four on everything is how a
  block ends up with no hierarchy at all.
- **Space has a rhythm**: pick a scale (4, 8, 12, 16, 24, 32, 48, 64 in Tailwind)
  and use those numbers. A section needs more air than its contents, and a group
  more than the items inside it. Even spacing everywhere is the same as no
  spacing decisions.
- **Alignment**: the eye should find a few edges and keep finding them. If three
  elements start at three different x positions with nothing to say, something is
  arbitrary.
- **Restraint**: two type sizes and one accent colour carry most blocks. Every
  extra colour, border, radius and shadow spends attention the content needed.
  Remove until it hurts, then stop.
- **Responsive**: decide the phone layout first, then say what changes at `sm`,
  `md`, `lg` and above. Columns that never collapse are the most common way a block
  overflows its width. A block is measured at 390, 834, 1024 and 1440.
- **The page is not yours**: the block sits inside somebody else's layout. It owns
  its own section and nothing above it, so it should not assume the page's
  background, fonts or spacing beyond Tailwind's own.
