"""The caller's own tasks, over HTTP.

Every route here is scoped to the token's user: the list never shows a task
someone else started, and reading someone else's answers exactly as an unknown
id does.
"""

import uuid

import pytest
from sqlalchemy import select

from app.generations.models import Generation
from app.tasks.models import Task, TaskStep
from app.users.models import User
from tests.auth_stub import mint_token
from tests.helpers import auth_header

pytestmark = pytest.mark.anyio


async def _sign_in(client, db_session, email: str) -> tuple[str, User]:
    """Provision the token's user the way a first sign-in does, and return both."""
    token = mint_token(email=email)
    response = await client.get("/v1/users/me", headers=auth_header(token))
    assert response.status_code == 200, response.text

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    return token, user


async def test_tasks_require_authentication(client):
    assert (await client.get("/v1/tasks")).status_code == 401
    assert (await client.get(f"/v1/tasks/{uuid.uuid4()}")).status_code == 401


async def test_a_caller_only_sees_their_own_tasks(client, db_session):
    mine, me = await _sign_in(client, db_session, "mine@example.com")
    _, them = await _sign_in(client, db_session, "theirs@example.com")
    db_session.add_all(
        [
            Task(brief="mine", created_by=me.id),
            Task(brief="theirs", created_by=them.id),
        ]
    )
    await db_session.commit()

    body = (await client.get("/v1/tasks", headers=auth_header(mine))).json()

    assert body["total"] == 1
    assert [task["brief"] for task in body["items"]] == ["mine"]


async def test_the_task_list_narrows_to_one_status(client, db_session):
    token, user = await _sign_in(client, db_session, "status@example.com")
    db_session.add_all(
        [
            Task(brief="finished", status="succeeded", created_by=user.id),
            Task(brief="running", status="running", created_by=user.id),
        ]
    )
    await db_session.commit()

    response = await client.get(
        "/v1/tasks", params={"status": "running"}, headers=auth_header(token)
    )

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert [task["brief"] for task in response.json()["items"]] == ["running"]


async def test_an_unknown_status_is_rejected(client, db_session):
    token, _ = await _sign_in(client, db_session, "status@example.com")

    response = await client.get(
        "/v1/tasks", params={"status": "zombie"}, headers=auth_header(token)
    )

    assert response.status_code == 422


async def test_a_task_reads_with_its_steps_in_index_order_and_its_attempts(client, db_session):
    token, user = await _sign_in(client, db_session, "reader@example.com")
    task = Task(
        brief="A pricing page",
        status="running",
        created_by=user.id,
        steps=[
            TaskStep(index=1, name="Retrieving references"),
            TaskStep(index=0, name="Moderating the brief"),
        ],
    )
    db_session.add(task)
    await db_session.commit()

    task_id = task.id
    db_session.add_all(
        [
            Generation(task_id=task_id, attempt_no=2, code="second pass"),
            Generation(task_id=task_id, attempt_no=1, code="first pass"),
        ]
    )
    await db_session.commit()

    # A request gets its own scope in production; expiring here makes the steps
    # load from the table, in index order, instead of from the collection this
    # test built in memory.
    db_session.expire_all()

    response = await client.get(f"/v1/tasks/{task_id}", headers=auth_header(token))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["brief"] == "A pricing page"
    assert [step["index"] for step in body["steps"]] == [0, 1]
    assert [attempt["attempt_no"] for attempt in body["generations"]] == [1, 2]
    # The trace link the UI builds from this field resolves to nothing for a task
    # that was never traced.
    assert body["langfuse_trace_id"] is None


async def test_a_task_of_someone_else_is_invisible(client, db_session):
    mine, _ = await _sign_in(client, db_session, "mine@example.com")
    _, them = await _sign_in(client, db_session, "theirs@example.com")
    task = Task(brief="theirs", created_by=them.id)
    db_session.add(task)
    await db_session.commit()

    # The same 404 an unknown id gets: a 403 would confirm the task exists.
    invisible = await client.get(f"/v1/tasks/{task.id}", headers=auth_header(mine))
    unknown = await client.get(f"/v1/tasks/{uuid.uuid4()}", headers=auth_header(mine))

    assert invisible.status_code == 404
    assert unknown.status_code == 404


async def test_the_task_page_envelope_is_honest(client, db_session):
    token, user = await _sign_in(client, db_session, "pager@example.com")
    db_session.add_all([Task(brief=f"brief {index}", created_by=user.id) for index in range(3)])
    await db_session.commit()

    first = (await client.get("/v1/tasks", params={"limit": 2}, headers=auth_header(token))).json()
    second = (
        await client.get("/v1/tasks", params={"limit": 2, "offset": 2}, headers=auth_header(token))
    ).json()

    assert first["total"] == 3  # the total ignores the page size
    assert first["limit"] == 2
    assert len(first["items"]) == 2
    assert second["total"] == 3
    assert len(second["items"]) == 1
