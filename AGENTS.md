# AGENTS.md — GenBlocks

Guidance for AI agents working in this repository. Read this first, then the
root `README.md` for the product and the app READMEs for setup details.

GenBlocks is a public registry of generated UI blocks and stock images. A block
is built in a **Modal** sandbox by a LangGraph agent, scored by an independent
judge, and published only when every rubric threshold clears. The app pairs a
**Next.js 16** frontend with a **FastAPI** backend on **PostgreSQL**, delegates
identity to **Supabase Auth**, and ships an **MCP server** for external agents.

## Working agreements

These are standing instructions for this project. Follow them without being
asked again.

- **Never read or write `.env` or `.env.production`.** In any directory, under
  any circumstance. `.env.example` files are fine. If a change seems to require
  touching a real env file, stop and hand it back to the maintainer.
- **The root README describes the product.** `PLAN.md` holds the decisions and
  execution history; `DESIGN.md` is the visual source of truth; the backend and
  frontend READMEs cover setup for each app. For product behavior, the root
  README and `PLAN.md` win when an app README conflicts with them. Raise the
  conflict instead of copying the older claim.
- **Code is written in English:** identifiers, comments, filenames, commit
  messages, test descriptions. User-facing copy follows the product's own
  language.
- **Keep changes minimal and reversible.** Change only what the task requires.
  Do not refactor adjacent code unless asked.

### Working on the frontend

Before writing any frontend code:

1. **Review the design skills and use the ones the task needs.** Do this every
   time frontend work comes up, not just for "design" tasks. The design skills
   cover UI direction, motion, responsive behavior, accessibility, UI polish and
   visual critique.
2. **Use the shadcn skill before building a component from scratch.** Check what
   shadcn already offers and install the component; only custom-build what it
   does not provide. shadcn also ships **AI-interaction components** (e.g. chat
   and conversation primitives) that are a good fit for this product — prefer
   them over hand-rolled equivalents.
   - Add components with `pnpm dlx shadcn@latest add <component>` from
     `frontend/`.
   - shadcn config lives in `frontend/components.json` (style `base-nova`,
     Lucide icons). Primitives land in `frontend/components/ui/`.
3. **Treat `DESIGN.md` (repo root) as the source of truth for visual
   decisions.** Use its tokens through the Tailwind/shadcn utilities already
   wired in `frontend/app/globals.css`; never hardcode a color or radius.
   Follow its Do's and Don'ts: no gradients, glass, or shadow-for-depth; one
   filled primary action per screen; verdict colors stay functional; tabular
   numerals for figures. `globals.css` implements the tokens. If a token value
   changes, change `DESIGN.md` first, then update `globals.css` and the
   components in the same change.

`frontend/AGENTS.md` carries a Next.js-version warning. Heed it: this Next.js
release has breaking changes versus older training data, so read the bundled
guides under `frontend/node_modules/next/dist/docs/` before writing Next.js
code. `frontend/CLAUDE.md` just redirects there.

## Repository layout

```
.
├── AGENTS.md     # Agent guidance (this file)
├── DESIGN.md     # Visual system: source of truth for the UI
├── PLAN.md       # Execution plan: decisions, phases and production hardening
├── backend/      # FastAPI application (resource server) + MCP server
├── frontend/     # Next.js web app (product UI + OAuth consent screen)
├── docker-compose.yml   # Local stack: postgres, migrate, backend, mcp, frontend
└── .env.example         # Source of truth for the Postgres credentials
```

`README.md` at the root describes the product and the local loop. `backend/` and
`frontend/` each have their own README for setup and internals.

## Commands

Run the whole stack (Compose reads the root `.env` for the Postgres
credentials; all three env files must exist):

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up

docker compose exec backend python -m app.categories.seed
docker compose exec backend python -m app.seed.vault
```

### Backend — run from `backend/`

```bash
uv sync                                   # install dependencies
uv run fastapi dev                        # dev server on :8000
uv run alembic upgrade head               # apply migrations
uv run alembic revision --autogenerate -m "describe change"
uv run pytest                             # full test suite
uv run pytest tests/unit                  # no database required
uv run pytest tests/integration           # needs the test database
uv run ruff check .                       # lint
uv run ruff format .                      # format
uv run modal deploy app/harness/modal_app.py  # publish the sandbox
```

### Frontend — run from `frontend/`

```bash
pnpm install
pnpm dev            # dev server on :3000
pnpm build          # production build
pnpm lint           # ESLint
pnpm test:run       # Vitest, single run
pnpm test:e2e       # Playwright; needs the stack and the seed (install browsers once)
```

## Conventions

### Backend

- Imports are **absolute**, rooted at the `app` package
  (`from app.users.service import ...`). Avoid relative imports.
- Every directory is a regular package with an empty `__init__.py`; nothing is
  re-exported there on purpose.
- Run CLI commands from `backend/` so `app` is on `sys.path`.
- Authorization lives in the **services**, not the routers or tools. A tool or
  endpoint that writes its own `if` about who may do something is wrong: call
  the service and let it check the role.
- A published MCP **tool name is never renamed**; publish a new one beside it.
- When you add a model, import it in `alembic/env.py` so autogenerate sees it.

### The generation pipeline

- **Spec, harness and judge are separate stages.** The spec files a brief, the
  harness builds it, and the judge scores it. Do not let the harness score its
  own work or the judge edit the artifact.
- **The judge is a gate.** A block is published only when every dimension clears
  its threshold. Thresholds live in `app/settings.py`; the rubric text lives in
  `app/judge/rubrics/`. The judge is never told the thresholds.
- **The harness loop is bounded.** `look` returns the report and both renders;
  the budget counts looks, and an unchanged project returns the previous render
  without rebuilding. Keep the file allowlist in `app/harness/agent.py` and the
  static checks in `app/harness/checks.py` in step with the scaffold.
- **Modal holds no secrets.** The sandbox receives files and returns reports,
  renders and a preview document. It never gets database credentials or provider
  keys.
- **Rubrics and skills are versioned by content hash.** Editing either changes
  the version stamped on future runs, so an old score can be read against the
  text that produced it.
- **The conversational tools and MCP tools call the same services.** A tool is a
  thin adapter; authorization belongs to the service.

### Frontend

- Next.js App Router under `frontend/app/`; server-only logic in
  `frontend/server/` (server actions, schemas), pure helpers in `frontend/lib/`.
- Import through the `@/` alias.
- shadcn primitives belong in `frontend/components/ui/`.

## Domain model, in one line

The catalogue of blocks, images and categories is public. A **task belongs to
the user who queued it**, and the service checks that ownership. Organizations
and memberships remain from the template but are not part of the product flow;
do not add `organization_id` to public artifacts or use organization roles for
the operator queue. The API and the MCP server are separate transports over the
same services.

## Testing expectations

- Tests are part of the work: if a change touches logic, add or update tests
  unless told otherwise.
- Backend: pytest, split into `tests/unit` and `tests/integration` (real
  Postgres, forged Supabase tokens). Frontend: Vitest (`__tests__/`, MSW for the
  backend) and Playwright (`e2e/`).
- CI runs lint, format check, tests and build per app via
  `.github/workflows/backend.yml` and `frontend.yml`.

## Production state

- `SITE_URL` is required in the frontend's production environment. Auth links
  fail closed when it is missing; do not fall back to the request Host header.
- The MCP service gets its own environment. Start from
  `backend/mcp.env.example`, not the API's `.env`; production must not grant the
  agent-facing process the Cloudinary, Modal, BFL, Voyage, Chroma or Langfuse
  credentials it does not need.
- The task worker gets its own environment too, in `backend/worker.env.example`,
  and it is a **Modal function** in production (`app/tasks/modal_app.py`), not
  the API process. The API wakes it when a task is queued and a one-minute
  schedule is the safety net. Reconciliation there is by age
  (`WORKER_STALE_SECONDS`), because runs overlap: never make a boot interrupt
  every running task, which is only safe where the API is the sole owner.
- There is **no application-level rate limiter** by decision. The monthly task
  quota, provider spend caps and authenticated or verified accounts are the
  current boundary; an edge rule is the next lever if abuse appears. Revisit the
  decision only if an anonymous AI endpoint is introduced.
- `docker-compose.yml` is a development stack. Do not treat it as the production
  deployment.
- API docs are disabled unless `ENV=development`.

## Maintainer

Jonathan Freire — <https://jonathanfreire.com>
