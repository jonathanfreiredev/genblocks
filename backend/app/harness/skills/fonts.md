# Type on this shelf

A block ships its own typeface. The family is part of what a visitor copies, so the
choice is a design decision and a delivery decision at once: the import names a
package, the visitor installs it, and the face you photographed is the face they
get. Nothing is fetched from a font CDN, at build time or at run time.

The categories below are not a hierarchy. They are the jobs a face can be asked to
do, and the brief is what tells you which job is on the table. Read the brief's tone
before you read this table: "clean and modern" starts in the neutral sans, "an
editorial hero" starts in the serif for headlines, "a launch page for a game" may be
the one place an extravagant display is the right answer.

## Choosing

- **Two families by default, three at most.** One for display, one for text, and —
  when the content earns it — one utility face. Three families with three equal
  jobs is not a system, it is three decisions.
- **The third family has to have a job of its own.** A mono for prices, timestamps
  or code, or a display face that only sets the headline. Two sans fighting over
  the same paragraph is the mistake this rule exists to prevent.
- **A loud face needs a quiet partner.** One extravagant or script face per block,
  headlines and short copy only. Never body text, never a button, never a label.
- **Script is one line, large.** A signature, a date, a single word. At 14px it is
  unreadable, and in a control it is unusable.
- **Mono is for data.** Figures that should line up, code, versions, identifiers.
  Its job is alignment, not decoration.
- **Size and weight carry more than the family does.** A neutral sans at three
  sizes and two weights has more hierarchy than two fancy faces at one size each.
- **If the brief names a family in the table, use it.** If it names one that is
  not here — a commercial face, a Fontshare release, something from a brand book —
  choose the closest in the same group and say which you used in your final answer.
  Do not pretend the substitute is the requested font.

## Installing one

One import per weight, latin subset only:

```tsx
import "@fontsource/instrument-serif/latin-400.css";
import "@fontsource/geist/latin-400.css";
import "@fontsource/geist/latin-700.css";
import "@fontsource/jetbrains-mono/latin-400.css";
```

- `latin-<weight>.css` is the subset a block ships. `latin-<weight>-italic.css`
  exists only where the table says the family has an italic.
- Never import the bare package (`"@fontsource/geist"`), `index.css`, or a
  `@fontsource-variable/*` package: those ship every script the family has, and
  the preview is one document, so every one of them is inlined into it.
- Never a Google Fonts URL or a `@font-face` pointing at another host. A stylesheet
  from somewhere else is a block that breaks the day that host changes, and the
  checker refuses it before the build.
- The imports are what a visitor installs: the package column is the first half of
  every import, and the weight is the rest. Nothing else needs to be installed for
  a typeface.

## Applying one

Put the family on the block's root, through one class per role in the block's own
stylesheet, and let inheritance do the rest:

```css
/* the block's own CSS file, which travels with it */
.type-display { font-family: "Instrument Serif", Georgia, serif; }
.type-body { font-family: "Geist", ui-sans-serif, system-ui, sans-serif; }
.type-mono { font-family: "JetBrains Mono", ui-monospace, monospace; }
```

```tsx
<section className="type-body">
  <h1 className="type-display text-6xl">…</h1>
  <span className="type-mono tabular-nums">€24</span>
</section>
```

- `button`, `input`, `select` and `textarea` inherit the family: Tailwind's
  preflight sets `font: inherit` on them, so do not repeat the class on every
  field.
- `code`, `kbd`, `samp` and `pre` do **not** inherit: Tailwind gives them the mono
  stack by itself. Put `type-mono` on the element when the mono face matters.
- `font-medium` is a weight; `font-['Geist']` is a family. Two different things
  behind the same prefix.
- A class per role, not a family on every element: the second one is unreadable
  for the person copying the block and easy to leave half-applied.

## The families

<!-- families:begin -->

### Neutral sans

UI and body text: the faces that stay out of the way.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| Geist | `@fontsource/geist` | 100-900 | yes | Neutral geometric sans; the registry's own face. |
| Inter | `@fontsource/inter` | 100-900 | yes | Neutral UI sans, tall x-height, very legible. |
| Instrument Sans | `@fontsource/instrument-sans` | 400-700 | yes | Quiet grotesque with a slight editorial edge. |
| Manrope | `@fontsource/manrope` | 200-800 | no | Rounded geometric sans, friendly without being cute. |
| Public Sans | `@fontsource/public-sans` | 100-900 | yes | Plain, government-grade sans; nothing draws attention. |
| DM Sans | `@fontsource/dm-sans` | 100-900 | yes | Warm geometric sans with soft terminals. |
| Plus Jakarta Sans | `@fontsource/plus-jakarta-sans` | 200-800 | yes | Friendly geometric sans, lightly rounded. |
| Figtree | `@fontsource/figtree` | 300-900 | yes | Clean geometric sans; neutral with a smile. |
| Work Sans | `@fontsource/work-sans` | 100-900 | yes | Humanist workhorse; slightly wide and calm. |
| Karla | `@fontsource/karla` | 200-800 | yes | Grotesque with quirky details; informal. |
| Schibsted Grotesk | `@fontsource/schibsted-grotesk` | 400-900 | yes | Editorial grotesque, tight and confident. |
| Hanken Grotesk | `@fontsource/hanken-grotesk` | 100-900 | yes | Neutral grotesque; quiet and versatile. |
| Onest | `@fontsource/onest` | 100-900 | no | Modern neutral sans, slightly condensed. |
| Wix Madefor Display | `@fontsource/wix-madefor-display` | 400-800 | no | Sturdy display sans, plain-spoken. |

### Sans with character

A headline or a whole brand voice; not long paragraphs.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| Sora | `@fontsource/sora` | 100-800 | no | Geometric sans built for small UI text; technical. |
| Space Grotesk | `@fontsource/space-grotesk` | 300-700 | no | Quirky grotesque with distinctive letterforms; tech. |
| Outfit | `@fontsource/outfit` | 100-900 | no | Sleek geometric display sans; fashion-adjacent. |
| Archivo | `@fontsource/archivo` | 100-900 | yes | Sturdy grotesque with a wide range of weights. |
| Bricolage Grotesque | `@fontsource/bricolage-grotesque` | 200-800 | no | Expressive grotesque with odd proportions; design-led. |
| Geologica | `@fontsource/geologica` | 100-900 | no | Soft variable sans with a rounded, modern feel. |
| Anybody | `@fontsource/anybody` | 100-900 | yes | Condensed-leaning display sans; athletic and loud. |
| Familjen Grotesk | `@fontsource/familjen-grotesk` | 400-700 | yes | Editorial grotesque, sharp and modern. |
| Unbounded | `@fontsource/unbounded` | 200-900 | no | Wide geometric display sans; bold and futuristic. |
| Syne | `@fontsource/syne` | 400-800 | no | Art-gallery display sans; unusual widths. |
| Chivo | `@fontsource/chivo` | 100-900 | yes | Strong grotesque; sports and editorial. |
| Rubik | `@fontsource/rubik` | 300-900 | yes | Rounded-corner sans, friendly and legible. |

### Condensed and industrial

Narrow faces for posters, labels and dense headlines.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| Oswald | `@fontsource/oswald` | 200-700 | no | Tall condensed sans; posters and news. |
| Anton | `@fontsource/anton` | 400 | no | Ultra-heavy condensed; one weight, maximum impact. |
| Barlow Condensed | `@fontsource/barlow-condensed` | 100-900 | yes | Engineered condensed sans, clean and neutral. |
| Archivo Narrow | `@fontsource/archivo-narrow` | 400-700 | yes | Narrow grotesque; dense labels and headlines. |
| Roboto Condensed | `@fontsource/roboto-condensed` | 100-900 | yes | Neutral condensed sans; utilitarian. |
| Fjalla One | `@fontsource/fjalla-one` | 400 | no | Condensed display sans; poster-like. |
| Teko | `@fontsource/teko` | 300-700 | no | Very condensed display sans; signage. |
| Saira Condensed | `@fontsource/saira-condensed` | 100-900 | no | Technical condensed sans; industrial. |
| Big Shoulders Display | `@fontsource/big-shoulders-display` | 100-900 | no | Ultra-condensed display sans; editorial and loud. |

### Serif for reading

Long text with a book's voice.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| Newsreader | `@fontsource/newsreader` | 200-800 | yes | Editorial serif built for reading on screen. |
| Source Serif 4 | `@fontsource/source-serif-4` | 200-900 | yes | Sturdy transitional serif for long-form text. |
| Lora | `@fontsource/lora` | 400-700 | yes | Brushy contemporary serif; warm and readable. |
| Crimson Pro | `@fontsource/crimson-pro` | 200-900 | yes | Bookish serif; quiet and classic. |
| EB Garamond | `@fontsource/eb-garamond` | 400-800 | yes | Old-style Garamond; literary and elegant. |
| Spectral | `@fontsource/spectral` | 200-800 | yes | Screen-first serif; calm and modern. |
| Literata | `@fontsource/literata` | 200-900 | yes | E-reader serif; highly legible at small sizes. |
| Petrona | `@fontsource/petrona` | 100-900 | yes | Slab-ish serif; friendly and contemporary. |
| Libre Baskerville | `@fontsource/libre-baskerville` | 400-700 | yes | Classic Baskerville; formal and bookish. |
| Bitter | `@fontsource/bitter` | 100-900 | yes | Contemporary slab serif; sturdy and warm. |
| Zilla Slab | `@fontsource/zilla-slab` | 300-700 | yes | Friendly slab serif; geeky and open. |
| Roboto Slab | `@fontsource/roboto-slab` | 100-900 | no | Neutral slab serif; technical and plain. |

### Serif for headlines

Contrast and presence at size; a paragraph in one is a costume.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| Fraunces | `@fontsource/fraunces` | 100-900 | yes | Expressive old-style serif with optical sizes; characterful. |
| Instrument Serif | `@fontsource/instrument-serif` | 400 | yes | High-contrast editorial serif; one weight, elegant. |
| Playfair Display | `@fontsource/playfair-display` | 400-900 | yes | High-contrast Didone; magazine headlines. |
| DM Serif Display | `@fontsource/dm-serif-display` | 400 | yes | Warm high-contrast serif; one weight. |
| Bodoni Moda | `@fontsource/bodoni-moda` | 400-900 | yes | Sharp Didone; fashion and luxury. |
| Abril Fatface | `@fontsource/abril-fatface` | 400 | no | Fat high-contrast display serif; poster. |
| Yeseva One | `@fontsource/yeseva-one` | 400 | no | Ornate display serif; decorative. |
| Prata | `@fontsource/prata` | 400 | no | Calm high-contrast display serif; quiet luxury. |
| Marcellus | `@fontsource/marcellus` | 400 | no | Roman inscriptional serif; refined. |
| Cinzel | `@fontsource/cinzel` | 400-900 | no | Roman capitals; classical and ceremonial. |
| Gilda Display | `@fontsource/gilda-display` | 400 | no | Soft high-contrast serif; boutique. |
| Cormorant Garamond | `@fontsource/cormorant-garamond` | 300-700 | yes | Very light Garamond display; delicate. |
| Young Serif | `@fontsource/young-serif` | 400 | no | Chunky contemporary serif; warm and bold. |
| Alfa Slab One | `@fontsource/alfa-slab-one` | 400 | no | Heavy slab display; retro poster. |

### Script and handwriting

One line, large. Never a control, never a paragraph.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| Caveat | `@fontsource/caveat` | 400-700 | no | Handwritten marker; casual annotations. |
| Dancing Script | `@fontsource/dancing-script` | 400-700 | no | Flowing script; warm and informal. |
| Great Vibes | `@fontsource/great-vibes` | 400 | no | Formal calligraphic script; invitation-like. |
| Pacifico | `@fontsource/pacifico` | 400 | no | Retro surf script; friendly. |
| Kalam | `@fontsource/kalam` | 300 400 700 | no | Hand-drawn pen script; informal notes. |
| Courgette | `@fontsource/courgette` | 400 | no | Soft brush script; friendly. |
| Satisfy | `@fontsource/satisfy` | 400 | no | Loose brush script; casual. |
| Amatic SC | `@fontsource/amatic-sc` | 400 700 | no | Tall hand-drawn capitals; craft and poster. |
| Permanent Marker | `@fontsource/permanent-marker` | 400 | no | Felt-tip marker; loud and casual. |
| Sacramento | `@fontsource/sacramento` | 400 | no | Thin monoline script; light and elegant. |

### Extravagant display

Loud by design: one per block, headlines and short copy only.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| Monoton | `@fontsource/monoton` | 400 | no | Neon tube lines; retro signage. |
| Bungee | `@fontsource/bungee` | 400 | no | Urban signage capitals; blocky and playful. |
| Climate Crisis | `@fontsource/climate-crisis` | 400 | no | Melting, distorted display; loud and strange. |
| Nabla | `@fontsource/nabla` | 400 | no | Colour font with depth; Chromium only, heavy, never for body. |
| Rubik Glitch | `@fontsource/rubik-glitch` | 400 | no | Glitched letterforms; digital noise. |
| Silkscreen | `@fontsource/silkscreen` | 400 700 | no | Pixel font; 8-bit, best small. |
| Press Start 2P | `@fontsource/press-start-2p` | 400 | no | Arcade pixel font; gaming. |
| Major Mono Display | `@fontsource/major-mono-display` | 400 | no | Wide geometric mono display; retro-future. |
| Zen Dots | `@fontsource/zen-dots` | 400 | no | Dotted geometric display; techno. |
| Audiowide | `@fontsource/audiowide` | 400 | no | Wide techno sans; motorsport. |
| Orbitron | `@fontsource/orbitron` | 400-900 | no | Sci-fi geometric display; space. |
| Michroma | `@fontsource/michroma` | 400 | no | Wide squared techno sans; hardware. |
| Syncopate | `@fontsource/syncopate` | 400 700 | no | Wide, spaced capitals; luxury-tech. |
| Righteous | `@fontsource/righteous` | 400 | no | Rounded retro display; friendly. |
| Rye | `@fontsource/rye` | 400 | no | Western wood-type slab; Americana. |
| Titan One | `@fontsource/titan-one` | 400 | no | Rounded fat display; playful and loud. |
| Bowlby One | `@fontsource/bowlby-one` | 400 | no | Chunky rounded display; poster. |
| Frijole | `@fontsource/frijole` | 400 | no | Rough hand-drawn display; zine. |
| Ranchers | `@fontsource/ranchers` | 400 | no | Western condensed display; rodeo. |
| Rubik Mono One | `@fontsource/rubik-mono-one` | 400 | no | Blocky rounded mono display; heavy. |

### Mono

Data, code, prices and labels, where alignment carries meaning.

| Family | Package | Weights | Italic | Character |
| --- | --- | --- | --- | --- |
| JetBrains Mono | `@fontsource/jetbrains-mono` | 100-800 | yes | Developer mono; clear and neutral. |
| Geist Mono | `@fontsource/geist-mono` | 100-900 | yes | Neutral mono matching Geist; UI data. |
| IBM Plex Mono | `@fontsource/ibm-plex-mono` | 100-700 | yes | Technical mono with a humanist touch. |
| Space Mono | `@fontsource/space-mono` | 400 700 | yes | Quirky geometric mono; retro-tech. |
| Fira Code | `@fontsource/fira-code` | 300-700 | no | Coding mono with ligatures; technical. |
| Source Code Pro | `@fontsource/source-code-pro` | 200-900 | yes | Neutral coding mono; very legible. |
| DM Mono | `@fontsource/dm-mono` | 300-500 | yes | Light geometric mono; quiet data. |
| Martian Mono | `@fontsource/martian-mono` | 100-800 | no | Wide, low-contrast mono; sturdy and technical. |
| Azeret Mono | `@fontsource/azeret-mono` | 100-900 | yes | Squared mono; editorial-technical. |
| Fragment Mono | `@fontsource/fragment-mono` | 400 | yes | Grotesque mono; neutral and compact. |
| Spline Sans Mono | `@fontsource/spline-sans-mono` | 300-700 | yes | Sans-like mono; UI labels. |
| Red Hat Mono | `@fontsource/red-hat-mono` | 300-700 | yes | Friendly mono; modern brand system. |

<!-- families:end -->
