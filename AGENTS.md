# AGENTS.md — GenBlocks

Guidance for AI agents working in this repository. Read this first, then the
`README.md` files in `backend/` and `frontend/` for depth on each app.

GenBlocks is a full-stack template where AI agents are first-class users of the
product. It pairs a **Next.js 16** frontend with a **FastAPI** backend on
**PostgreSQL**, delegates identity to **Supabase Auth**, and ships an **MCP
server** so agent traffic reaches the same domain through a consent screen.

## Working agreements

These are standing instructions for this project. Follow them without being
asked again.

- **Never read or write `.env` or `.env.production`.** In any directory, under
  any circumstance. `.env.example` files are fine. If a change seems to require
  touching a real env file, stop and hand it back to the maintainer.
- **Readmes are pending.** The `README.md` files still describe the
  `mcp-stack` template and are intentionally out of date until the web
  work starts. Do not treat them as the source of truth for naming yet.
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
   spot ink per screen; verdict colors stay functional; tabular numerals for
   figures. `globals.css` is derived from it — if a token value changes,
   change `DESIGN.md` first, re-run the linter, then re-export.

`frontend/AGENTS.md` carries a Next.js-version warning. Heed it: this Next.js
release has breaking changes versus older training data, so read the bundled
guides under `frontend/node_modules/next/dist/docs/` before writing Next.js
code. `frontend/CLAUDE.md` just redirects there.

## Repository layout

```
.
├── AGENTS.md     # Agent guidance (this file)
├── DESIGN.md     # Visual system ("Overprint") — source of truth for the UI
├── PLAN.md       # Execution plan: phases, decisions and model roster
├── backend/      # FastAPI application (resource server) + MCP server
├── frontend/     # Next.js web app (product UI + OAuth consent screen)
├── docker-compose.yml   # Local stack: postgres, migrate, backend, mcp, frontend
└── .env.example         # Source of truth for the Postgres credentials
```

Both `backend/` and `frontend/` have their own `README.md` with the full
structure, environment variables and architecture notes.

## Commands

Run the whole stack (Compose reads the root `.env` for the Postgres
credentials; all three env files must exist):

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up
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
```

### Frontend — run from `frontend/`

```bash
pnpm install
pnpm dev            # dev server on :3000
pnpm build          # production build
pnpm lint           # ESLint
pnpm test:run       # Vitest, single run
pnpm test:e2e       # Playwright (install browsers once: pnpm exec playwright install chromium)
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

### Frontend

- Next.js App Router under `frontend/app/`; server-only logic in
  `frontend/server/` (server actions, schemas), pure helpers in `frontend/lib/`.
- Import through the `@/` alias.
- shadcn primitives belong in `frontend/components/ui/`.

## Domain model, in one line

Domain data is **multi-tenant**: every row belongs to an organization and access
is resolved through the caller's membership in it. One Supabase access token
opens two doors — the API (first-party tokens only) and the MCP server (agent
tokens) — and both reach the same services. See "What each layer protects" in
`backend/README.md`.

## Testing expectations

- Tests are part of the work: if a change touches logic, add or update tests
  unless told otherwise.
- Backend: pytest, split into `tests/unit` and `tests/integration` (real
  Postgres, forged Supabase tokens). Frontend: Vitest (`__tests__/`, MSW for the
  backend) and Playwright (`e2e/`).
- CI runs lint, format check, tests and build per app via
  `.github/workflows/backend.yml` and `frontend.yml`.

## Maintainer

Jonathan Freire — <https://jonathanfreire.com>
