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
    # asynchronous FLUX.2 API: a request is queued, polled and downloaded. The
    # model is the pinned snapshot rather than the moving "preview" one, on
    # purpose: a block scored today should be comparable with the next one.
    bfl_api_key: str | None = None
    image_model: str = "flux-2-pro"
    bfl_base_url: str = "https://api.bfl.ai/v1"

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

    # The sandbox, by the name it was deployed under, and how long a task waits
    # on it. A cold container plus a browser is minutes, so the bound is
    # generous on purpose: it is there to end a run that will never answer, not
    # to hurry one that will.
    harness_app_name: str = "genblocks-harness"
    harness_timeout_seconds: int = 900

    # Chroma stores the retrieval vectors. Left blank in development it falls
    # back to a local persistent client, in this directory; in production it
    # points at Chroma Cloud, which needs all four.
    chroma_host: str | None = None
    chroma_api_key: str | None = None
    chroma_tenant: str | None = None
    chroma_database: str | None = None
    chroma_path: str = ".chroma"

    # How close is too close. Retrieval answers with cosine distance, so smaller
    # is nearer: a brief within ``duplicate_distance`` of a published block is
    # that block again, and the library already has it. A picture within
    # ``image_reuse_distance`` of what a block asked for is the picture it would
    # have generated, so it is reused instead. Both are calibration, measured
    # against real briefs — not taste.
    duplicate_distance: float = 0.18
    image_reuse_distance: float = 0.15

    # --- Generation loop -----------------------------------------------------
    # How many times the harness may build the block and look at it before it has
    # to finish with what it has. The budget counts *looks*, not model turns: the
    # sandbox and its render are what cost, and reading a skill is free. The number
    # was set by measuring real runs — the distribution of `iterations` and whether
    # the next look still changes the score — not by taste.
    harness_max_iterations: int = 6
    # How many pictures one block may ask the library for, in one pass near the end
    # of its run. Images are the priciest part of a task by a distance.
    images_per_block: int = 4
    # Every dimension of the judge's rubric has its own bar, and an attempt
    # clears only when it clears all of them: a high mean does not carry a block
    # past a dimension it failed (PLAN.md, section 7). These numbers are the
    # calibration, not the code — they move against real generations, and the
    # rubric's own version is what records its wording. A dimension that is not
    # named here is scored, shown, and not gated on.
    #
    # Calibrated against the first real generations: the judge scores good work
    # between 75 and 100, so the bars sit just inside its "good" band. The three
    # that are not taste are set higher — a block whose render is shaky is a
    # shaky block, and one that does not do what the brief asked is the wrong
    # block, however well it looks.
    rubric_thresholds: dict[str, int] = {
        "render": 85,
        "accessibility": 80,
        "visual": 75,
        "copy": 75,
        "compliance": 85,
        "prompt_fit": 75,
    }

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
