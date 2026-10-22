"""Waking the worker is a courtesy: a queue that cannot reach Modal still queues.

The row is committed before the wake-up is attempted, and the schedule is the net
underneath it, so nothing here is allowed to raise.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.settings import settings
from app.tasks import trigger

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _fresh_lookup(monkeypatch):
    """The function is looked up once per process; every test starts over."""
    monkeypatch.setattr(trigger, "_function", None)


def _spawnable() -> MagicMock:
    """What ``Function.from_name`` returns: something with an async spawn."""
    function = MagicMock()
    function.spawn.aio = AsyncMock()
    return function


async def test_a_deployment_without_a_worker_wakes_nothing(monkeypatch):
    monkeypatch.setattr(settings, "worker_function", None)

    with patch("modal.Function.from_name") as lookup:
        await trigger.wake_worker()

    lookup.assert_not_called()


async def test_the_configured_function_is_started(monkeypatch):
    monkeypatch.setattr(settings, "worker_function", "genblocks-worker.drain")
    function = _spawnable()

    with patch("modal.Function.from_name", return_value=function) as lookup:
        await trigger.wake_worker()

    lookup.assert_called_once_with("genblocks-worker", "drain")
    function.spawn.aio.assert_awaited_once_with()


async def test_a_setting_without_a_function_name_reaches_no_caller(monkeypatch):
    monkeypatch.setattr(settings, "worker_function", "genblocks-worker")

    with patch("modal.Function.from_name") as lookup:
        await trigger.wake_worker()

    lookup.assert_not_called()


async def test_modal_being_unreachable_reaches_no_caller(monkeypatch):
    monkeypatch.setattr(settings, "worker_function", "genblocks-worker.drain")

    with patch("modal.Function.from_name", side_effect=OSError("no route to host")):
        await trigger.wake_worker()
