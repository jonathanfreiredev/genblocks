"""What the conversation shows besides words.

A suggestion is a thing the agent found while working — a block that may already
answer the brief, a picture the library already has — that the person can open.
It travels as its own event rather than inside the agent's prose because it is not
prose: the dialog draws it as a card, and a card has an id to click and a picture
to show, neither of which survives being read out.

The list is deduplicated and bounded here rather than in the dialog: a model that
searches three times in one turn should not fill the conversation with the same
five rows.
"""

import uuid
from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.tasks.schemas import Brief

# What one message may say and how a conversation is named. The same bounds are
# enforced by the dialog, and these are the ones the API acts on.
MESSAGE_MAX_LENGTH = 4000
THREAD_MIN_LENGTH = 8
THREAD_MAX_LENGTH = 100

Message = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MESSAGE_MAX_LENGTH),
]

ThreadId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=THREAD_MIN_LENGTH, max_length=THREAD_MAX_LENGTH
    ),
]

# How many suggestions one conversation may collect. Enough to show that a brief
# has near neighbours, few enough that the rail stays a rail.
LIMIT = 8

Kind = Literal["component", "image"]


@dataclass(frozen=True, slots=True)
class Suggestion:
    """One thing worth showing, as the dialog reads it."""

    kind: Kind
    id: uuid.UUID
    title: str
    detail: str
    # The readable address of the thing; the id is only the fallback.
    slug: str | None = None
    # Cloudinary public id of what to show: a block's render, a picture itself.
    # None when there is nothing to show, and the card falls back to its words.
    path: str | None = None
    width: int | None = None
    height: int | None = None

    def as_body(self) -> dict:
        return {
            "kind": self.kind,
            "id": str(self.id),
            "slug": self.slug,
            "title": self.title,
            "detail": self.detail,
            "path": self.path,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True, slots=True)
class Proposal:
    """A brief the agent prepared, waiting for the person to confirm it.

    The model writes the brief; the person owns the consequence. Keeping the two
    apart is what makes prompt injection into a search result unable to spend
    somebody's quota or start a run.
    """

    brief: str
    force: bool = False

    def as_body(self) -> dict:
        return {"brief": self.brief, "force": self.force}


@dataclass
class Proposals:
    """The briefs one turn prepared, deduplicated by their exact words."""

    items: list[Proposal] = field(default_factory=list)

    def add(self, proposal: Proposal) -> bool:
        if any(one.brief == proposal.brief for one in self.items):
            return False

        self.items.append(proposal)
        return True


@dataclass
class Suggestions:
    """What the agent has put in front of the person, and what it already said.

    The tools add; the stream reads what is new. Keeping the "already said" half
    here is what makes a turn that searches twice show five cards rather than ten.
    """

    items: list[Suggestion] = field(default_factory=list)
    _seen: set[tuple[str, uuid.UUID]] = field(default_factory=set)

    def add(self, suggestion: Suggestion) -> bool:
        """Keep one suggestion, unless it is a repeat or the list is full."""
        key = (suggestion.kind, suggestion.id)

        if key in self._seen or len(self.items) >= LIMIT:
            return False

        self._seen.add(key)
        self.items.append(suggestion)

        return True


class ChatRequest(BaseModel):
    """One turn: what the person said, and which conversation it belongs to."""

    message: Message
    thread_id: ThreadId


class ConfirmRequest(BaseModel):
    """A prepared brief the person pressed "queue" on.

    ``force`` is the same escape hatch the conversation offers: the registry has
    something close, and the person has said they want their own version anyway.
    """

    brief: Brief
    force: bool = False
