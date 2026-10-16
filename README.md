# MCPStack

**The production-ready foundation for agent-native SaaS.**

[![Backend](https://github.com/jonathanfreiredev/mcp-stack/actions/workflows/backend.yml/badge.svg)](https://github.com/jonathanfreiredev/mcp-stack/actions/workflows/backend.yml)
[![Frontend](https://github.com/jonathanfreiredev/mcp-stack/actions/workflows/frontend.yml/badge.svg)](https://github.com/jonathanfreiredev/mcp-stack/actions/workflows/frontend.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

A full-stack template where **AI agents are first-class users of your product**. It ships the part that is tedious to get right: identity, an authorization layer, and an **MCP server** any MCP client can walk through, behind a consent screen the user approves.

Under the hood it pairs a **Next.js 16** frontend with a **FastAPI** backend on **PostgreSQL**, and delegates authentication to [**Supabase Auth**](https://supabase.com/docs/guides/auth) (OAuth 2.1 / OIDC). Supabase owns credentials, email verification, social login and sessions, while the backend is a **resource server** that verifies the access token against the project's JWKS. Signup, login, email verification, password reset, profile editing and password change all ship as working examples, so you start from a real end-to-end setup instead of a blank page.

## What you can build

![Identity issuing one access token two ways, a frontend and external agents such as Claude Code, Cursor, opencode or n8n, an MCP server, a FastAPI backend and PostgreSQL, with the token carried along each path](https://res.cloudinary.com/ddjovluur/image/upload/v1791981836/mcp-stack/diagram-architecture_yo10gf.png)

One access token, and two ways to get it: signing in, or approving an agent over OAuth. That one token opens two doors. The API serves your product; the MCP server serves agents, and it runs the same domain services the API runs, so an agent can never reach something your own code would not.

The difference between the two tokens is a single claim. Without `client_id` the token came from your own sign-in, and it can call the API and the MCP. With `client_id` it was issued to an agent: the API turns it away and only the tools answer. That is the whole separation between human and agent traffic, and it lives in one place.

The repository ships one tool, `whoami`, as a working example of that path. What you publish on top is yours.

## Quickstart

```bash
# One file per app, plus the stack's own: all three have to exist.
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker compose up
```

That brings up PostgreSQL, the API, the MCP server and the web app. The two apps
start on the example values, so fill in your Supabase project below to sign in. To watch the loop close, point an MCP client at the server:

1. Add the server to your client. The four clients this project documents are in [Connect your agent](#connect-your-agent) below.
2. Call the `whoami` tool. Your client opens a consent screen in the browser.
3. Approve it, and the tool answers with the profile behind the token.

Prerequisites, the manual path without Docker and every environment variable are below.

## Connect your agent

The MCP server listens on `http://localhost:8001/mcp`, and each client is told about it a different way. These are the four this project documents. Whichever you pick, the first call opens a consent screen in the browser, and the token that comes back can only reach the tools.

### opencode

```bash
opencode mcp add mcp-stack --global --url http://localhost:8001/mcp
```

Run it in your terminal. Drop `--global` to register the server for this project only, then run `/mcps`, pick `mcp-stack` and sign in. See [opencode MCP servers](https://opencode.ai/v2/docs/mcp-servers).

### Claude Code

```bash
claude mcp add --transport http mcp-stack http://localhost:8001/mcp
```

Run it in your terminal before you start Claude Code, then run `/mcp` inside it to sign in. See [Claude Code MCP](https://code.claude.com/docs/en/mcp).

### Cursor

Save this as `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` to have it in every project:

```json
{
  "mcpServers": {
    "mcp-stack": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

Then turn `mcp-stack` on in Cursor's MCP settings; it opens the browser to sign in. See [Cursor MCP](https://cursor.com/en-US/docs/mcp).

### n8n

Add an MCP Client Tool node under an AI Agent and paste `http://localhost:8001/mcp` as its endpoint, with the transport set to HTTP Streamable, which is the one this server serves. For authentication, pick OAuth2 and leave Dynamic Client Registration on, so n8n registers itself and opens the same consent screen. See [n8n MCP Client Tool](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/).

The landing runs this same agent in the browser, so you can watch the door refuse an
anonymous call before you install anything.

## Tech stack

| Layer             | The value                                                                    | Stack                                                                                                                    |
| ----------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Product UI**    | Server-rendered pages, with one schema validating each input on both sides.  | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Motion, React Hook Form, Zod, next-safe-action |
| **Identity**      | Credentials, sessions and agent authorization, all delegated.                | Supabase Auth (OIDC), `@supabase/ssr`, asymmetric JWTs verified against JWKS                                             |
| **API**           | One validated HTTP door into the domain, async end to end.                   | FastAPI, Pydantic v2, SQLAlchemy 2 (async), asyncpg, PyJWT                                                               |
| **Agent access**  | A second door into the same domain, user approval included.                  | FastMCP, MCP over streamable HTTP, OAuth 2.1 consent                                                                     |
| **Data**          | The tenant model, versioned and reversible.                                  | PostgreSQL 17, Alembic                                                                                                   |
| **Observability** | Logs you can read in dev and ship as JSON in production.                     | structlog, request id and access log middleware                                                                          |
| **Engineering**   | Nothing merges unlinted or untested, and the whole loop runs in one command. | pytest, Vitest, Playwright, MSW, ruff, ESLint, Prettier, Docker Compose, GitHub Actions                                  |
| **Playground**    | See the agent work in the browser, with no client to install.                | LangGraph, MCPAdapter as the client                                                                                      |

Domain data is **multi-tenant**: every row belongs to an organization, and access is resolved through the caller's membership in it. That is what makes the authorization layer meaningful. See "Organizations and tenancy" in the [backend README](backend/README.md).

## Repository structure

```
.
├── backend/                 # FastAPI application (resource server)
│   ├── app/
│   │   ├── auth/            # JWT verification + bearer dependency
│   │   ├── authz/           # Roles, permissions and the policy table
│   │   ├── users/           # Profile model, schemas, JIT provisioning, /users router
│   │   ├── organizations/   # Tenant model (organization + membership), /organizations router
│   │   ├── mcp/             # MCP server for AI agents (runs as its own service)
│   │   ├── demo/            # The playground agent (LangGraph, MCPAdapter)
│   │   ├── health/          # Liveness + readiness probes
│   │   ├── middleware/      # Request id + structured access log
│   │   ├── db/              # Async engine, session, base model
│   │   ├── api.py           # Versioned API entrypoint (mounts /v1)
│   │   ├── settings.py      # Pydantic settings (reads .env)
│   │   ├── logging_config.py # structlog setup (text in dev, JSON in prod)
│   │   └── main.py          # App entrypoint, CORS, routers
│   ├── alembic/             # Database migrations
│   ├── tests/               # Unit + integration tests
│   ├── Dockerfile           # Dev image (+ production stage)
│   └── pyproject.toml       # Dependencies (managed with uv)
│
├── frontend/                # Next.js application
│   ├── app/                 # App Router pages, layouts, confirm + OAuth consent routes
│   ├── components/          # UI, auth and playground components (shadcn/ui based)
│   ├── server/              # Server actions, schemas, session helper
│   ├── lib/                 # Env validation, Supabase client, safe-action, providers
│   ├── e2e/                 # Playwright end-to-end tests
│   ├── public/              # Static assets
│   ├── proxy.ts             # Refreshes the Supabase session per request
│   ├── Dockerfile           # Dev image
│   └── package.json         # Dependencies (managed with pnpm)
│
├── .github/workflows/       # CI (backend + frontend)
├── docker-compose.yml       # Local development stack
└── LICENSE                  # MIT
```

## Prerequisites

- **Node.js** 20+ and **pnpm**
- **Python** 3.14+ and [**uv**](https://docs.astral.sh/uv/)
- **Docker** or **Podman** for the containerized stack (the database, API and web app)
- A **Supabase project** (free tier is enough)

## Getting started

### 1. Supabase

Create a project and configure auth (enable Email and, optionally, Google; set the Site URL and redirect URLs to `/auth/confirm`). Copy the project URL and anon key — you will paste them into the frontend env. The full walkthrough is in [`frontend/README.md`](./frontend/README.md#supabase-setup).

### 2. Backend

```bash
cd backend

# Install dependencies
uv sync

# Create your environment file and set SUPABASE_URL
cp .env.example .env

# Apply database migrations
uv run alembic upgrade head

# Run the dev server on http://localhost:8000
uv run fastapi dev
```

The database comes up with the rest of the stack through `docker compose up` — see [Run with Docker](#run-with-docker).

Interactive API docs are available at http://localhost:8000/docs.

### 3. Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Create your environment file and set the Supabase URL / anon key
cp .env.example .env

# Run the dev server on http://localhost:3000
pnpm dev
```

Open http://localhost:3000 and sign up. Supabase sends a verification email (check its logs while developing) — open the link, then log in.

## Run with Docker

`docker-compose.yml` is a **local development** stack: PostgreSQL plus the API and the web app, with the source mounted and the dev servers running with reload.

```bash
cp .env.example .env                          # Postgres credentials for the stack
cp backend/.env.example backend/.env          # what the API reads
cp frontend/.env.example frontend/.env        # what the web app reads
docker compose up
```

A one-shot `migrate` service runs `alembic upgrade head` before the API starts, so the schema is always up to date. Like the API service it mounts the source, so a migration you just wrote is applied on the next `docker compose up` instead of waiting for a rebuild.

Three files supply the environment, and each has one job:

- **`.env`** (root) — the Postgres credentials. Compose reads it for variable substitution, so it is the source of truth for the database the stack runs on.
- **`backend/.env`** and **`frontend/.env`** — what the API and the web app read (`env_file` in `docker-compose.yml`). Only the Docker-internal hostnames (`postgres`, `backend`) are overridden.

Because the containers build their `DATABASE_URL` from the root `.env`, **`backend/.env` must carry the same password** if you also want to run Alembic or pytest from the host. `POSTGRES_PASSWORD` is required on purpose — the compose file gives it no default — so a missing `.env` fails loudly instead of silently picking one.

The stack also runs the **MCP server** on port 8001: the door AI agents such as Claude Code, Cursor, opencode or n8n come through. It is a separate service that shares the domain and the token verification with the API — see the [MCP server](backend/README.md#mcp-server) section of the backend README.

Deployment is not handled here: the frontend goes to Vercel (which builds it natively) and the backend to its own service. The `backend/Dockerfile` also has a production stage if you deploy it as a container.

## Health checks

The backend exposes three unauthenticated probes for orchestrators, load balancers and uptime monitors:

- `GET /health` — **liveness**: the process is running. It checks nothing external, so a failure means "restart the container".
- `GET /health/ready` — **readiness**: pings the database with `SELECT 1` and returns `503` when it is unreachable, so traffic is routed away without restarting the process.
- `GET /warmup` — **wake-up**: asks the MCP server whether it is up, which has the side effect of starting it. It always answers `200` with `{"api": ..., "mcp": ...}` so the page can poll it and report what is still coming.

On **Render** or **Railway**, set the health check path to `/health`. Locally, `docker-compose.yml` probes `/health` and the frontend waits for the backend to be healthy.

### Sleeping platforms

The playground is worth having awake and worth not paying for, so the deployment this project targets is a platform that stops idle services (Railway Serverless, Cloud Run, Render) with the page waking them:

- The **landing pings `/warmup` when it mounts**, through the frontend's own `/api/warmup` route. Nobody visiting the site by accident pays for it: the first visitor of an idle period starts both containers back up while they are still reading, and a tab that is hidden is not asked at all.
- **Nothing in the browser calls the API directly.** `BACKEND_URL` stays a server-side address, which is what lets it be a container name in compose and a private hostname anywhere else.
- The **API runs a single instance on purpose**: a run that stopped to ask a question lives in the process, so a second one would answer that the run does not exist.
- The engine uses **`NullPool`** (`app/db/session.py`): a pool holding connections open is a trickle of traffic, and a platform that decides to sleep from traffic would never see the service go idle.

The honest cost is the first visitor of an idle period. They get a notice saying the demo is waking, and their first run waits for it rather than failing.

## Environment variables

### `.env` (root)

Read by `docker-compose.yml` for variable substitution, so it is the source of truth for the database the stack runs on. Start from `.env.example`.

`POSTGRES_PASSWORD` deliberately has no default in the compose file: a missing `.env` fails loudly instead of silently picking one. It is also only applied the first time the Postgres volume is created, so changing it later requires recreating the volume (`docker compose down -v`). For Alembic or pytest runs from the host, `backend/.env` must carry the same password.

| Variable            | Required | Description                                                          |
| ------------------- | -------- | -------------------------------------------------------------------- |
| `POSTGRES_USER`     | No       | Role the container creates (default `postgres`).                     |
| `POSTGRES_PASSWORD` | Yes      | Password for that role. The containers build `DATABASE_URL` from it. |
| `POSTGRES_DB`       | No       | Database the container creates (default `mcpstack`).                 |

### `backend/.env`

| Variable                | Required | Description                                                                 |
| ----------------------- | -------- | --------------------------------------------------------------------------- |
| `DATABASE_URL`          | Yes      | Async PostgreSQL URL, e.g. `postgresql+asyncpg://postgres:password@localhost:5432/app`. |
| `SUPABASE_URL`          | Yes      | Supabase project URL. Used to derive the issuer and the JWKS endpoint.       |
| `SUPABASE_JWT_AUDIENCE` | No       | Audience claim on access tokens (default `authenticated`).                   |
| `ENV`                   | No       | `production` (default) or `development`. Enables SQL echo when in development. |
| `LOG_LEVEL`             | No       | Minimum level for the application logs (default `INFO`).                     |
| `FRONTEND_URL`          | No       | Base URL of the frontend, used for redirects.                                |
| `MCP_BASE_URL`          | No       | Public URL of the MCP server, published in the OAuth discovery document.     |
| `MCP_INTERNAL_URL`      | No       | Where the playground reaches the MCP server as a client.                    |
| `CORS_ORIGINS`          | No       | Comma-separated browser origins allowed to call the API (default `http://localhost:3000`). |

### `frontend/.env`

| Variable                        | Required | Description                                             |
| ------------------------------- | -------- | ------------------------------------------------------- |
| `BACKEND_URL`                   | Yes      | Base URL of the FastAPI backend, e.g. `http://localhost:8000`. |
| `NEXT_PUBLIC_SUPABASE_URL`      | Yes      | Supabase project URL.                                   |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Yes      | Supabase publishable key (replaces the legacy anon key). |
| `SUPABASE_SECRET_KEY`                  | Yes      | Supabase secret key. **Server-only**; deletes a user's account. |
| `NEXT_PUBLIC_AUTH_PROVIDERS`    | No       | Enabled login methods (`email,google`). Default `email`. |
| `NODE_ENV`                      | No       | Set automatically by Next.js.                           |

Environment variables in the frontend are validated at startup with `@t3-oss/env-nextjs` (`lib/env.js`). The publishable and secret keys are Supabase's current keys; they replace the legacy `anon` and `service_role` keys (deprecated at the end of 2026).

## API reference

All endpoints live on the FastAPI backend. Protected routes expect an `Authorization: Bearer <supabase_access_token>` header. The browser never calls it directly: the Next.js server holds the session in a cookie and forwards the access token on the user's behalf.

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
| POST   | `/v1/demo/run`                   |      | Run the playground agent, or continue a stopped run     |

The application API is versioned under `/v1`. The health checks stay unversioned so a future `/v2` never breaks orchestrators.

Agents do not use this API: they go through the **MCP server** on port 8001, a separate service that shares the same domain and authorization rules.

Errors use FastAPI's default body (`{"detail": ...}`). Migrating to RFC 9457 ("Problem Details") is deliberately deferred until FastAPI supports it natively.

Authentication (signup, login, verification, reset) is handled by **Supabase Auth**, not this API.

## Authentication flow

1. The user signs up or logs in through a **server action**, which calls **Supabase Auth** (`@supabase/ssr`). The session is stored in cookies managed by the Next.js server.
2. `proxy.ts` refreshes the session on every request (Next.js 16 renamed `middleware` to `proxy`).
3. `getSession()` (`frontend/server/auth/auth.lib.ts`) validates the user with Supabase and fetches the profile from the backend, returning the session and user.
4. Protected server actions use `protectedProcedure`, which rejects the request when there is no valid session and forwards the Supabase access token to the backend.
5. The backend **verifies** the token against Supabase's **JWKS** (`iss`, `aud`, `exp`) and **provisions a local profile** keyed by the token's `sub` the first time it sees the user.
6. Supabase sends verification and password-reset emails; `frontend/app/auth/confirm/route.ts` handles the links and the OAuth callback.
7. **Account deletion** is a hard delete on both sides: the backend removes the local profile and the frontend then deletes the Supabase identity through the admin API. The email is freed, so the same address can sign up again.
8. **AI agents** authenticate through Supabase's OAuth 2.1 server: the app registers itself with dynamic client registration, the user approves it on the consent screen (`frontend/app/oauth/consent`), and the resulting token is accepted by the **MCP server**. The API refuses those tokens — an agent can only reach the tools. Connected agents are listed on the profile page, where they can be disconnected.

## Common commands

### Backend (`backend/`)

| Command                                            | Description                        |
| -------------------------------------------------- | ---------------------------------- |
| `uv run fastapi dev`                               | Start the dev server with reload   |
| `uv run fastapi run`                               | Start the production server        |
| `uv run alembic revision --autogenerate -m "msg"`  | Create a migration from model changes |
| `uv run alembic upgrade head`                      | Apply migrations                   |
| `uv run alembic downgrade -1`                      | Roll back the last migration        |
| `uv run ruff check .`                              | Lint the backend                   |
| `uv run ruff format .`                             | Format the backend                 |
| `uv run pytest`                                    | Run all backend tests              |
| `uv run pytest tests/unit`                         | Run unit tests (no database needed) |

### Frontend (`frontend/`)

| Command        | Description                     |
| -------------- | ------------------------------- |
| `pnpm dev`     | Start the dev server            |
| `pnpm build`   | Production build                |
| `pnpm start`   | Serve the production build      |
| `pnpm lint`    | Run ESLint                      |

## Continuous integration

GitHub Actions runs two path-filtered workflows, so a change in one app does not trigger the other:

- `.github/workflows/backend.yml` — lints, checks formatting, applies migrations and runs the tests against a PostgreSQL service container.
- `.github/workflows/frontend.yml` — lints, type-checks, runs the unit tests, builds the app and runs the Playwright end-to-end tests.

There are 93 backend tests, 76 frontend unit tests and 8 end-to-end tests.

## License

[MIT](./LICENSE) © 2026 [Jonathan Freire](https://jonathanfreire.com)
