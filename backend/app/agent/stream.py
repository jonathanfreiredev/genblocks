"""One turn of the graph, as the frames the dialog reads.

The graph speaks in messages; the dialog wants five things: the words as they
arrive, the tools being reached for, the briefs awaiting confirmation, the things
worth showing, and an end. This module is that translation and nothing else. It
keeps no history of the conversation — only of what it has already said in this
turn, so a chunk that repeats does not become a second event.
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from app.agent.schemas import Proposals, Suggestions
from app.tasks.models import Task
from app.tasks.schemas import TaskRead


@dataclass(frozen=True, slots=True)
class Event:
    """One server-sent event: a name, and a body that is already JSON."""

    name: str
    data: dict[str, Any]


def encode(event: Event) -> str:
    """The event as it goes on the wire.

    One ``data`` line, never several: every body here is a single JSON object,
    and a reader that only has to join lines is a reader that cannot mis-join
    them.
    """
    return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"


@dataclass
class TurnReader:
    """Reads the graph's stream and says what the dialog should show.

    ``proposals`` is the list the tools append to. Reading it here rather than
    parsing the tool's message is what lets the confirmation card reach the dialog
    the moment the brief is ready, and in the order it happened. ``suggested``
    works the same way for the blocks and pictures the agent found: the tools keep
    them, the stream sends the ones the dialog has not been told about.
    """

    queued: list[Task]
    suggested: Suggestions
    proposals: Proposals = field(default_factory=Proposals)
    _announced: set[str] = field(default_factory=set)
    _shown: set[uuid.UUID] = field(default_factory=set)
    _surfaced: set[tuple[str, uuid.UUID]] = field(default_factory=set)
    _proposed: set[tuple] = field(default_factory=set)

    def read(self, chunk: Any) -> list[Event]:
        """The events one chunk of the stream becomes."""
        if isinstance(chunk, ToolMessage):
            return [
                Event("tool", {"name": chunk.name, "state": "finished"}),
                *self._tasks(),
                *self._suggestions(),
                *self._proposals(),
            ]

        if isinstance(chunk, AIMessage):
            return [*self._tools(chunk), *self._words(chunk)]

        return []

    def close(self) -> list[Event]:
        """The events that end a turn, whatever else the stream did."""
        return [*self._tasks(), *self._suggestions(), *self._proposals(), Event("done", {})]

    def _tools(self, message: AIMessage) -> list[Event]:
        """The tool calls this chunk is the first to name.

        A streamed call arrives in pieces: the name in the first chunk and the
        arguments over the ones that follow, and only the last piece carries the
        call whole. The pieces are what a call is announced from; a message that
        arrives assembled — a model that does not stream — is read the same way,
        from the other list.
        """
        started = []

        for piece in getattr(message, "tool_call_chunks", None) or []:
            name = piece.get("name")
            key = piece.get("id") or f"piece:{piece.get('index')}"
            if name and key not in self._announced:
                self._announced.add(key)
                started.append(Event("tool", {"name": name, "state": "started"}))

        for call in message.tool_calls:
            # A piece whose arguments are still incomplete arrives here nameless
            # or id-less. It is not a call the dialog can be told about, and the
            # piece that named it already was.
            key = call["id"] or f"call:{call['name']}"
            if not call["name"] or key in self._announced:
                continue
            self._announced.add(key)
            started.append(Event("tool", {"name": call["name"], "state": "started"}))

        return started

    def _words(self, message: AIMessage) -> list[Event]:
        text = _text(message.content)
        return [Event("token", {"text": text})] if text else []

    def _tasks(self) -> list[Event]:
        """What the conversation has queued and the dialog has not been told."""
        queued = []
        for task in self.queued:
            if task.id in self._shown:
                continue

            self._shown.add(task.id)
            queued.append(Event("task", TaskRead.model_validate(task).model_dump(mode="json")))

        return queued

    def _suggestions(self) -> list[Event]:
        """What the agent found and the dialog has not been shown yet."""
        fresh = [
            one.as_body()
            for one in self.suggested.items
            if (one.kind, one.id) not in self._surfaced
        ]
        for one in self.suggested.items:
            self._surfaced.add((one.kind, one.id))

        return [Event("suggestions", {"items": fresh})] if fresh else []

    def _proposals(self) -> list[Event]:
        """Tasks waiting for the person's confirmation, each said once."""
        fresh = [one.as_body() for one in self.proposals.items if one.key not in self._proposed]

        for one in self.proposals.items:
            self._proposed.add(one.key)

        return [Event("proposal", one) for one in fresh]


def _text(content: Any) -> str:
    """A message's words, whether it carries them as a string or as blocks."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(block.get("text", "") for block in content if isinstance(block, dict))

    return ""
