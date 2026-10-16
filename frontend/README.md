# Frontend — Next.js

The web client for the [MCPStack](../README.md). It renders the UI, validates forms, and authenticates users with **Supabase Auth** through `@supabase/ssr`. The session lives in cookies managed by the Next.js server; domain data is read from the FastAPI backend.

## Tech stack

- **Next.js 16** (App Router) and **React 19**
- **TypeScript**
- **Tailwind CSS 4** with **shadcn/ui** components (base-nova style, Lucide icons)
- **React Hook Form** + **Zod** for forms and validation
- **next-safe-action** for type-safe server actions
- **@supabase/ssr** + **@supabase/supabase-js** for authentication
- **@t3-oss/env-nextjs** for environment variable validation
- **Motion** for animations
- **pnpm** as the package manager

## Project structure

```
frontend/
├── app/
│   ├── (root)/            # Public shell: home page + header layout
│   ├── auth/              # login, signup, forgot-password, reset-password, verify-email
│   │   └── confirm/       # Route handler for email links and the OAuth callback
│   ├── api/
│   │   ├── oauth/         # Route handler that records a consent decision
│   │   └── warmup/        # Route handler the page asks to wake the demo
│   ├── profile/           # Protected profile page
│   ├── layout.tsx         # Root layout (fonts, metadata, Toaster, wake-up provider)
│   ├── error.tsx          # Route error boundary
│   ├── not-found.tsx      # 404 page
│   ├── loading.tsx        # Route loading UI
│   └── globals.css        # Tailwind + theme tokens
├── components/
│   ├── auth/              # Auth, profile, change-password and verification components
│   ├── demo/              # The playground: the trace, the approval, and the wake-up
│   ├── ui/                # shadcn/ui primitives
│   └── ...                # Header, avatar menu, sidebar, background
├── server/
│   ├── auth/              # Session helper, server actions, schemas
│   ├── demo/              # The playground action and the shapes the page reads
│   └── users/             # Profile + password server actions and schemas
├── lib/
│   ├── env.js             # Validated env vars
│   ├── auth-providers.ts  # Which login methods are enabled
│   ├── demo-wake.ts       # The question that wakes the demo, and a wait
│   ├── supabase/server.ts # Supabase server client (cookies)
│   ├── supabase/admin.ts  # Supabase admin client (service role; deletes users)
│   ├── safe-action.ts     # Public / protected action clients
│   ├── mcp-clients.ts     # The MCP clients the landing documents
│   └── utils.ts           # cn() helper
├── proxy.ts               # Refreshes the Supabase session on every request
├── __tests__/             # Vitest tests (unit, integration, components)
├── vitest.config.ts       # Vitest configuration
├── vitest.setup.ts        # Test setup (MSW lifecycle)
├── e2e/                   # Playwright end-to-end tests
├── playwright.config.ts   # Playwright configuration
└── package.json
```

## Requirements

- Node.js 20+
- [pnpm](https://pnpm.io/)
- A **Supabase project** (see below)
- The backend running (see `../backend/README.md`)

## Setup

```bash
pnpm install
```

Copy the example environment file and fill in your Supabase project URL and anon key:

```bash
cp .env.example .env
```

Then start the dev server:

```bash
pnpm dev
```

Open http://localhost:3000. Both Supabase and the backend must be reachable for auth and profile data to work.

## Environment variables

| Variable                               | Required | Description                                                                                |
| -------------------------------------- | -------- | ------------------------------------------------------------------------------------------ |
| `BACKEND_URL`                          | Yes      | Base URL of the FastAPI backend.                                                           |
| `NEXT_PUBLIC_SUPABASE_URL`             | Yes      | Supabase project URL (Project Settings > API).                                             |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Yes      | Supabase publishable key (replaces the legacy anon key).                                   |
| `SUPABASE_SECRET_KEY`                  | Yes      | Supabase secret key. **Server-only**; the admin client uses it to delete a user's account. |
| `NEXT_PUBLIC_AUTH_PROVIDERS`           | No       | Enabled login methods, comma-separated: `email,google`. Default `email`.                   |
| `NODE_ENV`                             | No       | Set automatically by Next.js.                                                              |

Variables are validated with `@t3-oss/env-nextjs` in `lib/env.js`. Set `SKIP_ENV_VALIDATION=1` to bypass validation (useful for Docker builds).

## Supabase setup

1. Create a project at [supabase.com](https://supabase.com).
2. **Authentication > Providers**: enable **Email** (and **Google** if you want social login). Google needs a Client ID/Secret from Google Cloud, pasted into Supabase.
3. **Authentication > URL Configuration**: set the **Site URL** and add redirect URLs for your environments, e.g. `http://localhost:3000/auth/confirm` (and the production equivalent). The `emailRedirectTo` / `redirectTo` values used by the actions must be allow-listed here.
4. Copy the project URL and anon key into `frontend/.env`.

### Toggling login methods

Supabase is the source of truth: a provider only works if it is enabled in the dashboard. On top of that, `NEXT_PUBLIC_AUTH_PROVIDERS` controls which options the UI renders. The template ships with **`email` only**; add `google` to enable the social button.

## How it works

- **Session** — `@supabase/ssr` stores the Supabase session in cookies. `proxy.ts` refreshes it on every request, so Server Components always see a valid token. `server/auth/auth.lib.ts` (`getSession()`, memoised with React `cache()`) validates the user with Supabase and fetches the profile from the backend, returning `{ session, user }` or `null`.
- **Server actions** — `server/auth/auth.actions.ts` and `server/users/users.actions.ts` call Supabase (`signUp`, `signInWithPassword`, `signOut`, `signInWithOAuth`, `resetPasswordForEmail`, `updateUser`, `resend`) and the backend. Client components invoke them through `next-safe-action`.
- **Auth flows** — `/auth/login`, `/auth/signup`, `/auth/forgot-password`, `/auth/reset-password` and `/auth/verify-email`. Supabase sends the emails; `app/auth/confirm/route.ts` handles the links (email confirmation, password recovery) and the OAuth callback, exchanges the credential for a session and redirects.
- **Protected actions** — `protectedProcedure` in `lib/safe-action.ts` requires a valid session and exposes the token and user to the action. The token is forwarded to the backend in the `Authorization` header.
- **Account deletion** — `deleteUserAction` asks for the password again, then hard-deletes the profile through the backend and the Supabase identity through the admin client (`lib/supabase/admin.ts`, service role key). It then signs out and leaves the protected area.
- **Guards** — `app/auth/layout.tsx` redirects authenticated users away from the auth pages, while `app/profile/page.tsx` redirects unauthenticated users to `/auth/login`. The root layout shows a resend-verification banner while the email is unverified.
- **Waking the demo** — the backend is allowed to sleep when nobody is looking, so the page wakes it. See below.

## Waking the demo

A deployment that stops idle services is what keeps this project free, and it costs the
first visitor of an idle period a wait. Waking the services early is the page's job:

- `components/demo/wake-provider.tsx` sits in the root layout and asks `/api/warmup` as
  soon as a page mounts, then every three seconds while the answer is "not yet". A hidden
  tab is not asked at all: nobody is waiting, and asking would keep two containers awake
  for an audience of none.
- `app/api/warmup/route.ts` is that question. It goes through the frontend so the browser
  never calls the API directly — `BACKEND_URL` is a server-side address, and inside
  compose it is a container name a browser cannot resolve.
- `components/demo/wake-notice.tsx` says "Waking the demo" under the hero, under the
  playground's button and under the sign-in form. It renders **nothing** when the services
  are up, which is the common case, so most visitors never learn that they can sleep.
- The playground's run (`components/demo/playground.tsx`) retries while the answer is
  still "not yet", so a click that arrives too early waits instead of failing. A decision
  given to a stopped run is deliberately **not** retried: replaying an answer would apply
  it twice.

The wait is bounded. Two minutes without an answer is where the page stops saying the demo
is waking and starts saying it is still asleep, and the run reports the failure it saw.

## OAuth consent screen

`app/oauth/consent/page.tsx` is where Supabase sends a user who is approving an
AI agent (an MCP client such as Claude Code). It is the one place the grant can
be seen before it is given, so it says plainly that the agent will act with the
user's own access instead of implying a narrower one.

- The page needs the `authorization_id` query parameter Supabase adds to the
  redirect. Without it, it shows an error rather than failing silently.
- A visitor with no session is sent to `/auth/login` with the consent URL in
  `next`, and the login form returns there. Google sign-in carries it too.
- `app/api/oauth/decision/route.ts` records the decision through a plain form
  POST, so the screen works without JavaScript. The session cookie is
  `SameSite=Lax`, which is what stops a cross-site POST from approving anything.
- An already-approved client comes back from `getAuthorizationDetails` without
  an `authorization_id`; the page then forwards straight to the client.

One gap remains, deliberate for now: `next` is not threaded through sign-up or
email verification, so a visitor without an account has to finish signing up and
then start the flow again.

## Connected applications

`components/auth/connected-apps-card.tsx`, on the profile page, lists what the
user has approved (`server/oauth/oauth.lib.ts`) and disconnects it
(`server/oauth/oauth.actions.ts`).

Revoking removes the user's **grant**, not the client: the application keeps its
registration and has to ask again, which is why disconnecting does not ask for
the password the way the danger zone does. The access token it already holds
stays valid until it expires — verification is stateless, so there is nothing to
invalidate — which is the normal JWT trade-off rather than a bug.

When the grants cannot be read (Supabase unreachable, or its OAuth server turned
off) the section says so instead of claiming nothing is connected.

`lib/safe-next-path.ts` validates every `next` value, and `app/auth/confirm/route.ts`
uses it too: that parameter arrives in a URL, and honouring it unchecked turns the
page into an open redirect.

## Scripts

| Command         | Description                |
| --------------- | -------------------------- |
| `pnpm dev`      | Start the dev server       |
| `pnpm build`    | Production build           |
| `pnpm start`    | Serve the production build |
| `pnpm lint`     | Run ESLint                 |
| `pnpm test`     | Run tests (watch)          |
| `pnpm test:run` | Run tests once             |
| `pnpm test:e2e` | Run E2E tests (Playwright) |

## Testing

Tests use **Vitest** and **React Testing Library**, configured the way the
[Next.js Vitest guide](https://nextjs.org/docs/app/guides/testing/vitest)
recommends (see `vitest.config.ts`). They live in `__tests__/`, mirroring the
source tree, and import modules through the `@/` alias.

```bash
pnpm test       # watch mode
pnpm test:run   # single run (CI)
```

- **Unit** tests cover pure logic (e.g. `lib/auth-providers.ts`, `lib/api-error.ts`).
- **Integration** tests exercise the server layer (server actions, session helper)
  with the backend mocked by **MSW** (`vitest.setup.ts` + `__tests__/msw/`). They
  opt into the Node environment with `// @vitest-environment node`; the default is
  `jsdom`.
- **Component** tests render forms with React Testing Library and
  `@testing-library/jest-dom` matchers, mocking the server action, `next/navigation`
  and the toast manager.
- **E2E** tests use **Playwright** (`e2e/`, `playwright.config.ts`). They start the
  dev server via `webServer` and cover public routes and the auth guard, so they
  need no Supabase credentials or backend. Install the browser once with
  `pnpm exec playwright install chromium`.
- Authenticated flows (login, profile) need a real Supabase project and a seeded
  user; they are left out of the default smoke.

## UI components

Components under `components/ui/` are generated with [shadcn/ui](https://ui.shadcn.com/) (config in `components.json`). Add more with:

```bash
pnpm dlx shadcn@latest add <component>
```

## Notes for agents

`AGENTS.md` warns that this project uses a Next.js version whose APIs may differ from older training data. Read the bundled guides under `node_modules/next/dist/docs/` before writing Next.js code.
