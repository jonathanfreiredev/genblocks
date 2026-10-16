"""The caller's own background tasks.

A task belongs to the user who started it, so every read here is scoped to the
caller: someone else's task answers exactly as an unknown id does, with nothing
to tell the two apart.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.dependencies import get_first_party_user
from app.db.session import get_async_db_session
from app.generations.schemas import GenerationRead
from app.generations.service import list_generations
from app.pagination import OffsetPage
from app.tasks.schemas import TaskDetailRead, TaskListQuery, TaskRead
from app.tasks.service import get_task, list_tasks
from app.users.models import User

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get("", response_model=OffsetPage[TaskRead])
async def read_tasks(
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[TaskListQuery, Query()],
) -> OffsetPage[TaskRead]:
    """List the caller's tasks, newest first unless ``sort`` says otherwise.

    ``status`` narrows to one lifecycle state. No task another user started ever
    appears in the result, whatever the filters say.
    """
    tasks, total = await list_tasks(
        session, params=params, created_by=user.id, status=params.status
    )

    return OffsetPage(
        items=[TaskRead.model_validate(task) for task in tasks],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@tasks_router.get("/{task_id}", response_model=TaskDetailRead)
async def read_task(
    task_id: uuid.UUID,
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> TaskDetailRead:
    """Return one of the caller's tasks, with its checklist and its attempts.

    The attempts are the live progress of a running task (the component does not
    exist yet) and the full history once it is published.
    """
    task = await get_task(session, task_id=task_id, created_by=user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    attempts = await list_generations(session, task_id=task.id)

    detail = TaskDetailRead.model_validate(task)
    detail.generations = [GenerationRead.model_validate(attempt) for attempt in attempts]
    return detail
