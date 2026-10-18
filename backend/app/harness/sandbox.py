"""Calling the sandbox from inside the service.

The sandbox is somebody else's process on somebody else's machine, reached by
name. Nothing of ours travels with the request except the files, and nothing it
answers comes back unread: :class:`SandboxResult` is what makes a renamed field a
loud failure rather than an attempt that records nothing.

Every way of not getting an answer — no deployment, no credentials, a run that
outlives its bound — arrives as :class:`SandboxUnavailable`, because the task row
is where a reader will look and "the sandbox did not answer" is what it should
say.
"""

import asyncio
from typing import Any

import modal
from pydantic import ValidationError

from app.harness.schemas import SandboxFile, SandboxRequest, SandboxResult
from app.settings import settings

# The function inside the app, published by deploying ``app/harness/modal_app.py``
# and renamed only together with it.
FUNCTION_NAME = "check"


class SandboxUnavailable(Exception):
    """The sandbox could not be reached, could not answer, or ran too long."""


async def check(files: list[SandboxFile], *, function: Any = None) -> SandboxResult:
    """Check one project in the sandbox, and read back what it found.

    ``function`` is the deployed function, injected by a test that has no
    deployment to call; production reaches for it by name.
    """
    request = SandboxRequest(files=files).model_dump(mode="json")

    try:
        call = function or _deployed()
    except modal.exception.Error as refused:
        raise SandboxUnavailable(_deploy_me(refused)) from refused

    try:
        answer = await asyncio.wait_for(
            call.remote.aio(request),
            timeout=settings.harness_timeout_seconds,
        )
    except TimeoutError as ran_long:
        raise SandboxUnavailable(
            f"The sandbox did not answer within {settings.harness_timeout_seconds} seconds."
        ) from ran_long
    except modal.exception.Error as broke:
        raise SandboxUnavailable(f"The sandbox failed: {broke}") from broke

    try:
        return SandboxResult.model_validate(answer)
    except ValidationError as unreadable:
        raise SandboxUnavailable(
            f"The sandbox answered something this service does not understand: {unreadable}"
        ) from unreadable


def _deployed() -> Any:
    """The sandbox function, by the name it was deployed under."""
    return modal.Function.from_name(settings.harness_app_name, FUNCTION_NAME)


def _deploy_me(error: Exception) -> str:
    return (
        f"The sandbox is not reachable ({error}). Deploy it from backend/ with "
        "`modal deploy app/harness/modal_app.py`."
    )
