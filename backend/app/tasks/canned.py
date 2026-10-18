"""The stand-ins for what the pipeline does not do yet.

A task has to run end to end long before every phase exists, so this module
supplies what is missing: the **spec** (which type a brief is filed under) and the
**judge** (what an attempt scores). Both are fixed, so a run is reproducible and
free, and neither pretends to be more than it is:

- ``rubric_version`` is :data:`VERSION`, so a stand-in score can never be mistaken
  for a calibrated one.
- The spec's ``spec`` block says ``"source": "canned"`` on its own face.

What is *not* here anymore is the block itself: since Fase 7 the code is written
by the generator and checked by the sandbox (``app/harness``), and the attempt
credits the model that wrote it.

The seeded vault (``app.seed.vault``) is a different thing: planted by hand to
show what a finished run looks like, with ``seed-v0`` as its rubric version.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.categories import service as categories_service

# The version both the spec and the rubric are stamped with. Not a rubric
# version in the real sense: nothing was measured.
VERSION = "canned-v1"

# The type a run files its block under, until the spec phase reads the taxonomy.
# It has to exist; the seed plants it, and a missing one fails the task with a
# message that says so.
CATEGORY_SLUG = "hero"

# What the stand-in judge wrote, already above every threshold. Every run gets
# the same numbers: the point of a stand-in is that it does not vary.
SCORES = {
    "render": 91,
    "accessibility": 89,
    "visual": 84,
    "copy": 86,
    "novelty": 79,
    "compliance": 93,
}

# How much of the brief survives into the title and the card's one-liner.
TITLE_LIMIT = 60
DESCRIPTION_LIMIT = 200
# Where a title prefers to stop, in the order it reads best. A brief is usually
# "the thing, then the details", and stopping at the comma gives a phrase where
# cutting at a character count gives a sentence that ends mid-way.
TITLE_BREAKS = (",", ";", ":", ".")
# Below this, a break is not a clause worth being a title on its own.
TITLE_MIN_CLAUSE = 12


class CategoryNotSeeded(Exception):
    """The spec names a category the taxonomy does not have.

    A development database without its taxonomy is a setup mistake, and it is
    worth failing the task over it loudly instead of filing the block nowhere.
    """


@dataclass(frozen=True)
class CannedSpec:
    """What the spec phase decided to build, ready for the phases after it."""

    category_id: uuid.UUID
    category_slug: str
    title: str
    description: str
    spec: dict


async def build_spec(session: AsyncSession, *, brief: str) -> CannedSpec:
    """Resolve the stand-in spec against the taxonomy.

    The only thing that depends on what the caller asked for is the copy that
    carries the brief; the type and the guide are the same for every run.
    """
    category = await categories_service.get_category_by_slug(session, slug=CATEGORY_SLUG)
    if category is None:
        raise CategoryNotSeeded(
            f"The taxonomy has no {CATEGORY_SLUG!r} category. "
            "Run `python -m app.categories.seed` first."
        )

    return CannedSpec(
        category_id=category.id,
        category_slug=category.slug,
        title=title_for(brief),
        description=description_for(brief),
        spec={"version": VERSION, "source": "canned", "category": category.slug},
    )


def title_for(brief: str) -> str:
    """The block's title: the brief's first clause, cut to fit if it needs it."""
    clause = _first_clause(_single_line(brief))
    if len(clause) <= TITLE_LIMIT:
        return clause

    head = clause[:TITLE_LIMIT].rsplit(" ", 1)[0]
    # A single word longer than the limit has no boundary to cut at.
    return head or clause[:TITLE_LIMIT]


def description_for(brief: str) -> str:
    """The card's one-liner: the brief as it was given, trimmed to fit."""
    single_line = _single_line(brief)
    if len(single_line) <= DESCRIPTION_LIMIT:
        return single_line

    return f"{single_line[:DESCRIPTION_LIMIT].rsplit(' ', 1)[0]}…"


def headline_score(scores: dict[str, int]) -> int:
    """The judge's headline number: the flat mean of its rubric scores."""
    return round(sum(scores.values()) / len(scores))


def _first_clause(value: str) -> str:
    """The head of a brief, up to the first place it breaks.

    A clause too short to stand on its own is not a title, so the search moves on
    and a brief that never breaks keeps all of itself.
    """
    for separator in TITLE_BREAKS:
        head, found, _ = value.partition(separator)
        if found and len(head) >= TITLE_MIN_CLAUSE:
            return head

    return value


def _single_line(value: str) -> str:
    """Collapse a brief's whitespace, so nothing downstream inherits its breaks."""
    return " ".join(value.split())
