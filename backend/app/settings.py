from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Defaults to production so a missing ENV never silently enables
    # development-only behaviour (SQL echo, text logs). Set ENV=development locally.
    env: str = "production"
    database_url: str
    # Base URL of the frontend, used to build the links sent to the user.
    frontend_url: str = "http://localhost:3000"
    # Minimum level for the application logs (DEBUG, INFO, WARNING, ...).
    log_level: str = "INFO"
    # Base URL of the Supabase project that issues the access tokens. The issuer
    # and the JWKS endpoint are derived from it (see the properties below).
    supabase_url: str
    # Audience claim Supabase access tokens carry.
    supabase_jwt_audience: str = "authenticated"
    # Public URL of the MCP server, as its clients reach it. Published as the
    # protected resource in the OAuth discovery document, so it must be the URL
    # clients use, not a container-internal hostname.
    mcp_base_url: str = "http://localhost:8001"
    # Where this service reaches the MCP server as a client (the playground). It
    # is a different address from ``mcp_base_url`` inside compose, where the
    # service answers to its own name rather than to localhost.
    mcp_internal_url: str = "http://localhost:8001"
    # Comma-separated list of browser origins allowed to call the API. Set the
    # real frontend domain(s) in production.
    cors_origins: str = "http://localhost:3000"

    # --- Generation providers ------------------------------------------------
    # Server-only credentials for the services that build and judge components.
    # The API and the MCP server read them; they are never handed to the
    # sandbox or the browser. Each stays optional so the service boots without
    # it, and the phase that uses one is the phase that requires it.

    # OpenAI powers the conversational agent, the spec, the harness and the
    # judge.
    openai_api_key: str | None = None
    llm_model: str = "gpt-6-luna"

    # Black Forest Labs generates the stock image library through its
    # asynchronous FLUX.2 API.
    bfl_api_key: str | None = None
    image_model: str = "flux-2-pro"

    # Groq powers moderation only, with a free-tier safety model.
    groq_api_key: str | None = None
    moderation_model: str = "openai/gpt-oss-safeguard-20b"

    # Voyage embeds screenshots and images for retrieval.
    voyage_api_key: str | None = None
    embedding_model: str = "voyage-multimodal-3"

    # Cloudinary stores generated images and screenshots. Nothing is kept on
    # disk.
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

    # Modal runs the code sandbox that builds and renders generated components.
    # It holds no secret: the agent loop lives in the backend (pattern B), so
    # these tokens only let the backend reach the sandbox.
    modal_token_id: str | None = None
    modal_token_secret: str | None = None

    # Chroma stores the retrieval vectors. Left blank in development it falls
    # back to a local persistent client; in production it points at Chroma
    # Cloud, which needs all four.
    chroma_host: str | None = None
    chroma_api_key: str | None = None
    chroma_tenant: str | None = None
    chroma_database: str | None = None

    # --- Generation loop -----------------------------------------------------
    # A component is published from the best of at most this many attempts.
    max_attempts: int = 2

    @property
    def debug(self) -> bool:
        return self.env == "development"

    @property
    def cors_origin_list(self) -> list[str]:
        """Allowed browser origins, split from the comma-separated setting."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def mcp_internal_endpoint(self) -> str:
        """The full URL of the MCP endpoint this service calls as a client."""
        return f"{self.mcp_internal_url.rstrip('/')}/mcp"

    @property
    def supabase_issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_issuer}/.well-known/jwks.json"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
