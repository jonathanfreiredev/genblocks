"""The visual half of a brief: what a block should look like, decided before code.

The brief says what the block is for; the plan says how it is expressed. Without
one, the first place a visual decision is taken is the file the builder is already
writing, and a model writing Tailwind reaches for the same accent, the same radius
and the same four cards every time. So the decision is made earlier, by a model
whose only job is that decision, and it is made in closed vocabulary: four
directions, five compositions, four densities, four surface treatments, a named
accent and a typeface from the shelf.

Closed vocabulary is not a template. The directions are criteria, not layouts, and
the builder may deviate when the render asks for it — `rationale` and `signature`
are what keep a plan from being a checklist of adjectives.

The plan is stored with the block (``components.spec``), shown to the builder in
the ask, and read by the judge, which is the only way it can be scored rather than
remembered.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.harness import fonts

# The version stamped on a plan. A stored block says which vocabulary chose it.
VERSION = "design-v1"


class Direction(StrEnum):
    """The temper of the block, not its layout."""

    EDITORIAL = "editorial"
    PRECISION = "precision"
    GRAPHIC = "graphic"
    ARTISANAL = "artisanal"
    INDUSTRIAL = "industrial"


class Composition(StrEnum):
    """How the section is put together at a glance."""

    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    COLUMNAR = "columnar"
    MODULAR = "modular"
    OVERLAY = "overlay"


class Density(StrEnum):
    """How much air the content is given."""

    SPARSE = "sparse"
    MODERATE = "moderate"
    DENSE = "dense"


class Surfaces(StrEnum):
    """How planes are separated: by nothing, by a line, by a box, or by depth."""

    FLAT = "flat"
    BORDERED = "bordered"
    DIVIDED = "divided"
    LAYERED = "layered"


class Accent(StrEnum):
    """The one colour the block may spend attention on.

    Named by Tailwind hue rather than by hex so the builder writes a class a
    visitor can read, and so the palette can be checked against the files. ``neutral``
    is a choice too: a block may make its point with type and space alone.
    """

    NEUTRAL = "neutral"
    RED = "red"
    ORANGE = "orange"
    AMBER = "amber"
    YELLOW = "yellow"
    LIME = "lime"
    GREEN = "green"
    EMERALD = "emerald"
    TEAL = "teal"
    CYAN = "cyan"
    SKY = "sky"
    BLUE = "blue"
    INDIGO = "indigo"
    VIOLET = "violet"
    PURPLE = "purple"
    FUCHSIA = "fuchsia"
    PINK = "pink"
    ROSE = "rose"


DIRECTION_NOTES = {
    Direction.EDITORIAL: (
        "expressive type, asymmetry, a large headline, vertical rhythm and negative "
        "space. For hero sections, portfolios, premium product pages."
    ),
    Direction.PRECISION: (
        "clear hierarchy, controlled density, precise states, well-organised data and "
        "functional controls. For pricing, dashboards, settings, forms, tables."
    ),
    Direction.GRAPHIC: (
        "strong contrast, geometry, an unconventional composition, graphic type and "
        "colour used on purpose. For launches, banners, calls to action."
    ),
    Direction.ARTISANAL: (
        "materials, subtle texture, photography, natural tones and details that feel "
        "physical. For commerce, lifestyle, food, hospitality."
    ),
    Direction.INDUSTRIAL: (
        "exposed structure and hard edges: monospace labels, rules instead of boxes, "
        "utility over polish, a palette that looks like a material. For developer "
        "tools, hardware, events, and brands that want to look unpolished on purpose."
    ),
}

COMPOSITION_NOTES = {
    Composition.SYMMETRIC: "a centred axis, used when the content really is equal.",
    Composition.ASYMMETRIC: "weight on one side; a deliberate imbalance.",
    Composition.COLUMNAR: "a grid of columns the eye follows.",
    Composition.MODULAR: "blocks of different sizes that share an edge.",
    Composition.OVERLAY: "one plane over another: type over image, card over ground.",
}

DENSITY_NOTES = {
    Density.SPARSE: "few elements, a lot of air; the section is a statement.",
    Density.MODERATE: "a working section: enough air to read, enough content to use.",
    Density.DENSE: "many small decisions; for tables, dashboards, specifications.",
}

SURFACE_NOTES = {
    Surfaces.FLAT: "no borders and no shadow; separation comes from space and type.",
    Surfaces.BORDERED: "hairlines do the separating; boxes stay square to the page.",
    Surfaces.DIVIDED: "rules between rows and sections rather than around them.",
    Surfaces.LAYERED: "one raised plane, with a shadow that means hierarchy.",
}

# How much of the shelf the planner is shown. The names, not the packages: the
# package is resolved here, so a typo in a model answer cannot become an import.
SHELF = fonts.FAMILIES


class DesignPlan(BaseModel):
    """The decision the implementation follows, compact enough to be read once."""

    model_config = ConfigDict(extra="forbid")

    direction: Direction
    composition: Composition
    # The order attention should travel in: first thing named wins. Two to five
    # stops, because a hierarchy with one stop is a single element and six is a
    # list nobody follows.
    hierarchy: list[str] = Field(min_length=2, max_length=5)
    display_font: str
    body_font: str
    # Only when the content has figures, code or labels that should align.
    mono_font: str | None = None
    accent: Accent
    # Why this colour belongs to this subject. The point of the field is that a
    # default cannot fill it.
    accent_reason: str = Field(min_length=8, max_length=200)
    surfaces: Surfaces
    density: Density
    # The one decision that gives the block character, in a phrase.
    signature: str = Field(min_length=8, max_length=160)
    # What this particular direction must not become. Empty is allowed.
    avoid: list[str] = Field(default_factory=list, max_length=4)
    # Why this direction, and how it differs from what the registry already has.
    rationale: str = Field(min_length=8, max_length=320)

    @field_validator("display_font", "body_font", "mono_font")
    @classmethod
    def _on_the_shelf(cls, value: str | None) -> str | None:
        if value is None:
            return None

        found = family_for(value)
        if found is None:
            raise ValueError(f"{value!r} is not a family on the type shelf.")

        # The canonical spelling, so the plan renders the name the shelf uses.
        return found.family

    @field_validator("avoid")
    @classmethod
    def _short_phrases(cls, value: list[str]) -> list[str]:
        return [one.strip() for one in value if one.strip()]


def family_for(name: str) -> fonts.Family | None:
    """The shelf entry a family name names, matched without case."""

    for family in SHELF:
        if family.family.casefold() == name.strip().casefold():
            return family

    return None


def as_dict(plan: DesignPlan) -> dict:
    """The plan as the block stores it: decisions, and the packages they resolve to.

    The package is what the builder imports and the visitor installs, so the record
    keeps both: the name a reader recognises and the install line that made it real.
    """
    return {
        "version": VERSION,
        "direction": plan.direction.value,
        "composition": plan.composition.value,
        "hierarchy": list(plan.hierarchy),
        "typography": {
            "display": _font(plan.display_font),
            "body": _font(plan.body_font),
            "mono": _font(plan.mono_font) if plan.mono_font else None,
        },
        "accent": plan.accent.value,
        "accent_reason": plan.accent_reason,
        "surfaces": plan.surfaces.value,
        "density": plan.density.value,
        "signature": plan.signature,
        "avoid": list(plan.avoid),
        "rationale": plan.rationale,
    }


def _font(family: str) -> dict:
    found = family_for(family)
    if found is None:  # pragma: no cover - the validator has already refused it
        raise ValueError(f"{family!r} is not a family on the type shelf.")

    return {"family": found.family, "package": found.package}


def render(plan: dict | None) -> str:
    """The plan as the builder and the judge read it: one line per decision."""
    if not plan:
        return "No design plan was filed for this block."

    typography = plan.get("typography") or {}
    display = typography.get("display") or {}
    body = typography.get("body") or {}
    mono = typography.get("mono") or {}
    fonts_said = f"display {display.get('family', '?')}, body {body.get('family', '?')}" + (
        f", mono {mono.get('family')}" if mono else ", no mono"
    )
    hierarchy = " > ".join(plan.get("hierarchy") or []) or "not stated"
    avoid = "; ".join(plan.get("avoid") or []) or "none named"
    direction = f"Direction: {plan.get('direction', '?')}"
    if plan.get("rationale"):
        direction += f" — {plan['rationale']}"

    return "\n".join(
        [
            direction,
            f"Composition: {plan.get('composition', '?')}",
            f"Hierarchy: {hierarchy}",
            f"Type: {fonts_said}",
            (
                f"Colour: accent {plan.get('accent', '?')} "
                f"({plan.get('accent_reason', '')}); surfaces {plan.get('surfaces', '?')}"
            ),
            f"Density: {plan.get('density', '?')}",
            f"Signature: {plan.get('signature', '')}",
            f"Avoid: {avoid}",
        ]
    )


def vocabulary() -> str:
    """The closed choices, for the planner's prompt.

    Read from the enums and the notes rather than written twice: a direction that
    exists in the schema and not in the prompt is a direction the model never picks.
    """
    blocks = []
    for title, notes in (
        ("Direction", DIRECTION_NOTES),
        ("Composition", COMPOSITION_NOTES),
        ("Density", DENSITY_NOTES),
        ("Surfaces", SURFACE_NOTES),
    ):
        lines = [f"- {one.value}: {said}" for one, said in notes.items()]
        blocks.append(f"{title}:\n" + "\n".join(lines))

    accents = ", ".join(accent.value for accent in Accent)
    blocks.append(f"Accent (one, by name): {accents}.")

    return "\n\n".join(blocks)


def shelf() -> str:
    """The type shelf as the planner chooses from it: family names by group."""
    lines = []
    for group in fonts.GROUPS:
        names = ", ".join(one.family for one in SHELF if one.group == group.slug)
        lines.append(f"- {group.title}: {names}")

    return "\n".join(lines)


def examples() -> str:
    """One plan that decides something, and one that decides nothing.

    Worked examples teach a vocabulary faster than a list of rules, and the second
    one is the more useful of the two: it looks like a plan and cannot be
    implemented, which is the failure the fields exist to make impossible.
    """
    return """\
Two plans for the same brief — a pricing section for a self-hosted analytics tool,
three tiers, annual toggle.

A plan that decides:
- direction: precision; composition: columnar; density: moderate
- hierarchy: annual toggle > recommended tier > price > what each tier includes >
  billing note
- type: display Geist 500, body Inter, mono JetBrains Mono for the figures
- accent: sky, because the product measures traffic and sky is the colour its own
  charts use; surfaces: divided, so the only box on the page is the recommended tier
- signature: the recommended tier is marked by a rule and a filled header, not by a
  scale effect or a badge
- avoid: four identical cards, a toggle dressed as a pill, gradients
- rationale: the registry already has two precision pricings, but neither is
  columnar and neither is blue, so this differs on composition and accent

A plan that decides nothing:
- direction: modern; composition: clean; density: balanced
- hierarchy: title, plans, details
- type: a nice sans; accent: a tasteful colour; surfaces: subtle
- signature: smooth animations
- rationale: it looks elegant

What goes wrong with the second: none of it can be implemented or checked. "Clean",
"balanced" and "subtle" are not instructions, so the builder falls back to its own
default — one family, one radius, a green accent — and the judge cannot tell a
decision from a default. Every field must name something you can see in the render
or read in the file, and the accent must say which colour, not what kind of colour.

Copy the shape of that decision, not its answers. Sky, Geist and Inter are there
because that brief was about traffic; a different brief needs different ones, and a
registry of identical plans is the same failure as a registry of identical blocks.
"""
