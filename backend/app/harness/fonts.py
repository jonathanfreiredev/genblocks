"""The type shelf: every family a block may ship, and what each one is for.

A block carries its own typeface now, so the family is part of the artifact: the
import in the block names the package, the visitor installs it, and the render the
judge reads is set in the same face the copy will be. That is why this is a table
rather than a recommendation in prose.

The shelf is curated twice over. Fontsource only carries families that may be
redistributed (OFL and friends), and this table only carries the ones we chose to
publish. Adding a family is three edits: the package in the scaffold's
``package.json``, a ``Family`` here, and ``python -m app.harness.fonts`` to rewrite
the table in ``skills/fonts.md`` — a test fails until the document matches this
module, so the agent never reads a shelf that is not the one installed.

The prose in ``skills/fonts.md`` is written by hand; only the block between the two
markers is generated. A block's copy, a designer's taste and a test's expectations
should not have to agree on line wrapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"
DOCUMENT = SKILLS_DIR / "fonts.md"

# The table's markers. Everything between them is generated.
BEGIN = "<!-- families:begin -->"
END = "<!-- families:end -->"


@dataclass(frozen=True)
class Group:
    """One heading of the table: the job a family is being asked to do."""

    slug: str
    title: str
    summary: str


@dataclass(frozen=True)
class Family:
    """One typeface, with the import path its package gives it.

    ``weights`` is the latin subset the package ships: the only one a block may
    import. ``italic`` says whether ``latin-<weight>-italic.css`` exists.
    """

    package: str
    family: str
    group: str
    weights: tuple[str, ...]
    italic: bool
    note: str


# The order the table reads in: the faces a block needs most often first, and the
# ones that are a decision rather than a default after them.
GROUPS = (
    Group("neutral-sans", "Neutral sans", "UI and body text: the faces that stay out of the way."),
    Group(
        "character-sans",
        "Sans with character",
        "A headline or a whole brand voice; not long paragraphs.",
    ),
    Group(
        "condensed",
        "Condensed and industrial",
        "Narrow faces for posters, labels and dense headlines.",
    ),
    Group("reading-serif", "Serif for reading", "Long text with a book's voice."),
    Group(
        "display-serif",
        "Serif for headlines",
        "Contrast and presence at size; a paragraph in one is a costume.",
    ),
    Group(
        "script", "Script and handwriting", "One line, large. Never a control, never a paragraph."
    ),
    Group(
        "extravagant",
        "Extravagant display",
        "Loud by design: one per block, headlines and short copy only.",
    ),
    Group("mono", "Mono", "Data, code, prices and labels, where alignment carries meaning."),
)

FAMILIES = (
    Family(
        package="@fontsource/geist",
        family="Geist",
        group="neutral-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Neutral geometric sans; the registry's own face.",
    ),
    Family(
        package="@fontsource/inter",
        family="Inter",
        group="neutral-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Neutral UI sans, tall x-height, very legible.",
    ),
    Family(
        package="@fontsource/instrument-sans",
        family="Instrument Sans",
        group="neutral-sans",
        weights=(
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Quiet grotesque with a slight editorial edge.",
    ),
    Family(
        package="@fontsource/manrope",
        family="Manrope",
        group="neutral-sans",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=False,
        note="Rounded geometric sans, friendly without being cute.",
    ),
    Family(
        package="@fontsource/public-sans",
        family="Public Sans",
        group="neutral-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Plain, government-grade sans; nothing draws attention.",
    ),
    Family(
        package="@fontsource/dm-sans",
        family="DM Sans",
        group="neutral-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Warm geometric sans with soft terminals.",
    ),
    Family(
        package="@fontsource/plus-jakarta-sans",
        family="Plus Jakarta Sans",
        group="neutral-sans",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=True,
        note="Friendly geometric sans, lightly rounded.",
    ),
    Family(
        package="@fontsource/figtree",
        family="Figtree",
        group="neutral-sans",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Clean geometric sans; neutral with a smile.",
    ),
    Family(
        package="@fontsource/work-sans",
        family="Work Sans",
        group="neutral-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Humanist workhorse; slightly wide and calm.",
    ),
    Family(
        package="@fontsource/karla",
        family="Karla",
        group="neutral-sans",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=True,
        note="Grotesque with quirky details; informal.",
    ),
    Family(
        package="@fontsource/schibsted-grotesk",
        family="Schibsted Grotesk",
        group="neutral-sans",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Editorial grotesque, tight and confident.",
    ),
    Family(
        package="@fontsource/hanken-grotesk",
        family="Hanken Grotesk",
        group="neutral-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Neutral grotesque; quiet and versatile.",
    ),
    Family(
        package="@fontsource/onest",
        family="Onest",
        group="neutral-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Modern neutral sans, slightly condensed.",
    ),
    Family(
        package="@fontsource/wix-madefor-display",
        family="Wix Madefor Display",
        group="neutral-sans",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=False,
        note="Sturdy display sans, plain-spoken.",
    ),
    Family(
        package="@fontsource/sora",
        family="Sora",
        group="character-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=False,
        note="Geometric sans built for small UI text; technical.",
    ),
    Family(
        package="@fontsource/space-grotesk",
        family="Space Grotesk",
        group="character-sans",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=False,
        note="Quirky grotesque with distinctive letterforms; tech.",
    ),
    Family(
        package="@fontsource/outfit",
        family="Outfit",
        group="character-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Sleek geometric display sans; fashion-adjacent.",
    ),
    Family(
        package="@fontsource/archivo",
        family="Archivo",
        group="character-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Sturdy grotesque with a wide range of weights.",
    ),
    Family(
        package="@fontsource/bricolage-grotesque",
        family="Bricolage Grotesque",
        group="character-sans",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=False,
        note="Expressive grotesque with odd proportions; design-led.",
    ),
    Family(
        package="@fontsource/geologica",
        family="Geologica",
        group="character-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Soft variable sans with a rounded, modern feel.",
    ),
    Family(
        package="@fontsource/anybody",
        family="Anybody",
        group="character-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Condensed-leaning display sans; athletic and loud.",
    ),
    Family(
        package="@fontsource/familjen-grotesk",
        family="Familjen Grotesk",
        group="character-sans",
        weights=(
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Editorial grotesque, sharp and modern.",
    ),
    Family(
        package="@fontsource/unbounded",
        family="Unbounded",
        group="character-sans",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Wide geometric display sans; bold and futuristic.",
    ),
    Family(
        package="@fontsource/syne",
        family="Syne",
        group="character-sans",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=False,
        note="Art-gallery display sans; unusual widths.",
    ),
    Family(
        package="@fontsource/chivo",
        family="Chivo",
        group="character-sans",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Strong grotesque; sports and editorial.",
    ),
    Family(
        package="@fontsource/rubik",
        family="Rubik",
        group="character-sans",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Rounded-corner sans, friendly and legible.",
    ),
    Family(
        package="@fontsource/oswald",
        family="Oswald",
        group="condensed",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=False,
        note="Tall condensed sans; posters and news.",
    ),
    Family(
        package="@fontsource/anton",
        family="Anton",
        group="condensed",
        weights=("400",),
        italic=False,
        note="Ultra-heavy condensed; one weight, maximum impact.",
    ),
    Family(
        package="@fontsource/barlow-condensed",
        family="Barlow Condensed",
        group="condensed",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Engineered condensed sans, clean and neutral.",
    ),
    Family(
        package="@fontsource/archivo-narrow",
        family="Archivo Narrow",
        group="condensed",
        weights=(
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Narrow grotesque; dense labels and headlines.",
    ),
    Family(
        package="@fontsource/roboto-condensed",
        family="Roboto Condensed",
        group="condensed",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Neutral condensed sans; utilitarian.",
    ),
    Family(
        package="@fontsource/fjalla-one",
        family="Fjalla One",
        group="condensed",
        weights=("400",),
        italic=False,
        note="Condensed display sans; poster-like.",
    ),
    Family(
        package="@fontsource/teko",
        family="Teko",
        group="condensed",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=False,
        note="Very condensed display sans; signage.",
    ),
    Family(
        package="@fontsource/saira-condensed",
        family="Saira Condensed",
        group="condensed",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Technical condensed sans; industrial.",
    ),
    Family(
        package="@fontsource/big-shoulders-display",
        family="Big Shoulders Display",
        group="condensed",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Ultra-condensed display sans; editorial and loud.",
    ),
    Family(
        package="@fontsource/newsreader",
        family="Newsreader",
        group="reading-serif",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=True,
        note="Editorial serif built for reading on screen.",
    ),
    Family(
        package="@fontsource/source-serif-4",
        family="Source Serif 4",
        group="reading-serif",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Sturdy transitional serif for long-form text.",
    ),
    Family(
        package="@fontsource/lora",
        family="Lora",
        group="reading-serif",
        weights=(
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Brushy contemporary serif; warm and readable.",
    ),
    Family(
        package="@fontsource/crimson-pro",
        family="Crimson Pro",
        group="reading-serif",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Bookish serif; quiet and classic.",
    ),
    Family(
        package="@fontsource/eb-garamond",
        family="EB Garamond",
        group="reading-serif",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=True,
        note="Old-style Garamond; literary and elegant.",
    ),
    Family(
        package="@fontsource/spectral",
        family="Spectral",
        group="reading-serif",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=True,
        note="Screen-first serif; calm and modern.",
    ),
    Family(
        package="@fontsource/literata",
        family="Literata",
        group="reading-serif",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="E-reader serif; highly legible at small sizes.",
    ),
    Family(
        package="@fontsource/petrona",
        family="Petrona",
        group="reading-serif",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Slab-ish serif; friendly and contemporary.",
    ),
    Family(
        package="@fontsource/libre-baskerville",
        family="Libre Baskerville",
        group="reading-serif",
        weights=(
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Classic Baskerville; formal and bookish.",
    ),
    Family(
        package="@fontsource/bitter",
        family="Bitter",
        group="reading-serif",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Contemporary slab serif; sturdy and warm.",
    ),
    Family(
        package="@fontsource/zilla-slab",
        family="Zilla Slab",
        group="reading-serif",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Friendly slab serif; geeky and open.",
    ),
    Family(
        package="@fontsource/roboto-slab",
        family="Roboto Slab",
        group="reading-serif",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Neutral slab serif; technical and plain.",
    ),
    Family(
        package="@fontsource/fraunces",
        family="Fraunces",
        group="display-serif",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Expressive old-style serif with optical sizes; characterful.",
    ),
    Family(
        package="@fontsource/instrument-serif",
        family="Instrument Serif",
        group="display-serif",
        weights=("400",),
        italic=True,
        note="High-contrast editorial serif; one weight, elegant.",
    ),
    Family(
        package="@fontsource/playfair-display",
        family="Playfair Display",
        group="display-serif",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="High-contrast Didone; magazine headlines.",
    ),
    Family(
        package="@fontsource/dm-serif-display",
        family="DM Serif Display",
        group="display-serif",
        weights=("400",),
        italic=True,
        note="Warm high-contrast serif; one weight.",
    ),
    Family(
        package="@fontsource/bodoni-moda",
        family="Bodoni Moda",
        group="display-serif",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Sharp Didone; fashion and luxury.",
    ),
    Family(
        package="@fontsource/abril-fatface",
        family="Abril Fatface",
        group="display-serif",
        weights=("400",),
        italic=False,
        note="Fat high-contrast display serif; poster.",
    ),
    Family(
        package="@fontsource/yeseva-one",
        family="Yeseva One",
        group="display-serif",
        weights=("400",),
        italic=False,
        note="Ornate display serif; decorative.",
    ),
    Family(
        package="@fontsource/prata",
        family="Prata",
        group="display-serif",
        weights=("400",),
        italic=False,
        note="Calm high-contrast display serif; quiet luxury.",
    ),
    Family(
        package="@fontsource/marcellus",
        family="Marcellus",
        group="display-serif",
        weights=("400",),
        italic=False,
        note="Roman inscriptional serif; refined.",
    ),
    Family(
        package="@fontsource/cinzel",
        family="Cinzel",
        group="display-serif",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Roman capitals; classical and ceremonial.",
    ),
    Family(
        package="@fontsource/gilda-display",
        family="Gilda Display",
        group="display-serif",
        weights=("400",),
        italic=False,
        note="Soft high-contrast serif; boutique.",
    ),
    Family(
        package="@fontsource/cormorant-garamond",
        family="Cormorant Garamond",
        group="display-serif",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Very light Garamond display; delicate.",
    ),
    Family(
        package="@fontsource/young-serif",
        family="Young Serif",
        group="display-serif",
        weights=("400",),
        italic=False,
        note="Chunky contemporary serif; warm and bold.",
    ),
    Family(
        package="@fontsource/alfa-slab-one",
        family="Alfa Slab One",
        group="display-serif",
        weights=("400",),
        italic=False,
        note="Heavy slab display; retro poster.",
    ),
    Family(
        package="@fontsource/caveat",
        family="Caveat",
        group="script",
        weights=(
            "400",
            "500",
            "600",
            "700",
        ),
        italic=False,
        note="Handwritten marker; casual annotations.",
    ),
    Family(
        package="@fontsource/dancing-script",
        family="Dancing Script",
        group="script",
        weights=(
            "400",
            "500",
            "600",
            "700",
        ),
        italic=False,
        note="Flowing script; warm and informal.",
    ),
    Family(
        package="@fontsource/great-vibes",
        family="Great Vibes",
        group="script",
        weights=("400",),
        italic=False,
        note="Formal calligraphic script; invitation-like.",
    ),
    Family(
        package="@fontsource/pacifico",
        family="Pacifico",
        group="script",
        weights=("400",),
        italic=False,
        note="Retro surf script; friendly.",
    ),
    Family(
        package="@fontsource/kalam",
        family="Kalam",
        group="script",
        weights=(
            "300",
            "400",
            "700",
        ),
        italic=False,
        note="Hand-drawn pen script; informal notes.",
    ),
    Family(
        package="@fontsource/courgette",
        family="Courgette",
        group="script",
        weights=("400",),
        italic=False,
        note="Soft brush script; friendly.",
    ),
    Family(
        package="@fontsource/satisfy",
        family="Satisfy",
        group="script",
        weights=("400",),
        italic=False,
        note="Loose brush script; casual.",
    ),
    Family(
        package="@fontsource/amatic-sc",
        family="Amatic SC",
        group="script",
        weights=(
            "400",
            "700",
        ),
        italic=False,
        note="Tall hand-drawn capitals; craft and poster.",
    ),
    Family(
        package="@fontsource/permanent-marker",
        family="Permanent Marker",
        group="script",
        weights=("400",),
        italic=False,
        note="Felt-tip marker; loud and casual.",
    ),
    Family(
        package="@fontsource/sacramento",
        family="Sacramento",
        group="script",
        weights=("400",),
        italic=False,
        note="Thin monoline script; light and elegant.",
    ),
    Family(
        package="@fontsource/monoton",
        family="Monoton",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Neon tube lines; retro signage.",
    ),
    Family(
        package="@fontsource/bungee",
        family="Bungee",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Urban signage capitals; blocky and playful.",
    ),
    Family(
        package="@fontsource/climate-crisis",
        family="Climate Crisis",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Melting, distorted display; loud and strange.",
    ),
    Family(
        package="@fontsource/nabla",
        family="Nabla",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Colour font with depth; Chromium only, heavy, never for body.",
    ),
    Family(
        package="@fontsource/rubik-glitch",
        family="Rubik Glitch",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Glitched letterforms; digital noise.",
    ),
    Family(
        package="@fontsource/silkscreen",
        family="Silkscreen",
        group="extravagant",
        weights=(
            "400",
            "700",
        ),
        italic=False,
        note="Pixel font; 8-bit, best small.",
    ),
    Family(
        package="@fontsource/press-start-2p",
        family="Press Start 2P",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Arcade pixel font; gaming.",
    ),
    Family(
        package="@fontsource/major-mono-display",
        family="Major Mono Display",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Wide geometric mono display; retro-future.",
    ),
    Family(
        package="@fontsource/zen-dots",
        family="Zen Dots",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Dotted geometric display; techno.",
    ),
    Family(
        package="@fontsource/audiowide",
        family="Audiowide",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Wide techno sans; motorsport.",
    ),
    Family(
        package="@fontsource/orbitron",
        family="Orbitron",
        group="extravagant",
        weights=(
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=False,
        note="Sci-fi geometric display; space.",
    ),
    Family(
        package="@fontsource/michroma",
        family="Michroma",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Wide squared techno sans; hardware.",
    ),
    Family(
        package="@fontsource/syncopate",
        family="Syncopate",
        group="extravagant",
        weights=(
            "400",
            "700",
        ),
        italic=False,
        note="Wide, spaced capitals; luxury-tech.",
    ),
    Family(
        package="@fontsource/righteous",
        family="Righteous",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Rounded retro display; friendly.",
    ),
    Family(
        package="@fontsource/rye",
        family="Rye",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Western wood-type slab; Americana.",
    ),
    Family(
        package="@fontsource/titan-one",
        family="Titan One",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Rounded fat display; playful and loud.",
    ),
    Family(
        package="@fontsource/bowlby-one",
        family="Bowlby One",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Chunky rounded display; poster.",
    ),
    Family(
        package="@fontsource/frijole",
        family="Frijole",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Rough hand-drawn display; zine.",
    ),
    Family(
        package="@fontsource/ranchers",
        family="Ranchers",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Western condensed display; rodeo.",
    ),
    Family(
        package="@fontsource/rubik-mono-one",
        family="Rubik Mono One",
        group="extravagant",
        weights=("400",),
        italic=False,
        note="Blocky rounded mono display; heavy.",
    ),
    Family(
        package="@fontsource/jetbrains-mono",
        family="JetBrains Mono",
        group="mono",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=True,
        note="Developer mono; clear and neutral.",
    ),
    Family(
        package="@fontsource/geist-mono",
        family="Geist Mono",
        group="mono",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Neutral mono matching Geist; UI data.",
    ),
    Family(
        package="@fontsource/ibm-plex-mono",
        family="IBM Plex Mono",
        group="mono",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Technical mono with a humanist touch.",
    ),
    Family(
        package="@fontsource/space-mono",
        family="Space Mono",
        group="mono",
        weights=(
            "400",
            "700",
        ),
        italic=True,
        note="Quirky geometric mono; retro-tech.",
    ),
    Family(
        package="@fontsource/fira-code",
        family="Fira Code",
        group="mono",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=False,
        note="Coding mono with ligatures; technical.",
    ),
    Family(
        package="@fontsource/source-code-pro",
        family="Source Code Pro",
        group="mono",
        weights=(
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Neutral coding mono; very legible.",
    ),
    Family(
        package="@fontsource/dm-mono",
        family="DM Mono",
        group="mono",
        weights=(
            "300",
            "400",
            "500",
        ),
        italic=True,
        note="Light geometric mono; quiet data.",
    ),
    Family(
        package="@fontsource/martian-mono",
        family="Martian Mono",
        group="mono",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
        ),
        italic=False,
        note="Wide, low-contrast mono; sturdy and technical.",
    ),
    Family(
        package="@fontsource/azeret-mono",
        family="Azeret Mono",
        group="mono",
        weights=(
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ),
        italic=True,
        note="Squared mono; editorial-technical.",
    ),
    Family(
        package="@fontsource/fragment-mono",
        family="Fragment Mono",
        group="mono",
        weights=("400",),
        italic=True,
        note="Grotesque mono; neutral and compact.",
    ),
    Family(
        package="@fontsource/spline-sans-mono",
        family="Spline Sans Mono",
        group="mono",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Sans-like mono; UI labels.",
    ),
    Family(
        package="@fontsource/red-hat-mono",
        family="Red Hat Mono",
        group="mono",
        weights=(
            "300",
            "400",
            "500",
            "600",
            "700",
        ),
        italic=True,
        note="Friendly mono; modern brand system.",
    ),
)


def weights_text(family: Family) -> str:
    """``100-900`` when the family fills the scale, otherwise the weights it has."""
    numbers = [int(weight) for weight in family.weights]
    if len(numbers) > 1 and numbers == list(range(numbers[0], numbers[-1] + 1, 100)):
        return f"{numbers[0]}-{numbers[-1]}"

    return " ".join(str(number) for number in numbers)


def table() -> str:
    """The catalog, one table per group, as the skill embeds it."""
    blocks: list[str] = []
    for group in GROUPS:
        members = [family for family in FAMILIES if family.group == group.slug]
        rows = "\n".join(
            f"| {family.family} | `{family.package}` | {weights_text(family)} "
            f"| {'yes' if family.italic else 'no'} | {family.note} |"
            for family in members
        )
        blocks.append(
            f"### {group.title}\n\n{group.summary}\n\n"
            "| Family | Package | Weights | Italic | Character |\n"
            "| --- | --- | --- | --- | --- |\n"
            f"{rows}"
        )

    return "\n\n".join(blocks)


def render(document: str) -> str:
    """The document with a fresh table between its markers.

    Raises :class:`ValueError` when the markers are gone, because a silently
    ungenerated document is a shelf the agent reads and the image does not have.
    """
    before, marker, rest = document.partition(BEGIN)
    if not marker:
        raise ValueError(f"The fonts document has no {BEGIN!r} marker.")

    _, marker, after = rest.partition(END)
    if not marker:
        raise ValueError(f"The fonts document has no {END!r} marker.")

    return f"{before}{BEGIN}\n\n{table()}\n\n{END}{after}"


def current() -> str:
    """The document on disk, for the loader and for the test that guards it."""
    return DOCUMENT.read_text(encoding="utf-8")


def main() -> None:
    """Rewrite the generated half of the skill. Run from ``backend/``."""
    document = current()
    updated = render(document)
    if updated == document:
        print(f"fonts: {len(FAMILIES)} families, the document is current")
        return

    DOCUMENT.write_text(updated, encoding="utf-8")
    print(f"fonts: {len(FAMILIES)} families written to {DOCUMENT}")


if __name__ == "__main__":
    main()
