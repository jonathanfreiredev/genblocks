"""Calling the sandbox, without one to call.

What is tested is everything between the request and the attempt: the shape that
leaves, the shape that is insisted on coming back, and the four ways of not
getting an answer — none of which may look to a reader like a broken block rather
than an unreachable sandbox.
"""

import asyncio
from types import SimpleNamespace

import modal
import pytest

from app.harness import sandbox
from app.harness.schemas import SandboxCheck, SandboxFile, SandboxResult
from app.settings import settings

pytestmark = pytest.mark.anyio

FILES = [SandboxFile(path="src/Block.tsx", content="export default function Block() {}")]

ANSWER = {
    "checks": [{"name": "typecheck", "ok": True, "detail": None}],
    "violations": [],
    "screenshot": b"\x89PNG",
}


class FakeFunction:
    """A deployed function, as the client reaches one."""

    def __init__(
        self,
        *,
        answer: dict | None = None,
        error: Exception | None = None,
        delay: float = 0.0,
    ) -> None:
        self.answer = answer if answer is not None else ANSWER
        self.error = error
        self.delay = delay
        self.sent: dict | None = None
        self.remote = SimpleNamespace(aio=self._called)

    async def _called(self, request: dict) -> dict:
        self.sent = request

        if self.delay:
            await asyncio.sleep(self.delay)

        if self.error is not None:
            raise self.error

        return self.answer


async def test_a_result_comes_back_read():
    found = await sandbox.check(FILES, function=FakeFunction())

    assert isinstance(found, SandboxResult)
    assert [check.name for check in found.checks] == ["typecheck"]
    assert found.screenshot == b"\x89PNG"


async def test_the_request_is_the_contract():
    function = FakeFunction()

    await sandbox.check(FILES, function=function)

    prefixes = (
        [f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/"]
        if settings.cloudinary_cloud_name
        else []
    )
    assert function.sent == {
        "files": [{"path": "src/Block.tsx", "content": FILES[0].content}],
        "asset_prefixes": prefixes,
    }


async def test_the_function_is_reached_by_the_name_it_was_deployed_under(monkeypatch):
    class Deployed:
        asked: tuple[str, str] | None = None

        @classmethod
        def from_name(cls, app_name: str, name: str) -> FakeFunction:
            cls.asked = (app_name, name)
            return FakeFunction()

    monkeypatch.setattr(sandbox.modal, "Function", Deployed)

    await sandbox.check(FILES)

    assert Deployed.asked == (settings.harness_app_name, sandbox.FUNCTION_NAME)


async def test_a_sandbox_that_is_not_deployed_says_how_to_deploy_it(monkeypatch):
    class Missing:
        @classmethod
        def from_name(cls, app_name: str, name: str) -> None:
            raise modal.exception.NotFoundError("no such app")

    monkeypatch.setattr(sandbox.modal, "Function", Missing)

    with pytest.raises(sandbox.SandboxUnavailable) as refused:
        await sandbox.check(FILES)

    assert "modal deploy app/harness/modal_app.py" in str(refused.value)


async def test_a_run_that_outlives_its_bound_is_not_waited_for(monkeypatch):
    monkeypatch.setattr(settings, "harness_timeout_seconds", 1)

    with pytest.raises(sandbox.SandboxUnavailable) as refused:
        await sandbox.check(FILES, function=FakeFunction(delay=5))

    assert "within 1 seconds" in str(refused.value)


async def test_a_sandbox_that_failed_remotely_is_reported_as_unavailable():
    function = FakeFunction(error=modal.exception.RemoteError("the chromium died"))

    with pytest.raises(sandbox.SandboxUnavailable) as refused:
        await sandbox.check(FILES, function=function)

    assert "the chromium died" in str(refused.value)


async def test_an_answer_this_service_cannot_read_is_refused_rather_than_guessed():
    function = FakeFunction(answer={"checks": "all of them"})

    with pytest.raises(sandbox.SandboxUnavailable) as refused:
        await sandbox.check(FILES, function=function)

    assert "does not understand" in str(refused.value)


async def test_a_check_that_failed_fatally_is_reported_by_the_result():
    function = FakeFunction(
        answer={
            "checks": [{"name": "build", "ok": False, "detail": "vite: unexpected token"}],
            "violations": [],
            "screenshot": None,
        }
    )

    found = await sandbox.check(FILES, function=function)

    assert found.blocked is True
    assert isinstance(found.checks[0], SandboxCheck)
    assert found.checks[0].detail == "vite: unexpected token"
