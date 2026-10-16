# Backend — FastAPI

The API for the [MCPStack](../README.md). It exposes the application's domain data (the user profile) on top of an async SQLAlchemy / PostgreSQL stack.

Authentication is delegated to [**Supabase Auth**](https://supabase.com/docs/guides/auth), which owns credentials, email verification, social login and sessions. This service is a **resource server**: it verifies the Supabase access token (an asymmetric JWT) against the project's **JWKS** and provisions a local profile the first time it sees a user. It never issues tokens or stores passwords.

## Tech stack

- **FastAPI** — HTTP layer
- **SQLAlchemy 2.0** (async) with **asyncpg** — ORM and driver
- **Alembic** — database migrations
- **Pydantic v2 / pydantic-settings** — schemas and configuration
- **PyJWT** with **cryptography** — verifying Supabase access tokens (RS256/ES256)
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
│   ├── demo/
│   │   ├── graph.py           # The agent loop, and the scripted decisions
│   │   ├── tools.py           # The tools the agent carries itself
│   │   ├── runner.py          # One run: a refusal at the door vs a fault
│   │   ├── schemas.py         # The shapes the page reads
│   │   └── router.py          # POST /demo/run, public on purpose
│   ├── health/
│   │   └── router.py          # Liveness, readiness and the MCP warm-up
│   ├── middleware/
│   │   └── request_id.py      # Request id + structured access log
│   ├── db/
│   │   ├── session.py         # Async engine + session factory
│   │   └── models.py          # Declarative Base and BaseModel (id, timestamps)
│   ├── api.py                 # Versioned API entrypoint (mounts /v1)
│   ├── settings.py            # Settings loaded from .env
│   ├── logging_config.py      # structlog setup (dev text / prod JSON)
│   ├── pagination.py          # Offset pagination + sorting for list endpoints
│   └── main.py                # FastAPI app, routers, CORS
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
```

PostgreSQL comes from the repository's `docker-compose.yml` (see [Run with Docker](../README.md#run-with-docker)), so `DATABASE_URL` must point at the host-mapped port (`localhost:5432`).

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
| `MCP_INTERNAL_URL`      | No       | `http://localhost:8001` | Where the playground reaches the MCP server as a client.             |
| `CORS_ORIGINS`          | No       | `http://localhost:3000` | Comma-separated browser origins allowed to call the API.             |

Settings are defined in `app/settings.py` and loaded from `backend/.env`.

## Running the server

```bash
# Development (auto-reload) — http://localhost:8000
uv run fastapi dev

# Production
uv run fastapi run
```

The OpenAPI docs are at `/docs`, and the raw schema at `/openapi.json`.

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

On **Render** or **Railway**, set the health check path to `/health`. An external monitor can point at the same path for alerts. In local development, `docker-compose.yml` probes `/health` and the frontend waits for the backend to be healthy.

The page calls `/warmup` through the frontend's own `/api/warmup` route, on every visit, so a deployment that stops idle services wakes them while the visitor is still reading. See [Sleeping platforms](../README.md#sleeping-platforms) for what that costs.

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

An **organization** is the tenant: every domain row you add belongs to exactly
one, and a **membership** grants a user a role (`owner` or `member`) inside it.
Authorization resolves permissions through memberships, never through the user,
so adding a resource means adding an `organization_id` and filtering by the
caller's membership.

Rules these endpoints follow:

- **The tenant comes from the token, never from the request.** A caller's
  organizations are resolved from their memberships, so no request can ask for a
  tenant the caller does not belong to.
- **A non-member gets a 404, not a 403.** A 403 would confirm that the
  organization exists, which leaks the tenant map to anyone who can guess an id.
  `app/organizations/dependencies.py` is the single place that rule lives.
- **Roles are validated in the database too** (`ck_memberships_role_valid`), so a
  manual query cannot introduce a role the authorization layer does not know.

Creating an organization writes the organization and its owner membership in one
transaction: an organization nobody belongs to would be unreachable, because
every read is gated on a membership.

Two things to decide when you adapt this:

- Deleting a profile cascades to its memberships, but an organization whose last
  owner is deleted is left with no members. Decide what your product does: block
  deletion for sole owners, transfer ownership, or delete the tenant.
- Organizations have no UI yet; they are managed through the API.

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

**Permissions are scoped to an organization**, because every domain row hangs off
one: what a caller may do comes from their role in the owning organization, never
from the caller's identity. `app/authz/permissions.py` keeps the whole policy in
one table:

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
- **The role answers *what that caller may do, to this row*.** It is the only
  fine-grained layer. It lives in `app/authz/permissions.py` and in the domain
  services, and both doors reach it by calling the same service — which is why an
  operation with no service behind it has no authorization at all.
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

## Playground

The playground is the fourth way into this domain, and the only client you can watch
from a browser. It sits on the landing, before the client instructions, and it exists so a visitor
can see
an agent reach their own data with their own account, without installing a client
first.

It runs a real agent, built the way the LangGraph quickstart builds one
(`app/demo/graph.py`): a state that carries messages, a node that decides which tool
runs next, and a node that runs it. The loop is the library's own pieces — `ToolNode`
runs the tools and `tools_condition` decides whether there is another round — so
there is no hand-rolled dispatcher to keep in step with them. The decisions are a list
and nothing calls a model, which the page says out loud, so nobody mistakes the trace
for a model thinking.

LangGraph and the MCP adapter are core dependencies, because the playground runs
inside the API and goes out to the server on every run. No model provider is, because
nothing here calls a model: the decisions are a list. Whoever adds one brings their
own, and the loop it drives is the same.

The agent carries three tools. Two live in the agent's own code and need nobody's
permission: one reads the clock, and one stops the run to ask the visitor before anything
goes out. The third is the server's, and where the run gets it depends on the caller: with
a token it lists the catalogue with `MCPAdapter` and hands the graph whatever the server
publishes, and without one there is no catalogue to ask for, so it calls the tool the plan
names and the door answers. The name appears in the plan either way; only the description
comes from the server.

Asking is where the graph keeps its place. The tool calls `interrupt`, which stops the run
and hands the question to whoever is looking at the page; the graph saves where it got to,
the answer comes back on the next request with the id of the same run, and the run carries
on from there. That checkpointer is in memory (`app/demo/runner.py`), which is what one
process can offer: a deployment serving many runs at once would keep those somewhere it
can expire them.

- `POST /v1/demo/run` is **public**, which is unusual for this API and deliberate.
  Anonymous is the interesting case: the run asks the visitor to approve the call that
  goes out, and then the server shows its catalogue to nobody without a token, so the
  tool is called by name and the door refuses it. The page shows that refusal next to a
  way to sign in. A route that demanded a token would hide the half of the story worth
  telling.
- The browser never sees the token. The Next.js server holds the session and forwards
  it here, and this service forwards it to the MCP server. The only thing the endpoint
  does with a token is pass it on; no domain rule runs behind it.
- The usual rules still hold: a token that does not verify is a 401, and a token
  issued to an OAuth client is rejected, because this API never acts on one.

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
- `Organization` and `Membership` (`app/organizations/models.py`) are the tenant model: resources belong to an organization and roles are resolved through memberships. See "Organizations and tenancy".
- `email` is **indexed but not unique**: it mirrors a Supabase-owned value, so Supabase is the source of truth. The identity key is `supabase_user_id`.
