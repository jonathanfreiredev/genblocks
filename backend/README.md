# Backend — FastAPI

The API for [GenBlocks](../README.md). It serves the public catalogue and the per-user task queue on top of an async SQLAlchemy / PostgreSQL stack, and it owns the generation worker and the agent chat.

Authentication is delegated to [**Supabase Auth**](https://supabase.com/docs/guides/auth), which owns credentials, email verification, social login and sessions. This service is a **resource server**: it verifies the Supabase access token (an asymmetric JWT) against the project's **JWKS** and provisions a local profile the first time it sees a user. It never issues tokens or stores passwords.

## Tech stack

- **FastAPI** — HTTP layer
- **SQLAlchemy 2.0** (async) with **asyncpg** — ORM and driver
- **Alembic** — database migrations
- **Pydantic v2 / pydantic-settings** — schemas and configuration
- **PyJWT** with **cryptography** — verifying Supabase access tokens (RS256/ES256)
- **LangGraph** and **LangChain** — the assistant, the harness agent and the judge
- **OpenAI**, **Groq**, **Black Forest Labs**, **Voyage** and **Modal** — models, moderation, images, embeddings and the sandbox
- **Chroma** and **Cloudinary** — retrieval and asset storage
- **Langfuse** — optional traces and scores
- **uv** — dependency management
- **ruff** — linting and formatting

## Project structure

```
backend/
├── app/
│   ├── auth/
│   │   ├── verifier.py        # Verify a Supabase JWT against the project's JWKS
│   │   ├── claims.py          # TokenClaims + parsing, shared by both doors
│   │   └── dependencies.py    # Bearer token -> TokenClaims
│   ├── users/
│   │   ├── models.py          # User (profile) ORM model
│   │   ├── schemas.py         # UserRead / UserUpdate
│   │   ├── service.py         # Just-in-time profile provisioning
│   │   ├── dependencies.py    # TokenClaims -> local User
│   │   └── router.py          # /users endpoints (read, update, delete me)
│   ├── authz/
│   │   ├── permissions.py     # Roles, permissions and the policy table
│   │   └── dependencies.py    # Resolves the REST door's caller (agents rejected)
│   ├── organizations/
│   │   ├── models.py          # Organization + Membership (the tenant model)
│   │   ├── schemas.py         # OrganizationRead / MembershipRead
│   │   ├── service.py         # Create with an owner, list, resolve memberships
│   │   ├── dependencies.py    # Path organization -> the caller's membership
│   │   └── router.py          # /organizations endpoints
│   ├── mcp/
│   │   ├── server.py          # FastMCP app, Supabase auth and /health
│   │   ├── auth.py            # Verifies MCP tokens with app.auth.verifier
│   │   ├── tools.py           # The tools, and their registration
│   │   └── main.py            # ASGI entrypoint (uvicorn app.mcp.main:app)
│   ├── agent/                 # Chat graph, SSE stream and conversational tools
│   ├── harness/               # Builder agent, static checks, Modal sandbox and skills
│   ├── judge/                 # Independent scoring, rubrics and thresholds
│   ├── tasks/                 # Queue, worker, pipeline steps, spec and quota
│   ├── components/            # Published blocks and image direction
│   ├── images/                # Stock images, planning and sanitization
│   ├── categories/            # Two-level taxonomy
│   ├── vectors/               # Voyage embeddings and Chroma retrieval
│   ├── briefs/                # Exact brief cache
│   ├── moderation/            # Text, image and no-people gates
│   ├── observability/         # Optional Langfuse wrapper
│   ├── reports/               # Public reports and the operator queue
│   ├── admin/                 # Content and user takedowns
│   ├── health/
│   │   └── router.py          # Liveness, readiness and the MCP warm-up
│   ├── middleware/
│   │   ├── body_limit.py      # 1 MB request-body ceiling
│   │   └── request_id.py      # Request id + structured access log
│   ├── db/
│   │   ├── session.py         # Async engine + session factory
│   │   └── models.py          # Declarative Base and BaseModel (id, timestamps)
│   ├── api.py                 # Versioned API entrypoint (mounts /v1)
│   ├── settings.py            # Settings loaded from .env
│   ├── logging_config.py      # structlog setup (dev text / prod JSON)
│   ├── pagination.py          # Offset pagination + sorting for list endpoints
│   └── main.py                # FastAPI app, routers, CORS and the worker
├── alembic/                   # Migrations (async env.py)
├── alembic.ini
├── pyproject.toml
└── .python-version            # 3.14
```

## Requirements

- Python **3.14+**
- [uv](https://docs.astral.sh/uv/)
- **Docker** or **Podman** for the containerized stack (the database, API and web app), or a PostgreSQL server you can point `DATABASE_URL` at
- A **Supabase project** (see the [frontend README](../frontend/README.md) for the auth setup)

## Setup

```bash
cd backend

# Install dependencies into .venv
uv sync

# Create your environment file
cp .env.example .env

# Apply migrations
uv run alembic upgrade head

# Seed the taxonomy and the development vault
uv run python -m app.categories.seed
uv run python -m app.seed.vault
```

PostgreSQL comes from the repository's `docker-compose.yml`, so `DATABASE_URL` must point at the host-mapped port (`localhost:5432`).

## Environment variables

Create `backend/.env`:

```dotenv
# DATABASE
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/app

# Supabase project URL (the issuer and JWKS are derived from it)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated

# Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Environment: production (default) or development (enables SQL echo)
ENV=development

# Comma-separated browser origins allowed to call the API (CORS)
CORS_ORIGINS=http://localhost:3000
```

| Variable                | Required | Default                 | Description                                                          |
| ----------------------- | -------- | ----------------------- | -------------------------------------------------------------------- |
| `DATABASE_URL`          | Yes      | –                       | Async connection string. Must use the `postgresql+asyncpg://` driver. |
| `SUPABASE_URL`          | Yes      | –                       | Supabase project URL. The issuer (`<url>/auth/v1`) and JWKS (`<url>/auth/v1/.well-known/jwks.json`) are derived from it. |
| `SUPABASE_JWT_AUDIENCE` | No       | `authenticated`         | Audience claim the access tokens carry.                              |
| `ENV`                   | No       | `production`            | `development` enables SQL echo and text logs.                        |
| `LOG_LEVEL`             | No       | `INFO`                  | Minimum level for the application logs.                              |
| `FRONTEND_URL`          | No       | `http://localhost:3000` | Base URL of the frontend, used for redirects and documentation.      |
| `MCP_BASE_URL`          | No       | `http://localhost:8001` | Public URL of the MCP server. Published in the OAuth discovery document, so it must be the URL clients use. |
| `MCP_INTERNAL_URL`      | No       | `http://localhost:8001` | Internal address the API probes for `/warmup`; not the public MCP URL. |
| `WORKER_FUNCTION`       | Prod     | –                       | The Modal function that drains the queue, as `app.function`. Empty in development, where the API owns the worker. Its environment is `worker.env.example`, not this file. |
| `CORS_ORIGINS`          | No       | `http://localhost:3000` | Comma-separated browser origins allowed to call the API.             |
| `BFL_ASSET_HOSTS`       | No       | `delivery.bfl.ai,api.bfl.ai` | Hosts a BFL polling or sample URL may name. Anything else is refused before it is fetched. |
| `IMAGE_MAX_BYTES`       | No       | `20971520`              | Input and output byte bound for a picture before moderation/storage. |
| `IMAGE_MAX_PIXELS`      | No       | `24000000`              | Decoded pixel bound for a picture.                                  |
| `IMAGE_REENCODE_QUALITY`| No       | `85`                    | JPEG quality used when a picture is re-encoded.                     |
| `OPENAI_MODERATION_MODEL` | No | `omni-moderation-latest` | OpenAI text/image moderation model. |
| `PEOPLE_DETECTION_MODEL` | No      | `gpt-4o-mini`           | Vision model that refuses any picture containing a human or human-like figure. |
| `IMAGE_DIRECTION_MODEL` | No       | `gpt-4o-mini`           | Text model that classifies image direction or a standalone prompt and proposes no-person rewrites. |
| `ADMIN_EMAILS`          | No       | –                       | Comma-separated global operators for the item queue and report takedowns. |
| `RESEND_API_KEY`        | No       | –                       | Resend key for new-report and new-item notifications. Empty keeps them silent. |
| `RESEND_FROM_EMAIL`     | No       | `GenBlocks <onboarding@resend.dev>` | Verified sender for operator notifications. |
| `REPORT_NOTIFICATION_EMAILS` | No  | `ADMIN_EMAILS`          | Comma-separated recipients; falls back to the operators.             |

Settings are defined in `app/settings.py` and loaded from `backend/.env`. The generation providers, storage, retrieval, sandbox and tracing settings are listed in `backend/.env.example`; the MCP's smaller production set is in `backend/mcp.env.example`, and the deployed worker's set is in `backend/worker.env.example`.

## Running the server

```bash
# Development (auto-reload) — http://localhost:8000
uv run fastapi dev

# Production
uv run fastapi run
```

The OpenAPI docs are at `/docs` and the raw schema at `/openapi.json` when `ENV=development`. Production disables all three routes.

## Logging

Logging is [structlog](https://www.structlog.org/) on top of the standard library, configured in `app/logging_config.py`:

- **Development** (`ENV=development`) renders human-readable lines; **production** renders one JSON object per line, ready for any log aggregator.
- Uvicorn's own logs go through the same pipeline, so the process emits a single format.
- Every request gets a **`request_id`** — reused from an inbound `X-Request-ID` header or generated — attached to all its log lines and echoed back in the `X-Request-ID` response header. Authenticated requests also carry `user_id`.

Verbosity is controlled with `LOG_LEVEL` (default `INFO`).

## Health checks

Two unauthenticated probes, for orchestrators, load balancers and uptime monitors, and one endpoint for the page:

- `GET /health` — **liveness**: the process is running. It checks nothing external on purpose, so a failure means "restart the container".
- `GET /health/ready` — **readiness**: runs `SELECT 1` against the database and returns `503` when it is unreachable, so traffic is routed away without restarting the process.
- `GET /warmup` — **wake-up**: probes the MCP server's liveness, which is also what starts it when the platform has stopped it. Answers `200` with `{"api": "ok", "mcp": "ok" | "waking"}`: the caller polls it, so "not yet" is a field rather than a status code, and a cached answer would be worse than none.

Set the health check path to `/health`. An external monitor can point at the same path for alerts. In local development, `docker-compose.yml` probes `/health` and the frontend waits for the backend to be healthy.

`/warmup` is kept for orchestrators and schedulers that need to wake the MCP service. The current frontend does not call it.

## Linting and formatting

The project uses [ruff](https://docs.astral.sh/ruff/) for both linting and formatting, configured in `pyproject.toml`.

```bash
# Lint
uv run ruff check .

# Lint and auto-fix
uv run ruff check --fix .

# Format
uv run ruff format .
```

## Tests

The suite has two layers, split by directory:

- **Integration tests** (`tests/integration/`) exercise the API **through its HTTP interface** against a real PostgreSQL database, using `httpx`'s ASGI transport. They forge Supabase-style access tokens with a local RSA key (`tests/auth_stub.py`), so no Supabase project is needed and the real signature, issuer, audience and expiry checks still run.
- **Unit tests** (`tests/unit/`) cover single functions in isolation, with no database (token verification edge cases).

Run everything:

```bash
uv run pytest
```

Run one layer:

```bash
uv run pytest tests/unit          # no database required
uv run pytest tests/integration   # needs the test database
```

### Test database

The integration tests use a dedicated PostgreSQL database. Create it once, next to your development one:

```bash
# from the repository root, against the running postgres service
docker compose exec postgres createdb -U postgres app_test
```

By default they connect to `app_test` on the same host as `DATABASE_URL`; set `TEST_DATABASE_URL` to point somewhere else. Each test creates the tables before it runs and drops them afterwards, so it never touches your development data.

## Database migrations

Alembic is configured for async migrations (`alembic/env.py`) and imports the models so autogenerate can detect changes.

```bash
# Generate a migration after changing a model
uv run alembic revision --autogenerate -m "describe change"

# Apply all pending migrations
uv run alembic upgrade head

# Roll back one migration
uv run alembic downgrade -1
```

When you add a new model, import it in `alembic/env.py` so it is included in autogenerate.

## API reference

Protected endpoints require an `Authorization: Bearer <supabase_access_token>` header.

| Method | Path                             | Auth | Description                                             |
| ------ | -------------------------------- | :--: | ------------------------------------------------------- |
| GET    | `/health`                        |      | Liveness: the process is up (no external checks)        |
| GET    | `/health/ready`                  |      | Readiness: the database is reachable (`503` if not)     |
| GET    | `/warmup`                        |      | Wake the MCP server and report what is up yet           |
| GET    | `/v1/users/me`                   |  ✓   | Return the current profile (provisions it on first use) |
| PATCH  | `/v1/users/me`                   |  ✓   | Update the profile name                                 |
| DELETE | `/v1/users/me`                   |  ✓   | Delete the profile (hard delete)                        |
| GET    | `/v1/categories`                 |      | The two-level taxonomy                                  |
| GET    | `/v1/components`                 |      | Published blocks, with search and pagination            |
| GET    | `/v1/components/by-slug/{slug}`  |      | One block, its files and its evidence                   |
| GET    | `/v1/components/{id}`            |      | One block by id                                         |
| GET    | `/v1/components/{id}/preview`    |      | The sandboxed HTML document for the live page           |
| GET    | `/v1/components/{id}/generations` |      | The attempts behind a block                             |
| GET    | `/v1/images`                     |      | The public stock library                                |
| GET    | `/v1/images/by-slug/{slug}`      |      | One image and its judge panel                           |
| POST   | `/v1/images/plan`                |  ✓   | Check an image prompt without queueing                  |
| POST   | `/v1/images/generate`            |  ✓   | Queue a standalone image                                |
| GET    | `/v1/tasks`                      |  ✓   | The caller's tasks                                      |
| POST   | `/v1/tasks`                      |  ✓   | Queue a component                                       |
| GET    | `/v1/tasks/{id}`                 |  ✓   | One task, its checklist and its attempts                |
| POST   | `/v1/agent/chat`                 |  ✓   | Stream one assistant turn                               |
| POST   | `/v1/agent/confirm`              |  ✓   | Queue a brief the person confirmed                      |
| POST   | `/v1/reports`                    |  ✓   | Report a public artifact                                |
| GET    | `/v1/admin/reports`              |  ✓   | The operator report queue                               |
| POST   | `/v1/organizations`              |  ✓   | Create an organization; the caller becomes its owner    |
| GET    | `/v1/organizations`              |  ✓   | List the organizations the caller belongs to            |
| GET    | `/v1/organizations/{id}`         |  ✓   | Read one organization the caller belongs to             |
| PATCH  | `/v1/organizations/{id}`         |  ✓   | Rename an organization (owner only)                     |
| GET    | `/v1/organizations/{id}/members` |  ✓   | List the members of an organization                     |

The application API is versioned under `/v1` (`app/api.py`); the health checks
stay unversioned so a future `/v2` never breaks orchestrators.

### Request / response examples

**PATCH `/v1/users/me`** — the name is domain data owned by this service; the email lives in Supabase and is changed from the client.

```json
{ "full_name": "Jane Smith" }
```

### Pagination and sorting

List endpoints paginate with **offset** and sort through a **per-endpoint
allowlist**. The reusable pieces live in `app/pagination.py`.

| Parameter | Default          | Bounds | Meaning                                              |
| --------- | ---------------- | ------ | ---------------------------------------------------- |
| `limit`   | `20`             | 1–100  | Page size                                            |
| `offset`  | `0`              | ≥ 0    | Rows to skip                                         |
| `sort`    | endpoint default | –      | Comma-separated fields; a leading `-` means descending |

Responses use the `OffsetPage` envelope:

```json
{ "items": [ ... ], "total": 137, "limit": 20, "offset": 40 }
```

`total` counts every row matching the filters (ignoring pagination) so a client
can render "page X of Y"; it costs an extra `COUNT` query. Example:
`GET /v1/organizations?limit=20&offset=40&sort=-created_at`.

Implementation notes:

- Resolve `sort` against a per-endpoint allowlist and pass the result to
  `select(...).order_by(...)`. Never build `ORDER BY` from raw client input.
- A list endpoint receives its parameters as one model:
  `Annotated[ListParams, Query()]`. FastAPI expands a single model into query
  parameters but only handles one per endpoint, so `ListParams` combines
  `PaginationParams` and `SortParams`. Unknown parameters are rejected, so a typo
  is a `422` instead of a silently ignored filter.
- `SortParams.order_by(...)` always appends a unique tiebreaker (`id`), so the
  order is total and rows cannot repeat or vanish between pages.
- Filter rows the endpoint owns with typed query parameters, and keep
  soft-deleted rows out with `deleted_at IS NULL`.
- Public block and image readers have no approval gate: an artifact is published
  after moderation and, for images, the image judge. Pictures made for a block
  and pictures made by a standalone image task join the same library.
  `/v1/admin/components` and `/v1/admin/images` expose the rows for operator
  inspection. Operator deletion is a hard delete through
  `app/deletion/service.py`: hide, purge Cloudinary, delete the row, forget its
  vector and write a `deletion_audit` row. Reports keep a snapshot because their
  foreign keys are set to null when the target disappears.
- Text search: `ILIKE '%term%'` is fine for small tables; move to a `pg_trgm`
  or full-text index when it matters.

#### Keyset (cursor) pagination

Offset is the default, but it has two weaknesses: it is unstable under
concurrent writes (rows can repeat or be skipped) and `OFFSET` degrades with
depth. For **large or high-churn collections** — infinite scroll, activity
feeds, a native app — use keyset instead:

- Sort by a **unique, ordered** key: `created_at` plus the `id` tiebreaker, or a
  time-ordered UUID (v7) as the key on its own.
- Accept an opaque `cursor` (base64 of the last row's sort values) instead of
  `offset`, and return `{ "items": [ ... ], "next_cursor": "..." | null }`.
- Compare with a row expression: `WHERE (created_at, id) < (:last_created_at, :last_id)`.
- Fetch `limit + 1` rows to know whether a next page exists.
- The cursor is tied to the sort: reject it if the `sort` changed.

Keyset cannot return `total` or jump to page N; that is the price of being
stable and fast at any depth. Pick **one mode per endpoint**, never both.

## Organizations and tenancy

Organizations and memberships are inherited from the `mcp-stack` template. They
exist in the schema and have endpoints, but GenBlocks does not use them in any
public flow: the catalogue is public and a task belongs to the user who queued
it. Do not add `organization_id` to blocks, images or tasks, and do not resolve
the operator queue through an organization role.

If you build on the template, the tenant rules are still there: the organization
comes from the caller's membership, a non-member gets a 404 rather than a 403,
and roles are validated in the database. See `app/organizations/dependencies.py`
and `app/organizations/models.py`.

## Authentication notes

- **Supabase Auth owns the user lifecycle**: signup, email verification, password reset, social login and sessions. This service stores no passwords and issues no tokens.
- Access tokens are **asymmetric JWTs** (RS256 by default, ES256 also accepted). `app/auth/verifier.py` validates the signature against the project's **JWKS**, plus the `iss`, `aud` and `exp` claims, so tokens from another project — or expired ones — are rejected.
- **Just-in-time provisioning**: the first time a valid token is seen, `app/users/service.py` creates the local profile keyed by `supabase_user_id` (the token's `sub`, a stable UUID). Later requests keep the mirrored email in sync. Concurrent first requests are safe: the insert is `ON CONFLICT DO NOTHING` on `supabase_user_id`, so a race never surfaces as a 500. The profile's own `id` is what you should use for relations.
- **Deleting an account** is a hard delete of the local profile (`DELETE /v1/users/me`). The Supabase identity is removed separately by the frontend, through the admin API. Since the row is gone — and `email` is not unique — the same address can sign up again.
- `app/auth/dependencies.py` resolves the bearer token into `TokenClaims`; `app/users/dependencies.py` resolves those claims into a local `User`. Inactive or unverified checks are handled by Supabase at authentication time, not here.

## Authorization notes

Authentication answers *who is this*; authorization answers *what may they do*. They
are separate modules on purpose: `app/auth/` verifies the token, `app/authz/`
decides what the caller may do with it.

For GenBlocks, authorization lives in the domain services: the public catalogue
is read-only, a task is scoped to `created_by`, and the operator queue is gated by
`ADMIN_EMAILS`. The organization permission table remains from the template and
applies only to the organization endpoints:

`app/authz/permissions.py` keeps that template policy in one table:

```python
ROLE_PERMISSIONS = {
    MembershipRole.OWNER: frozenset({Permission.ORGANIZATION_READ, Permission.ORGANIZATION_UPDATE}),
    MembershipRole.MEMBER: frozenset({Permission.ORGANIZATION_READ}),
}
```

Three properties worth keeping when you add permissions:

- **Deny by default.** `require(...)` looks the role up and grants nothing when the
  table does not list it, so a role that reaches the database without a policy is
  powerless instead of accidentally powerful.
- **The check cannot be skipped.** `app/organizations/dependencies.py` exposes a
  dependency *factory*: an endpoint asks for
  `Depends(require_membership(Permission.ORGANIZATION_UPDATE))` and receives the
  organization only if the caller is a member and their role grants it. There is no
  way to resolve an organization without naming the permission it needs.
- **Two rules, two statuses.** A caller who is not a member gets a **404**, because
  a 403 would confirm that the organization exists. A member whose role is not
  enough gets a **403**.

`require(...)` raises a domain error (`PermissionDenied`) rather than an
`HTTPException`, and `app/main.py` translates it. The MCP tools call the same code
and are not HTTP, so the translation belongs at the edge.

### One token, two doors

A Supabase access token carries a `client_id` claim when it was issued to an OAuth
client — an AI agent — and no such claim for the application's own login. Those
tokens belong to the agent door (the MCP server), and `app/authz/dependencies.py`
is where the API turns them away with a **403 rather than a 401**: the token is
valid and re-authenticating would produce the same one, so a client should not
retry. This is what keeps an agent from reaching the API surface directly: the
tools are the interface designed for machine callers, and accepting an agent token
here would make them optional.

### What each layer protects

Four layers, each answering a different question. Worth having straight, because
it is easy to build the wrong one and consider the job done:

- **Supabase Auth answers *who*.** It owns the user lifecycle and signs the token;
  `app/auth/verifier.py` checks the signature against the JWKS plus `iss`, `aud`
  and `exp`. Every layer below trusts what it returns and nothing else.
- **The door answers *which caller it serves*.** The API admits only first-party
  tokens (`app/authz/dependencies.py`); the MCP server takes the ones Supabase
  issued to an agent (`app/mcp/auth.py`), and does not turn a first-party one away.
  Neither door re-verifies the token, and neither is a permission check.
- **The role answers *what that caller may do, to this row*.** For the template
  organization endpoints it lives in `app/authz/permissions.py`; for GenBlocks it
  lives in the domain services, where a task is scoped to its owner and the
  operator queue is gated by `ADMIN_EMAILS`. Both doors reach the same service,
  which is why an operation with no service behind it has no authorization at all.
- **The tool answers *what a machine caller may ask for*.** Caller from the token,
  arguments validated by the schema, result typed. Nothing else.

There is deliberately **no per-tool and no per-client permission layer**. An agent
acts as the user whose token it carries, so its limits are that user's limits; a
table saying which tools a given client may use would be a rule the API does not
have, kept in a place the API cannot see.

## MCP server

`app/mcp/` is a second door into the same domain, built with
[FastMCP](https://gofastmcp.com). AI agents — Claude Code, Cursor, ChatGPT —
authenticate as your users through Supabase Auth's OAuth 2.1 server and call the
tools it exposes.

It is a **separate service**, not a route on the API: `docker-compose.yml` has an
`mcp` service whose entrypoint is `app/mcp/main.py`. It shares the domain layer
with the API — so a tool cannot do anything the API would not allow — and it
verifies tokens with the same `app/auth/verifier.py`.

### Its own environment

In production the MCP process gets its own environment, not a copy of
`backend/.env`: `backend/mcp.env.example` lists what it actually uses. It needs
the database, Supabase, the moderation keys and the shared task quota, and it can
use Resend for policy notices. It does **not** need Cloudinary, Modal, BFL,
Voyage, Chroma or Langfuse credentials, and a database role that can read the
vault and write tasks is enough. The local compose file still shares
`backend/.env` for convenience; that is a development shortcut, not the
production shape.

| Endpoint                                        | Description                           |
| ----------------------------------------------- | ------------------------------------- |
| `POST /mcp`                                     | The MCP endpoint (Streamable HTTP)    |
| `GET /.well-known/oauth-protected-resource/mcp` | Protected resource metadata (RFC 9728) |
| `GET /health`                                   | Liveness probe (never authenticated)  |

A client needs nothing but the URL: it reads the metadata from the 401 challenge,
registers itself with Supabase (dynamic client registration) and the user approves
the access once. Point Claude Code at `http://localhost:8001/mcp`.

The screen the user approves on lives in the frontend, at
`frontend/app/oauth/consent` — which is what Supabase's **Authorization Path**
has to point at.

`stateless_http` is on (`app/mcp/main.py`) because MCP clients do not forward
cookies, so a load balancer cannot pin them to the instance holding their session.
Without it the server only works as a single instance.

That choice has a consequence worth knowing before writing a tool: with no session
there is also no back-channel, so a tool cannot interrupt the call to ask the
client for anything. `ctx.elicit()`, sampling and roots all fail with
`NoBackChannelError`. Asking the user therefore has to go the other way — the tool
returns the request, the call ends, and the client calls again with the answer,
which is what the protocol's 2026-07-28 era introduced for exactly this case.
A client that negotiated an older era cannot be asked at all, unless the client
can be told to probe for the modern one.

This is not a workaround for our configuration. The same revision removed the
back-channel from the protocol and deprecated the features that leaned on it —
roots, sampling, logging — so the handshake form is the path being retired, not the
safe one to build on. The round-trip is how asking will be done from here.

### Adding a tool

A tool is a thin adapter, and the steps are short. `whoami` in `app/mcp/tools.py`
is the pattern to copy from.

1. Write the function and give it a return type. That type is the contract: a
   Pydantic model becomes the tool's `outputSchema`, so the caller gets data it
   can read rather than a sentence it is meant to obey.
2. Take the caller from the access token (`get_access_token()`), never from an
   argument. Arguments are chosen by a model, and a model can be talked into
   lying.
3. Put no rule in the tool: call a domain service and let it check the role. That
   is the only authorization there is — see "What each layer protects".
4. If it needs to ask the user something, asking means *returning* on one round and
   resuming on the next, because there is no back-channel to ask on: the paragraph
   above on `stateless_http` is why.
5. Decorate it with `@mcp.tool`. The decorator registers the tool at import time
   and hands the function back unchanged, so it stays directly callable. Importing
   `app/mcp/tools.py` — the entrypoint does it — is what runs the decorators.

Two conventions worth keeping:

- **A published name is never renamed.** Clients pin tool names in their own
  configuration and a conversation may be mid-flight, so a breaking change
  publishes a new name (`list_organizations_v2`) beside the old one and lets
  callers move at their own pace.
- **A tool is not a place for a rule.** If you find yourself writing an `if` that
  is about who may do something, it belongs in the service the tool calls.

Everything else about MCP — elicitation, background tasks, sampling, middleware —
belongs to FastMCP, and its documentation is the reference.

### The one thing this door cannot check

Supabase does not support **RFC 8707 resource indicators**, so an access token is
not bound to a specific resource: one minted for the MCP server is also accepted
by the API, and the reverse. The API compensates by accepting only first-party
tokens (`app/authz/dependencies.py`), and FastMCP's own warning about the missing
audience check does not appear because we hand it our verifier (`app/mcp/auth.py`)
instead of letting it build one. It is a trade-off we accepted knowingly, not
something we overlooked.

### A migration to expect

The 2026-07-28 revision starts moving client identification away from **Dynamic
Client Registration** and towards **Client ID Metadata Documents**. That
registration flow belongs to Supabase's OAuth server, not to this code: keeping up
means watching Supabase, not changing anything here. It is written down because it
is the kind of thing that looks like a bug when it starts happening.

## Generation worker

A queued row is claimed with `FOR UPDATE SKIP LOCKED`, marked `running`, and each
checklist step is written as the pipeline reaches it. The four steps are
retrieving references, generating the block, judging the attempt and publishing
the block. Images use their own four: checking the prompt, generating, judging
and filing.

**Where it runs.** In development the API process owns the worker, so the whole
loop starts with one command. In production it runs as a Modal function
(`app/tasks/modal_app.py`), because a block takes minutes to build — longer than
a service that scales to zero can promise a background process — and because a
run should not be competing with the API for CPU while somebody is browsing.

The deployed worker is one pass: reconcile, claim until the queue is empty, exit
(`python -m app.tasks.worker`). It is billed per second, so a loop that waited
for work would be a loop paying to wait; the queue is Postgres and the next run
picks up whatever arrived in the meantime. Two things start it: the API wakes it
the moment a row is committed (`app/tasks/trigger.py`, which never lets a failed
wake-up fail the request), and a one-minute schedule catches anything a failed
wake-up left behind.

**Reconciliation.** Runs overlap, so "a task is running and no process could be
working on it" is not something a boot can decide in production. Age decides it:
`interrupt_orphaned_tasks` closes a running task only once it has been running
longer than `WORKER_STALE_SECONDS` (45 minutes by default), which stays above the
worker function's own 30-minute timeout so a sweep can never interrupt live work.
In development, where the API is the only owner, the boot still interrupts every
running task.

Postgres is both the queue and the source of truth, so there is no broker to
drift from the task row the UI reads.

## The type shelf

A block ships its own typeface, so the families are dependencies of the scaffold
rather than a stylesheet from a CDN: `@fontsource/*` packages in
`app/harness/scaffold/package.json`, imported one latin weight at a time by the
block itself.

- **The catalog** is `app/harness/fonts.py`: package, family, group, weights,
  italic and one line of character. It is the only place a family is declared.
- **The document** the agent reads is `app/harness/skills/fonts.md`. Its table is
  generated from the catalog by `uv run python -m app.harness.fonts`, and a unit
  test fails when the two disagree — so the shelf the model is told about is the
  one the image installs.
- **Adding a family** is four steps: `npm install @fontsource/<family>` in the
  scaffold, a `Family` entry, regenerate the document, and
  `modal deploy app/harness/modal_app.py` — the image installs the scaffold's
  dependencies at build time, so an undeployed package does not exist for a run.
- **The build** keeps the one-document promise: a small Vite plugin drops the
  `woff` fallback Fontsource ships beside every `woff2`, and `assetsInlineLimit`
  inlines the remaining file as a data URL. The preview policy already allows
  `font-src data:`, so no font is ever a sibling request.

The families are all OFL or equivalent, which is what makes them redistributable:
the block's install line is the package name, and the visitor gets the same file
the render was photographed with.

## The design plan

The visual half of a brief is decided before the artifact exists, by a second spec
call whose answer is a closed vocabulary rather than prose: `app/design/plan.py`.

- **What it decides**: direction, composition, hierarchy, display and body family
  (resolved to a package from the shelf), one accent with the reason it belongs to
  the subject, surface treatment, density, one signature detail, and what this
  block in particular should avoid.
- **Where it is stored**: `components.spec["design"]`, with the packages it
  resolved to. A family that is not on the shelf is refused at the spec, before a
  container or a picture is paid for.
- **Who reads it**: the builder (in the ask), the judge (with the brief), and the
  three advisory checks in `app/harness/checks.py`, which compare the project with
  the plan and report drift without blocking a run.
- **How it stays varied**: the planner sees the newest blocks of the same type and
  is asked to differ on at least one axis, or to defend the repetition in its
  rationale. Variety is a property of the catalogue, so it is decided upstream: a
  judge that sees one block at a time cannot measure it.
- **Extending it**: a new direction, composition or accent is an enum and a line in
  the notes of `plan.py`; the prompt is generated from them, so the schema and the
  text cannot disagree.

## Conventions

- Imports are **absolute** and rooted at the `app` package (`from app.users.service import ...`). Avoid relative imports so the dependency direction stays easy to read.
- Every directory is a regular package with an empty `__init__.py`. Nothing is re-exported there on purpose, so import cycles remain visible instead of being hidden behind package-level imports.
- The `app` package is imported from the working directory (`backend/`). Run the CLI commands from `backend/` so `app` is on `sys.path`.

## CORS

Allowed origins come from the `CORS_ORIGINS` setting (comma-separated), read in
`app/main.py`. The default is `http://localhost:3000` for local development — set
your real frontend domain(s) before deploying.

## Notes

- `app/db/models.py` defines a shared `BaseModel` with a UUID primary key plus `created_at`, `updated_at`, and `deleted_at` columns for every table.
- The `User` model is a **profile**: `supabase_user_id` (unique, links to Supabase), `email`, `full_name`. Add your own fields and relations on top of `id`.
- `Organization` and `Membership` (`app/organizations/models.py`) remain from the template. The GenBlocks catalogue and tasks do not use them; see "Organizations and tenancy".
- `email` is **indexed but not unique**: it mirrors a Supabase-owned value, so Supabase is the source of truth. The identity key is `supabase_user_id`.
