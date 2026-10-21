"""The conversation, over HTTP.

One stream for the conversation and one endpoint for the consequence: the dialog
sends what was said, watches the agent prepare a brief, and queues it only when
the person presses the button. It is a first-party door like the rest of this API
— the caller's own token, and a task that belongs to them before it exists.

Server-sent events rather than a websocket: the traffic goes one way, there is no
session to keep open, and the stream ends on its own when the turn does. It is
also the only way to say something after the response has started, which is where
a failure mid-turn happens.
"""

from collections.abc import AsyncIterator
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import build_agent
from app.agent.model import get_chat_model
from app.agent.schemas import ChatRequest, ConfirmRequest, Proposals, Suggestions
from app.agent.stream import Event, TurnReader, encode
from app.agent.tools import build_tools
from app.authz.dependencies import get_first_party_user
from app.components.planning import ImageConfirmationRequired
from app.db.session import get_async_db_session
from app.moderation.service import BriefRejected
from app.notifications import email as notifications
from app.tasks.limits import MonthlyQuotaReached
from app.tasks.models import Task
from app.tasks.schemas import TaskRead
from app.tasks.service import enqueue_task
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
    proposals = Proposals()
    agent = build_agent(
        model=model,
        tools=build_tools(
            caller=user,
            queued=queued,
            suggested=suggested,
            proposals=proposals,
        ),
    )

    # The checkpointer is one per process and the thread id comes from the
    # browser, so the user is part of the key: a guessed thread id finds nothing
    # rather than someone else's turns.
    thread = f"{user.id}:{payload.thread_id}"
    config = {"configurable": {"thread_id": thread}}

    async def frames() -> AsyncIterator[str]:
        reader = TurnReader(queued=queued, suggested=suggested, proposals=proposals)

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


@agent_router.post(
    "/confirm",
    response_model=TaskRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def confirm_brief(
    payload: ConfirmRequest,
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    response: Response,
) -> TaskRead:
    """Queue a brief the person has confirmed, and return its task.

    This is the only path from the conversation to a task. The model prepares a
    brief; this endpoint is called by the button the person presses. A prompt
    injection in a registry result can therefore change what the assistant says,
    but it cannot spend a month's quota or start a run by itself.

    202 for a new task, 200 for a brief the registry already answered.
    """
    try:
        task = await enqueue_task(
            session,
            brief=payload.brief,
            created_by=user.id,
            fresh=payload.force,
        )
    except MonthlyQuotaReached as reached:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(reached),
        ) from reached
    except BriefRejected as refused:
        await notifications.policy_event(
            kind="brief_rejected",
            reason=str(refused),
            brief=payload.brief,
            user_id=user.id,
            user_email=user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(refused),
        ) from refused
    except ImageConfirmationRequired as confirmation:
        await notifications.policy_event(
            kind="image_people",
            reason=confirmation.reason,
            brief=payload.brief,
            user_id=user.id,
            user_email=user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(confirmation),
                "proposed_brief": confirmation.proposed_brief,
            },
        ) from confirmation

    if task.cached:
        response.status_code = status.HTTP_200_OK

    return TaskRead.model_validate(task)
