# Composition

The judge scores what it sees. What it is looking for is decisions, not
decoration.

- **Hierarchy**: one thing wins, and the rest is quiet about it. Size, weight,
  colour and space are the four levers. Pulling all four on everything is how a
  block ends up with no hierarchy at all.
- **Space has a rhythm**: pick a scale (4, 8, 12, 16, 24, 32, 48, 64, 96 in
  Tailwind) and use those numbers. A section needs more air than its contents, and
  a group more than the items inside it. Even spacing everywhere is the same as no
  spacing decisions.
- **Three distances, not one.** Related items sit 8-12px apart, a group sits 24-32
  from the next group, and a section gives 64-96 to the page. If every gap is 24,
  nothing is grouped.
- **Alignment**: the eye should find a few edges and keep finding them. If three
  elements start at three different x positions with nothing to say, something is
  arbitrary. Two edges per block is a system; five is a mess.
- **The container is decided once.** A max width, and one padding pair that scales
  (24 on a phone, 48-64 on a desktop). A block that hugs the viewport on one screen
  and floats in a narrow column on the next is two layouts.
- **Measure**: body text 60-75 characters, headlines 20-30. A paragraph that runs
  the width of a desktop is unreadable, and a headline broken into four lines is a
  shape nobody asked for.
- **Optical, not mathematical.** Text and an icon on one line align on the
  cap-height, not on the box. Icons are sized to the line they sit in and nudged a
  pixel when the eye asks. Figures use `tabular-nums` when they sit in a column.
- **Density follows the direction.** Sparse: one idea per viewport, generous
  section padding, nothing competing. Dense: 12-16px rows, tight numerals, but the
  same 24px target for anything a thumb presses.
- **Restraint**: two type sizes and one accent colour carry most blocks. Every
  extra colour, border, radius and shadow spends attention the content needed.
  Remove until it hurts, then stop.
- **Responsive**: decide the phone layout first, then say what changes at `sm`,
  `md`, `lg` and above. Columns that never collapse are the most common way a block
  overflows its width. A block is measured at 390, 834, 1024 and 1440.
- **The page is not yours**: the block sits inside somebody else's layout. It owns
  its own section and nothing above it, so it should not assume the page's
  background, fonts or spacing beyond Tailwind's own — a typeface is the exception
  it brings with it (see `fonts`).
