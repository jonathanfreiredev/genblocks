import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def no_tracing(monkeypatch):
    """Keep the suite off Langfuse.

    Tracing is a network call behind two keys. A suite that reached it would be
    testing somebody else's uptime and would leave traces of test runs in a real
    project. The keys are emptied here, so ``start`` answers with the disabled
    trace exactly the way a deployment that has not configured it does; the tests
    that care about a trace patch ``start`` themselves.
    """
    from app.settings import settings

    monkeypatch.setattr(settings, "langfuse_public_key", None)
    monkeypatch.setattr(settings, "langfuse_secret_key", None)


@pytest.fixture(autouse=True)
def no_moderation(monkeypatch):
    """Keep the suite off the safety model.

    Moderation is a network call behind a key. A suite that reached it would be
    testing somebody else's uptime and, worse, change its mind about a brief
    depending on what that service had for breakfast. It is stubbed to allow; a test
    that wants a refusal writes its own answer.
    """
    from app.moderation import service as moderation

    async def allowed(text, *, client=None):
        return None

    async def allowed_image(data, *, media_type="image/png", client=None):
        return None

    monkeypatch.setattr(moderation, "refusal", allowed)
    monkeypatch.setattr(moderation, "image_prompt_refusal", allowed)
    monkeypatch.setattr(moderation, "image_refusal", allowed_image)


@pytest.fixture(autouse=True)
def no_vectors(monkeypatch, tmp_path):
    """Keep the suite off the network and out of the real vector store.

    Retrieval is two external services — an embedder and a store — and a test that
    reached either would be testing somebody else's uptime. The settings are
    emptied rather than the service stubbed, because that is the state the product
    has to survive anyway: no embedder configured means indexing is a warning and
    search finds nothing, which is what every test that does not ask for vectors
    should see.

    A test that wants retrieval patches these back, and points ``chroma_path`` at
    its own directory.
    """
    from app.settings import settings

    monkeypatch.setattr(settings, "voyage_api_key", None)
    monkeypatch.setattr(settings, "chroma_api_key", None)
    monkeypatch.setattr(settings, "chroma_host", None)
    monkeypatch.setattr(settings, "chroma_path", str(tmp_path / "chroma"))
