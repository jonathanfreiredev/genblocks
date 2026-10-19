"""What a brief is going to be: the type it is filed under, and its copy.

This is the first place a model decides something that is not the artifact: which
type of block the brief is. Until Fase 10 it was a constant, and every block in
the registry was a hero; a taxonomy nothing reads is a dropdown nobody opens.

The decision is retrieval and a model together, because neither answers alone.
Retrieval says which blocks already look like this brief, and their types are
evidence; the taxonomy says which types exist, and only it can say what they
mean. A model asked to choose from a list is not a model inventing a category —
and an answer outside the list is a refusal, not a new type.

What stays deterministic is the copy: the title is the brief's first clause and
the description is the brief itself. Those were never a judgement call.
"""

import uuid
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.categories import service as categories_service
from app.categories.models import Category
from app.components import service as components_service
from app.components.models import Component
from app.settings import settings
from app.vectors import service as vectors

# The version the spec is stamped with. Not a rubric in the judge's sense —
# nothing here is measured — but the record should say which spec wrote it.
VERSION = "spec-v1"

# The type a brief falls back to when nothing in the registry resembles it. It has
# to exist: the seed plants it, and a missing one fails the task with a message
# that says so.
FALLBACK_SLUG = "hero"

COMPONENT_KIND = "component"

# How many published blocks are shown to the model as evidence of how the
# registry files things. Fewer than a handful is not a pattern; more is a prompt
# that costs more than the decision.
EXEMPLARS = 5

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
    """The taxonomy has no types to file a block under.

    A development database without its taxonomy is a setup mistake, and it is
    worth failing the task over it loudly instead of filing the block nowhere.
    """


class SpecUnavailable(Exception):
    """There is no model to choose the type with."""


class UnreadableCategory(Exception):
    """The model answered with a type the taxonomy does not have."""


class CategoryAnswer(BaseModel):
    """The shape the model's answer takes: one slug, and why."""

    category: str
    reason: str


@dataclass(frozen=True)
class BlockSpec:
    """What the spec phase decided to build, ready for the phases after it."""

    category_id: uuid.UUID
    category_slug: str
    title: str
    description: str
    spec: dict


def spec_model() -> BaseChatModel:
    """The model that files the brief, or a refusal saying what is missing."""
    if not settings.openai_api_key:
        raise SpecUnavailable("The spec has no model configured: set OPENAI_API_KEY on the API.")

    return ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key)


def as_spec(model: BaseChatModel | None = None) -> Runnable:
    """A model bound to the shape its answer has to take."""
    return (model or spec_model()).with_structured_output(CategoryAnswer, method="function_calling")


async def build_spec(
    session,
    *,
    brief: str,
    model: Runnable | None = None,
) -> BlockSpec:
    """Decide the type of block a brief asks for, and its copy.

    ``model`` is how a test answers with a script instead of paying for a
    completion; production passes nothing and gets the configured one.
    """
    types = [
        category
        for category in await categories_service.list_categories(session, kind=COMPONENT_KIND)
        if category.level == 2
    ]
    if not types:
        raise CategoryNotSeeded(
            "The taxonomy has no types of block. Run `python -m app.categories.seed` first."
        )

    exemplars, filed = await _exemplars(session, brief=brief)
    answer: CategoryAnswer = await (model or as_spec()).ainvoke(
        [
            SystemMessage(_frame(types)),
            HumanMessage(_about(brief=brief, exemplars=exemplars, filed=filed)),
        ]
    )

    chosen = next((one for one in types if one.slug == answer.category), None)
    if chosen is None:
        raise UnreadableCategory(
            f"The spec answered {answer.category!r}, which is not a type of block. "
            f"The taxonomy has: {', '.join(one.slug for one in types)}."
        )

    return BlockSpec(
        category_id=chosen.id,
        category_slug=chosen.slug,
        title=title_for(brief),
        description=description_for(brief),
        spec={
            "version": VERSION,
            "source": "rag",
            "category": chosen.slug,
            "reason": answer.reason,
            "exemplars": [one.slug for one in exemplars],
        },
    )


async def _exemplars(session, *, brief: str) -> tuple[list[Component], dict[uuid.UUID, str]]:
    """Published blocks near this brief, and the type each is filed under.

    Retrieval failing is not a reason to refuse the brief: the model still has the
    taxonomy and the copy, and the type it chooses is validated either way.
    """
    matches = await vectors.find_components(brief, limit=EXEMPLARS)
    if not matches:
        return [], {}

    found = await components_service.by_ids(session, ids=[one.id for one in matches])
    categories = await categories_service.list_categories(session, kind=COMPONENT_KIND)
    by_id = {one.id: one.slug for one in categories}

    return found, by_id


def _frame(types: list[Category]) -> str:
    """The half of the prompt that does not change: who files, and from what list."""
    listed = "\n".join(f"- {one.slug}: {one.name}" for one in types)

    return f"""\
You file blocks for GenBlocks, a registry of UI blocks. A person describes a block;
your job is to say which of the registry's types it belongs to.

The types, and only these:
{listed}

Answer with one slug from that list and one sentence saying why. Choose by what the
block is, not by the section of a page somebody named: a hero and a call to action
are both bands at the top, and only one of them is a hero.
"""


def _about(*, brief: str, exemplars: list[Component], filed: dict[uuid.UUID, str]) -> str:
    """The half of the prompt that changes: the brief, and what it resembles."""
    said = ["The brief:", "", brief, ""]

    if exemplars:
        said += ["Blocks the registry already holds that read like this one:", ""]
        said += [
            f"- {one.title} (filed under {filed.get(one.category_id, 'unknown')}): "
            f"{one.description}"
            for one in exemplars
        ]
        said += ["", "Their type is evidence, not an answer: say which type this is."]
    else:
        said += [
            "The registry holds nothing close to this brief, so the list above is "
            "all there is to go on."
        ]

    return "\n".join(said)


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
