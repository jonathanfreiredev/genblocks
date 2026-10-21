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
def no_image_policy(monkeypatch):
    """Keep the suite off the image-direction model as well.

    The default is a brief with no explicit image direction: ready, and the
    builder chooses. A test that wants people, a rewrite or a refusal patches
    ``app.image_policy.service.evaluate`` itself.
    """
    from app.image_policy import service as image_policy

    async def ready(brief, *, client=None):
        return image_policy.ImagePolicyDecision(
            status="ready",
            has_image_direction=False,
            has_people=False,
            people_role="none",
            reason="no explicit image direction; the builder chooses",
            proposed_brief=None,
        )

    monkeypatch.setattr(image_policy, "evaluate", ready)


@pytest.fixture(autouse=True)
def no_notifications(monkeypatch):
    """Keep the suite from sending real report emails.

    A developer who has RESEND_API_KEY in their local .env should not discover
    it by finding test reports in their inbox. The notification tests turn the
    key back on and answer with a mock transport.
    """
    from app.settings import settings

    monkeypatch.setattr(settings, "resend_api_key", None)


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
