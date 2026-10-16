"""The canned stand-in for the generation pipeline.

A task has to run end to end long before the harness (Fase 7) and the judge
(Fase 8) exist, so this module supplies what they will supply: a spec, a block
and a set of scores. All three are fixed, so a run is reproducible and free, and
none of them pretends to be more than it is:

- ``model`` is left empty on the attempt. Nothing generated that code, and the
  panel's job is to say what produced an artifact, not to flatter the pipeline.
- ``rubric_version`` is :data:`VERSION`, so a canned score can never be mistaken
  for a calibrated one.
- The block says on its own face that it is a placeholder.

The seeded vault (``app.seed.vault``) is a different thing: planted by hand to
show what a finished run looks like, with ``seed-v0`` as its rubric version.
"""

import json
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.categories import service as categories_service

# The version both the spec and the rubric are stamped with. Not a rubric
# version in the real sense: nothing was measured.
VERSION = "canned-v1"

# The type the canned block is filed under. It has to exist in the taxonomy; the
# seed plants it, and a missing one fails the task with a message that says so.
CATEGORY_SLUG = "hero"

# What the canned judge wrote, already above every threshold. Every run gets the
# same numbers: the point of a stand-in is that it does not vary.
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

# Generic Tailwind, no design tokens of this application's own: a block is meant
# to be copied into someone else's project and still render (PLAN.md, decision
# 24). ``__BRIEF__`` is replaced with the brief as a JavaScript string literal.
CODE_TEMPLATE = """export function CannedBlock() {
  const brief =
    __BRIEF__;

  return (
    <section
      aria-labelledby="canned-block-title"
      className="bg-white px-6 py-24 text-neutral-900 sm:px-8"
    >
      <div className="mx-auto max-w-3xl">
        <p className="font-mono text-xs font-bold uppercase tracking-[0.06em] text-neutral-500">
          Placeholder · no generator ran
        </p>

        <h1
          id="canned-block-title"
          className="mt-8 font-sans text-4xl leading-[1.1] tracking-[-0.02em] sm:text-5xl"
        >
          {brief}
        </h1>

        <p className="mt-6 max-w-[60ch] text-base leading-[1.55] text-neutral-600">
          This block is a stand-in. The harness that builds real blocks, and the judge
          that scores them, arrive with the rest of the pipeline.
        </p>
      </div>
    </section>
  );
}
"""


class CategoryNotSeeded(Exception):
    """The canned spec names a category the taxonomy does not have.

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
    code: str
    spec: dict


async def build_spec(session: AsyncSession, *, brief: str) -> CannedSpec:
    """Resolve the canned spec against the taxonomy.

    The only thing that depends on what the caller asked for is the copy that
    carries the brief; the type, the code and the scores are the same for every
    run.
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
        code=code_for(brief),
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


def code_for(brief: str) -> str:
    """The canned block, with the brief written into it as a string literal.

    ``json.dumps`` rather than an f-string: a brief can hold the quotes, the
    braces and the newlines that would otherwise break the file it is pasted
    into.
    """
    return CODE_TEMPLATE.replace("__BRIEF__", json.dumps(brief))


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
