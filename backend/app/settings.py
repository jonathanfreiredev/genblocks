from pathlib import Path
from urllib.parse import urlsplit

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

    # Groq powers the text moderation fallback, with a free-tier safety model.
    groq_api_key: str | None = None
    moderation_model: str = "openai/gpt-oss-safeguard-20b"
    # OpenAI moderation is the primary text and image gate when its key is set.
    # The moderation endpoint is deliberately not the generation model: it is a
    # classifier, not a chat that a brief can talk into a verdict.
    openai_moderation_model: str = "omni-moderation-latest"

    # A CSAM hash-matching service is not interchangeable with a generic image
    # classifier. Point this at an adapter that accepts the contract documented
    # in ``app.moderation.service``. In production its absence refuses image
    # work rather than publishing unchecked pictures.
    csam_scan_url: str | None = None
    csam_scan_api_key: str | None = None
    # Older deployments named this CSAM_SCAN_KEY. Accept both so a working
    # scanner is not turned off by a spelling difference in the environment.
    csam_scan_key: str | None = None

    # Every picture is decoded, bounded and re-encoded before it is moderated or
    # stored. The bounds are both a safety limit and a bill: a provider that
    # answers with a decompression bomb, a huge pixel canvas or an endless byte
    # stream is refused here rather than handed to a classifier or a CDN.
    image_max_bytes: int = 20 * 1024 * 1024
    image_max_pixels: int = 24_000_000
    image_reencode_quality: int = 85

    # The hosts a provider may name in a polling URL or a finished asset URL.
    # BFL answers with URLs; treating any URL it returns as trusted would turn a
    # compromised provider response into an SSRF primitive.
    bfl_asset_hosts: str = "delivery.bfl.ai,api.bfl.ai"

    # Who may see the report queue and take content down. A global operator role,
    # deliberately separate from an organization role: an owner of one tenant
    # must not be able to remove another tenant's public work.
    admin_emails: str = ""

    # Resend sends one email when a report enters the queue. It is a
    # notification, never a gate: a report is saved whether or not the email
    # provider answers. Leave the key blank to keep the queue silent.
    resend_api_key: str | None = None
    resend_from_email: str = "GenBlocks <onboarding@resend.dev>"
    # Where the notification goes. Empty falls back to ADMIN_EMAILS, so one
    # setting already names the people who can act on it.
    report_notification_emails: str = ""

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

    # --- Observability -------------------------------------------------------
    # Langfuse is a copy of what happened, never the source of truth: the ledger
    # is Postgres. Without both keys nothing is sent and every trace id stays
    # null. With them, the SDK buffers spans and exports them in the background,
    # so a slow or unavailable Langfuse costs a warning, not a task.
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # How close is too close. Retrieval answers with cosine distance, so smaller
    # is nearer: a brief within ``duplicate_distance`` of a published block is
    # that block again, and the library already has it. A picture within
    # ``image_reuse_distance`` of what a block asked for is the picture it would
    # have generated, so it is reused instead.
    #
    # Measured against the seeded registry with the text-only index: a brief
    # that repeats a block lands at 0.40–0.47, a variant at about 0.47, and
    # something unrelated at 0.77 and up. The bar sits between the repeat and
    # the rest, and it is a bar the agent can argue with — ``create_component``
    # takes a ``force`` after the person has said they want it anyway.
    duplicate_distance: float = 0.50
    image_reuse_distance: float = 0.45

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
    # How many blocks one person may queue in a calendar month (UTC). A product
    # decision, not a calibration: it protects the bill and keeps a single account
    # from spending the month's budget by accident. There is no global breaker in
    # code on purpose — Modal and OpenAI are capped where they are billed, and a
    # second number here would be a copy that drifts from the real one.
    tasks_per_month: int = 10
    # The hosts a block may load a picture or a stylesheet from, comma-separated.
    # Everything else it shows has to travel with it — a relative path or a
    # ``data:`` URL — because a block is copied into somebody else's page, and a
    # picture we do not host is a picture that stops arriving when that host moves.
    # Checked before the sandbox, so a project that points elsewhere costs no render.
    allowed_asset_hosts: str = "res.cloudinary.com"
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
    def csam_scan_credential(self) -> str | None:
        """The child-safety scanner credential, under either supported name."""
        return self.csam_scan_api_key or self.csam_scan_key

    @property
    def bfl_polling_hosts(self) -> tuple[str, ...]:
        """Hosts a BFL polling URL may name.

        The configured API host is the one BFL is called at; ``api.bfl.ai`` is
        kept as the documented host so a deployment that fronts the API through
        its own proxy does not lose the ability to poll the real service.
        """
        configured = urlsplit(self.bfl_base_url).hostname
        return tuple(one for one in {configured, "api.bfl.ai"} if one)

    @property
    def bfl_asset_host_list(self) -> tuple[str, ...]:
        """Hosts a finished BFL asset URL may name."""
        return tuple(
            one.strip().lower().rstrip(".")
            for one in self.bfl_asset_hosts.split(",")
            if one.strip()
        )

    @property
    def admin_email_list(self) -> tuple[str, ...]:
        """The operators allowed to review reports and take content down."""
        return tuple(one.strip().lower() for one in self.admin_emails.split(",") if one.strip())

    @property
    def report_notification_recipients(self) -> tuple[str, ...]:
        """Who receives a new-report email.

        An explicit list wins; otherwise the operators are the recipients,
        because they are already the people who can review and act on it.
        """
        configured = self.report_notification_emails or self.admin_emails
        return tuple(one.strip() for one in configured.split(",") if one.strip())

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
