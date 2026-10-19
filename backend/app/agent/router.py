"""The conversation, over HTTP.

One endpoint and one stream: the dialog sends what was said and reads back what
the agent does about it as it does it. It is a first-party door like the rest of
this API — the caller's own token, and a task that belongs to them before it
exists.

Server-sent events rather than a websocket: the traffic goes one way, there is no
session to keep open, and the stream ends on its own when the turn does. It is
also the only way to say something after the response has started, which is where
a failure mid-turn happens.
"""

from collections.abc import AsyncIterator
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.agent.graph import build_agent
from app.agent.model import get_chat_model
from app.agent.schemas import ChatRequest, Suggestions
from app.agent.stream import Event, TurnReader, encode
from app.agent.tools import build_tools
from app.authz.dependencies import get_first_party_user
from app.tasks.models import Task
from app.users.models import User

agent_router = APIRouter(prefix="/agent", tags=["agent"])

logger = structlog.get_logger("app.agent.router")

# What the dialog is told when a turn dies in flight. The 200 went out with the
# stream, so the stream is the only place left to say it.
FAILURE = "The agent stopped mid-answer. Nothing was queued."


@agent_router.post("/chat")
async def chat(
    payload: ChatRequest,
    user: Annotated[User, Depends(get_first_party_user)],
    model: Annotated[BaseChatModel, Depends(get_chat_model)],
) -> StreamingResponse:
    """Take one turn of the conversation and stream everything it does.

    The tools are built per request because the caller is bound into them: one
    conversation queues work for one user and cannot be talked into queueing it
    for another. The graph is built with them, so what a turn can reach is
    decided here and not by the model.
    """
    queued: list[Task] = []
    suggested = Suggestions()
    agent = build_agent(
        model=model,
        tools=build_tools(caller=user, queued=queued, suggested=suggested),
    )

    # The checkpointer is one per process and the thread id comes from the
    # browser, so the user is part of the key: a guessed thread id finds nothing
    # rather than someone else's turns.
    thread = f"{user.id}:{payload.thread_id}"
    config = {"configurable": {"thread_id": thread}}

    async def frames() -> AsyncIterator[str]:
        reader = TurnReader(queued=queued, suggested=suggested)

        try:
            async for chunk, _metadata in agent.astream(
                {"messages": [HumanMessage(payload.message)]},
                config,
                stream_mode="messages",
            ):
                for event in reader.read(chunk):
                    yield encode(event)
        except Exception as error:  # noqa: BLE001 - the stream owes the dialog an ending
            logger.warning("agent turn failed", thread=thread, error=str(error))
            yield encode(Event("error", {"message": FAILURE}))

        for event in reader.close():
            yield encode(event)

    return StreamingResponse(
        frames(),
        media_type="text/event-stream",
        headers={
            # Nothing between here and the browser may hold the frames back or
            # rewrite them: a stream that arrives whole is not a stream.
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
