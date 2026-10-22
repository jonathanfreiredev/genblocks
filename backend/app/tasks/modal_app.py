"""The task worker, deployed as a Modal function.

    modal deploy app/tasks/modal_app.py

It runs the same entrypoint a local checkout runs by hand
(``python -m app.tasks.worker``): drain the queue, then exit. The schedule is
the safety net — the API wakes the worker the moment a task is queued (see
``app/tasks/trigger.py``) — and this catches whatever a failed wake-up left
behind. Both runs are safe together: a claim takes its row under
``FOR UPDATE SKIP LOCKED``, and the sweep only touches tasks older than
``worker_stale_seconds``.

It lives here rather than in the API because a block takes minutes to build,
which is longer than a scale-to-zero service can promise a background process,
and because a run should not be competing with the API for CPU while somebody is
browsing the catalogue.

The environment it needs is in a Modal secret, created once:

    modal secret create genblocks-worker --from-dotenv worker.env

That file is the worker's own, and ``worker.env.example`` lists what goes in it.
"""

from __future__ import annotations

from pathlib import Path

import modal

APP_NAME = "genblocks-worker"
FUNCTION_NAME = "drain"

# The Modal secret holding the provider credentials and the database URL. Named
# here, never written here: values do not belong in the repository.
SECRET_NAME = "genblocks-worker"

# How long one run may live. It has to stay under ``settings.worker_stale_seconds``
# (45 minutes), or a sweep could interrupt a task this run is still working on.
FUNCTION_TIMEOUT_SECONDS = 30 * 60

# The schedule the safety net runs on. The API wakes the worker directly, so this
# only has to be often enough that a task left behind is not left for long.
SCHEDULE = modal.Cron("*/15 * * * *")


def _skip_scaffold(path: Path) -> bool:
    """Whether a path belongs to the sandbox's scaffold rather than the worker.

    The worker never reads the scaffold: it is built into the harness image, by
    the harness app. It is hundreds of megabytes of ``node_modules``, and this
    mount is re-established on every cold start, so it is left out.
    """
    parts = path.parts
    return "scaffold" in parts or "node_modules" in parts or "dist" in parts


def build_image() -> modal.Image:
    """The backend's dependencies and its source, without the sandbox's scaffold."""
    return (
        modal.Image.debian_slim(python_version="3.14")
        # The lockfile decides the versions, exactly as the API's image does.
        .uv_sync(extra_options="--no-dev")
        # ``ignore`` replaces Modal's default, which drops every file that is not
        # Python: the rubrics and the skills are Markdown, and a run without them
        # fails halfway through.
        .add_local_python_source("app", ignore=_skip_scaffold)
    )


app = modal.App(APP_NAME)


@app.function(
    image=build_image(),
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    schedule=SCHEDULE,
    timeout=FUNCTION_TIMEOUT_SECONDS,
)
def drain() -> None:
    """Drain the queue once and exit.

    Imported inside the function because the source is mounted when the container
    starts, not when the app is deployed: what runs is the code that travelled
    with this deploy, which is the point.
    """
    import asyncio

    from app.tasks.worker import main

    asyncio.run(main())
