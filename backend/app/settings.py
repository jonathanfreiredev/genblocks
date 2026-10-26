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
    # Where this service probes the MCP server for ``/warmup``. It is a different
    # address from ``mcp_base_url`` inside compose, where the MCP answers to its
    # service name rather than to localhost.
    mcp_internal_url: str = "http://localhost:8001"
    # Comma-separated list of browser origins allowed to call the API. Set the
    # real frontend domain(s) in production.
    cors_origins: str = "http://localhost:3000"

    # --- Generation providers ------------------------------------------------
    # Server-only credentials for the services that build and judge artifacts.
    # The API and the MCP server read them; they are never handed to the sandbox
    # or the browser. Each stays optional so the service boots without it, and the
    # feature that needs one explains the missing key when it is used.

    # OpenAI powers the conversational agent, the spec, the harness, the judge,
    # the image-direction policy, the person detector and moderation.
    openai_api_key: str | None = None
    llm_model: str = "gpt-6-luna"

    # Black Forest Labs generates the stock image library through its
    # asynchronous FLUX.2 API: a request is queued, polled and downloaded. The
    # model is the pinned snapshot rather than the moving "preview" one, on
    # purpose: a block scored today should be comparable with the next one.
    bfl_api_key: str | None = None
    image_model: str = "flux-2-pro"
    bfl_base_url: str = "https://api.bfl.ai/v1"

    # Groq is the text fallback for moderation and image-direction policy when
    # OpenAI is not configured.
    groq_api_key: str | None = None
    moderation_model: str = "openai/gpt-oss-safeguard-20b"
    # OpenAI moderation is the primary text and image gate when its key is set.
    # The moderation endpoint is deliberately not the generation model: it is a
    # classifier, not a chat that a brief can talk into a verdict.
    openai_moderation_model: str = "omni-moderation-latest"
    # The picture library has one non-negotiable visual rule: no people. This
    # vision model checks the bytes themselves, because a prompt filter cannot
    # guarantee what the generator actually produced. It is a separate call from
    # omni-moderation on purpose: one gate answers "is this safe content?", this
    # one answers "is there a human here at all?".
    people_detection_model: str = "gpt-4o-mini"
    # The image policy decides whether a component brief or a standalone prompt
    # asks for a picture, whether the person is incidental to it, and whether a
    # no-person rewrite is possible. It is text-only and never generates the
    # picture.
    image_direction_model: str = "gpt-4o-mini"

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
    # The domains a provider may name, subdomains included. BFL answers from a
    # regional host it does not document in advance (``api.us7.bfl.ai``), so a
    # list of exact names refuses a URL for a picture that was already paid for.
    # The domain is still BFL's own infrastructure; anything outside it, including
    # a name that merely ends in the same letters, stays refused.
    bfl_allowed_domains: str = "bfl.ai"

    # Who may see the report queue and take content down. This is a global
    # operator list, not an organization role: the product has no tenant scope for
    # public work, and the queue can point at any published artifact.
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
    # The delivery base an asset's public id is appended to. It is public and
    # signs nothing, so a process that only reads the vault (the MCP server) can
    # hand out image addresses without holding credentials. It ships with the
    # account's own base so nothing has to be configured to publish a URL; set
    # ASSET_BASE_URL to point a deployment somewhere else, or empty for none.
    asset_base_url: str = "https://res.cloudinary.com/ddjovluur/image/upload"

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

    # --- The worker ----------------------------------------------------------
    # Where the queue is drained. In development the API owns the worker (see
    # ``app/main.py``); in production it is a Modal function, and this is its
    # name as ``app.function``. Both doors that queue work wake it the moment
    # the row is committed, and it drains whatever it finds.
    #
    # Empty means nothing is woken, which is what a local checkout and a test
    # want: the row is still committed and the queue still moves, it just waits
    # for whoever is looking at it.
    worker_function: str | None = None
    # How long a task may stay ``running`` before a run treats it as the work of
    # a run that died. Runs overlap — the schedule fires every minute and one
    # run can last for minutes — so age is the only thing that tells a task
    # being worked on from one abandoned. It has to stay longer than the worker
    # function's own timeout (see ``app/tasks/modal_app.py``), or a sweep would
    # interrupt live work.
    worker_stale_seconds: int = 45 * 60

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
    # How many generations one person may queue in a calendar month (UTC), blocks
    # and images together. A product decision, not a calibration: it protects the
    # bill and keeps a single account from spending the month's budget by accident.
    # There is no global breaker in code on purpose — Modal, OpenAI and BFL are
    # capped where they are billed, and a second number here would be a copy that
    # drifts from the real one.
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
    def bfl_allowed_domain_list(self) -> tuple[str, ...]:
        """The BFL domains a polling or sample URL may name, subdomains included."""
        return tuple(
            one.strip().lower().lstrip(".").rstrip(".")
            for one in self.bfl_allowed_domains.split(",")
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
        # Deployment environments outlive individual settings. Ignoring unknown
        # keys lets a renamed or retired feature be removed without breaking a
        # boot; the application only reads the fields declared above.
        extra="ignore",
    )


settings = Settings()
