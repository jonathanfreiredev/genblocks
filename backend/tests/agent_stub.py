"""A model that answers from a script, so the agent can be tested without one.

The graph, the tools, the checkpointer and the stream are all the code that
ships. What is fake is the model, and it is fake in the one way that matters: it
streams, chunk by chunk, because a model that answers whole never exercises the
path between a token and a dialog.
"""

import json
from collections.abc import Iterator
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field


class ScriptedChatModel(BaseChatModel):
    """What a model says, written down in advance.

    ``turns`` is one entry per call the graph makes, so a script that searches
    and then queues has three turns: the search, the task, and the sentence that
    closes the conversation. The last turn is repeated if the graph asks again —
    a model that runs out of script should not fail the test, it should stop
    saying new things.
    """

    turns: list[AIMessage]
    """The script, one message per model call, in order."""

    index: int = 0
    """How far through the script the conversation has got."""

    pieces: int = 4
    """How many chunks a turn's words are cut into, so streaming is visible."""

    seen: list[list[BaseMessage]] = Field(default_factory=list)
    """What the graph asked with, once per call: the history a script ignores but
    a test can read to see whether the conversation was carried on."""

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        # Binding a schema is how a real model is told what it may call. Here the
        # calls are already written down, so there is nothing to bind.
        return self

    def _next(self) -> AIMessage:
        message = self.turns[self.index]
        if self.index < len(self.turns) - 1:
            self.index += 1

        return message

    def _chunks(self) -> Iterator[AIMessageChunk]:
        message = self._next()

        if message.tool_calls:
            for index, call in enumerate(message.tool_calls):
                yield AIMessageChunk(
                    content="",
                    id=message.id,
                    tool_call_chunks=[
                        {
                            "name": call["name"],
                            "args": json.dumps(call["args"]),
                            "id": call["id"],
                            "index": index,
                        }
                    ],
                )
            return

        text = message.content if isinstance(message.content, str) else ""
        size = max(1, len(text) // self.pieces)
        for start in range(0, len(text), size):
            yield AIMessageChunk(content=text[start : start + size], id=message.id)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Any = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        # A whole answer, for a caller that is not streaming: the graph streams,
        # a single call does not, and both have to work with one script.
        return ChatResult(generations=[ChatGeneration(message=self._next())])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Any = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        self.seen.append(list(messages))

        for chunk in self._chunks():
            if run_manager is not None and chunk.content:
                run_manager.on_llm_new_token(chunk.content)

            yield ChatGenerationChunk(message=chunk)
