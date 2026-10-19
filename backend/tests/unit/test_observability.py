"""The trace, decided without a Langfuse project.

What is tested here is the contract between the runner and the SDK: a trace that
is off builds nothing and writes nothing, a trace that is on opens a root, and
every step closes even when the step raised. The SDK itself is somebody else's
uptime; what would be a bug here is a span that leaks, a score that raises, or a
deployment without keys that still tries to reach the network.
"""

import pytest

from app.observability import service as observability
from app.settings import settings

pytestmark = pytest.mark.anyio

TRACE_ID = "a" * 32


class FakeSpan:
    """One observation, remembered."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.updates: list[dict] = []
        self.ended = False
        self.children: list[FakeSpan] = []
        # A broken exporter, for the test that checks it cannot break a step.
        self.fail = False

    def start_observation(self, *, name: str, input: object = None) -> FakeSpan:
        child = FakeSpan(name)
        child.input = input
        self.children.append(child)

        return child

    def update(self, **fields: object) -> None:
        if self.fail:
            raise RuntimeError("the exporter cannot serialize this")
        self.updates.append(fields)

    def end(self) -> None:
        if self.fail:
            raise RuntimeError("the exporter cannot serialize this")
        self.ended = True


class FakeClient:
    """The Langfuse client, answered without a project."""

    def __init__(self, *, broke: Exception | None = None) -> None:
        self.broke = broke
        self.roots: list[FakeSpan] = []
        self.scores: list[dict] = []
        self.fail_score = False
        self.shut = False

    def create_trace_id(self) -> str:
        return TRACE_ID

    def start_observation(self, **kwargs: object) -> FakeSpan:
        if self.broke is not None:
            raise self.broke

        root = FakeSpan(str(kwargs["name"]))
        root.kwargs = kwargs
        self.roots.append(root)

        return root

    def create_score(self, **kwargs: object) -> None:
        if self.fail_score:
            raise RuntimeError("the scores endpoint is down")

        self.scores.append(kwargs)

    def shutdown(self) -> None:
        self.shut = True


@pytest.fixture(autouse=True)
def with_keys(monkeypatch):
    """This module is about the configured path; the suite turns it off."""
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-lf-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-lf-test")


@pytest.fixture
def client(monkeypatch) -> FakeClient:
    fake = FakeClient()
    monkeypatch.setattr(observability, "_get_client", lambda: fake)

    return fake


def test_without_both_keys_nothing_is_built(monkeypatch):
    monkeypatch.setattr(settings, "langfuse_secret_key", None)
    monkeypatch.setattr(observability, "_get_client", lambda: pytest.fail("no client without keys"))

    trace = observability.start(name="generate_component", input={"brief": "A hero"})

    assert trace.id is None


async def test_with_keys_the_trace_is_ours_and_the_root_is_opened(client):
    trace = observability.start(
        name="generate_component", input={"brief": "A hero"}, metadata={"task_id": "t-1"}
    )

    assert trace.id == TRACE_ID
    root = client.roots[0]
    assert root.kwargs["trace_context"] == {"trace_id": TRACE_ID}
    assert root.kwargs["input"] == {"brief": "A hero"}
    assert root.kwargs["metadata"] == {"task_id": "t-1"}


async def test_a_step_is_a_child_that_closes(client):
    trace = observability.start(name="generate_component", input={})

    async with trace.step("Retrieving references", input={"brief": "A hero"}) as span:
        span.update(output={"category": "hero"})

    root = client.roots[0]
    child = root.children[0]
    assert child.name == "Retrieving references"
    assert child.input == {"brief": "A hero"}
    assert child.updates == [{"output": {"category": "hero"}}]
    assert child.ended is True


async def test_a_step_that_raises_closes_with_the_reason(client):
    trace = observability.start(name="generate_component", input={})

    with pytest.raises(RuntimeError, match="the sandbox is down"):
        async with trace.step("Generating the block"):
            raise RuntimeError("the sandbox is down")

    child = client.roots[0].children[0]
    assert child.ended is True
    assert child.updates == [{"level": "ERROR", "status_message": "the sandbox is down"}]


async def test_a_score_is_one_number_on_the_trace(client):
    trace = observability.start(name="generate_component", input={})

    trace.score("visual", 84)
    trace.score("published", 1, data_type="BOOLEAN", comment="the judge cleared it")

    assert client.scores == [
        {
            "trace_id": TRACE_ID,
            "name": "visual",
            "value": 84,
            "comment": None,
            "data_type": None,
        },
        {
            "trace_id": TRACE_ID,
            "name": "published",
            "value": 1,
            "comment": "the judge cleared it",
            "data_type": "BOOLEAN",
        },
    ]


async def test_a_score_that_fails_does_not_fail_the_run(client):
    client.fail_score = True
    trace = observability.start(name="generate_component", input={})

    # No exception: a score is a copy, and a copy that could not be sent is not a
    # reason to stop a task that has already committed.
    trace.score("visual", 84)


async def test_a_client_that_cannot_start_is_a_trace_that_is_off(monkeypatch):
    monkeypatch.setattr(
        observability, "_get_client", lambda: FakeClient(broke=RuntimeError("bad host"))
    )

    trace = observability.start(name="generate_component", input={})

    assert trace.id is None


async def test_the_root_is_closed_with_the_outcome(client):
    trace = observability.start(name="generate_component", input={})

    trace.finish(output={"slug": "a-hero"}, metadata={"iterations": 2})
    trace.end()

    root = client.roots[0]
    assert root.updates == [{"output": {"slug": "a-hero"}, "metadata": {"iterations": 2}}]
    assert root.ended is True


async def test_a_failed_run_closes_the_root_as_an_error(client):
    trace = observability.start(name="generate_component", input={})

    trace.finish(error="The judge did not publish it")
    trace.end()

    root = client.roots[0]
    assert root.updates[0] == {"level": "ERROR", "status_message": "The judge did not publish it"}


async def test_a_span_that_cannot_be_written_does_not_fail_the_step(client):
    trace = observability.start(name="generate_component", input={})

    async with trace.step("Generating the block") as span:
        client.roots[0].children[0].fail = True
        span.update(output={"files": []})

    trace.finish(output={"slug": "a-hero"})
    trace.end()
    # No exception out of any of it: a trace is a copy, and a copy that cannot be
    # written is a line in the log.


async def test_shutdown_flushes_a_client_that_exists(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(observability, "_client", fake)

    observability.shutdown()

    assert fake.shut is True
    assert observability._client is None


async def test_shutdown_without_a_client_does_nothing():
    # No keys, so no client was ever built: the process ending is not an event
    # this module has to react to.
    observability.shutdown()
