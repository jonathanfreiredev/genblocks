import pytest

from app.settings import Settings

# Provider credentials that must never leak into a test through the
# developer's backend/.env or shell.
_PROVIDER_ENV_VARS = (
    "OPENAI_API_KEY",
    "BFL_API_KEY",
    "GROQ_API_KEY",
    "VOYAGE_API_KEY",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    "CHROMA_HOST",
    "CHROMA_API_KEY",
    "CHROMA_TENANT",
    "CHROMA_DATABASE",
)


def _settings(monkeypatch: pytest.MonkeyPatch, **env: str) -> Settings:
    """Build settings with the .env file disabled and clean provider env vars."""
    for name in _PROVIDER_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    return Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:password@localhost:5432/genblocks",
        supabase_url="https://project.supabase.co",
    )


def test_generation_defaults(monkeypatch):
    settings = _settings(monkeypatch)

    assert settings.llm_model == "gpt-6-luna"
    assert settings.image_model == "flux-2-pro"
    assert settings.moderation_model == "openai/gpt-oss-safeguard-20b"
    assert settings.embedding_model == "voyage-multimodal-3"
    assert settings.max_attempts == 2


def test_harness_defaults(monkeypatch):
    settings = _settings(monkeypatch)

    # The sandbox is reached by name, and a cold container plus a browser is
    # minutes: the bound is there to end a run that will never answer.
    assert settings.harness_app_name == "genblocks-harness"
    assert settings.harness_timeout_seconds == 900


def test_provider_credentials_are_optional(monkeypatch):
    # Missing keys must not stop the service from booting.
    settings = _settings(monkeypatch)

    assert settings.openai_api_key is None
    assert settings.bfl_api_key is None
    assert settings.groq_api_key is None
    assert settings.voyage_api_key is None
    assert settings.cloudinary_api_secret is None
    assert settings.modal_token_id is None
    assert settings.chroma_host is None
    assert settings.chroma_tenant is None
    assert settings.chroma_database is None


def test_provider_credentials_come_from_the_environment(monkeypatch):
    settings = _settings(monkeypatch, OPENAI_API_KEY="sk-test", BFL_API_KEY="bfl-test")

    assert settings.openai_api_key == "sk-test"
    assert settings.bfl_api_key == "bfl-test"
