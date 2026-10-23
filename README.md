# GenBlocks

GenBlocks is a public registry of UI blocks and stock images generated from a brief. A generated block enters the library only after an independent judge reads its render, code and harness checks and clears it against a rubric. The item page keeps the evidence: the prompt, the files, the judge's scores, the checks and the trace.

The builder never controls that check. A generator that stops when the model says it is done asks you to trust the model. Here a second agent, which never saw the conversation and cannot edit the artifact, decides whether the work is good enough. When it says no, the task fails with its reason and the attempt stays visible.

## How a block gets made

```
brief
  -> exact cache, quota, moderation, image policy
  -> spec: taxonomy and nearest blocks
  -> harness agent: write, build, look, fix
  -> judge: score the artifact
  -> publish, or fail with the reason
```

The assistant, the HTTP API and an MCP client all enter through the same services. Each entry point adds its own transport and identity, then calls the same enqueue function, the same moderation and the same quota check.

Before a task exists, the brief is checked for an exact cache hit, the month's allowance, unsafe text and the image policy. A cached brief returns a finished task marked `Found in the registry` and spends no quota. Ten generations per calendar month are allowed per person, blocks and images together. The product does not generate pictures with people, so a brief that asks for them either gets a no-person rewrite or is refused before anything is queued.

### The spec

The spec is the first model call in the generation pipeline, and it answers one question: which type of block is this? The model sees the level-2 taxonomy and the five published blocks nearest to the brief. It returns a slug from that list, or the run fails. Titles and descriptions stay deterministic, built from the brief.

The same retrieval powers the duplicate guard. A brief close enough to an existing block is answered with that block instead of a new run. The distance is measured, not guessed. A person who has seen the match can still ask for their own version.

### The harness

The builder is a LangGraph agent with a small set of tools: write and read files, list the project, read a skill, look at the render, and ask the image library for a picture. `src/Block.tsx` is the entry point. Only `src/**/*.{tsx,ts,css}` can be written, and `src/main.tsx` plus `src/index.css` belong to the scaffold.

`look` is the part that changes the loop. It builds the project in a Modal sandbox and returns the checker's report with two images: the block on a light page and on the dark one the registry switches to. The agent reads both, fixes what it sees and looks again. The budget counts looks, not model turns, and stops at six by default.

Two static checks run before the sandbox: one refuses external assets outside the allowed hosts, the other refuses network calls, script injection and browser escapes. Both are fatal, and both run inside the loop so the agent can fix the problem while it still can.

A block is a project, not a file. A form can be split into fields and error components. Dependencies are read from the imports and compared with the packages preinstalled in the sandbox. The item page shows the install line the reader needs.

Pictures arrive late, after the layout is settled. The harness asks the library first and reuses a picture it already holds. Only a miss reaches the image provider. A block may use up to four pictures.

### The sandbox

Modal runs the build and the browser. It holds no secret and cannot reach the database. Inside, the project goes through TypeScript, the build and Playwright at four widths: 390, 834, 1024 and 1440. Axe runs in light and dark. Touch targets, focus and reduced motion are checked as well.

The sandbox folds the built page into one HTML document, capped at 2 MB. The block's item page serves that document inside an opaque-origin iframe with `connect-src 'none'` and `form-action 'none'`. A visitor can type, submit and watch an animation. None of it reaches this site or the network.

### The judge

The judge is a separate model call with no tools and no memory of the conversation. It receives the brief, every file, the sandbox report and both renders. It scores five dimensions for a block: render, accessibility, visual, copy and compliance. Images use a shorter rubric: visual, prompt fit and compliance.

Each dimension has its own threshold. A high average does not carry a weak dimension past the gate. The judge is not told the thresholds, so its reading stays independent of the bar the product applies.

The numbers live in Postgres. The judge's notes and summary travel with a failed task and, when configured, the Langfuse trace. An attempt that fails stays on the task page with its render and its reason. It never enters the library.

A real run makes one attempt. Retrying is a decision a person makes with the brief in front of them; the API can queue it, but the interface does not offer a retry button yet.

### Images

Stock images come from Black Forest Labs `flux-2-pro` through its asynchronous API. The backend queues the request, polls it, downloads the finished sample and discards the provider URL. The bytes are decoded, bounded and re-encoded before anything else sees them.

Two gates follow. A vision model refuses any picture with a person or human-like figure. OpenAI moderation then looks for sexual content, violence, hate and the other categories the product does not publish. Groq's safety model can replace OpenAI for text when only a Groq key is configured. A picture that passes the gates is judged, uploaded to Cloudinary, embedded with Voyage and filed in the same library the gallery reads.

Pictures made for a block join the public stock library. That is why a later block can reuse one instead of paying for the same scene again.

### Retrieval and the record

Voyage `voyage-multimodal-3` embeds the screenshot of a block and the bytes of an image. Chroma stores the vectors and their metadata. Development uses a persistent local directory; production points at Chroma Cloud.

Search still works when the index or the embedder is down: it falls back to text. The duplicate guard has its own distance and a way to override it.

Postgres is the source of truth for tasks, steps, scores and published artifacts. The API worker claims a task with `FOR UPDATE SKIP LOCKED` and writes each step as it happens. A restart turns an orphaned `running` task into `interrupted` instead of waiting forever. Langfuse is an optional copy of the run, never the source of truth.

## The assistant and external agents

The chat is a LangGraph agent streamed over server-sent events. It can search the registry, read an item, check a brief, prepare a block and prepare an image. It never queues a task by itself. It prepares a proposal, the dialog shows the brief, and a button sends the confirmation. The chat requires an account; there is no anonymous AI path.

An MCP server exposes the same services to agents outside the app. The tools cover reading (`whoami`, `list_categories`, `search_components`, `get_component`, `search_images`, `get_image`, `list_tasks`, `get_task`), planning (`plan_component`, `plan_image`) and writing (`create_component`, `generate_image`). A write queues a task and returns immediately; `get_task` follows it to the result.

The MCP client registers itself, the user approves the grant on this site, and the token can reach the MCP tools. Connected clients can be revoked from the profile page. The local endpoint is `http://localhost:8001/mcp`.

## Run it locally

You need Node.js 20+, pnpm, Python 3.14+, uv, Docker and a Supabase project.

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up
```

Compose starts PostgreSQL, runs the migrations, then brings up the API, the MCP server and the Next.js app. The first boot waits for the migration service to finish.

Seed the taxonomy and the development vault:

```bash
docker compose exec backend python -m app.categories.seed
docker compose exec backend python -m app.seed.vault
```

Open `http://localhost:3000`. The API is on `http://localhost:8000` and the MCP server on `http://localhost:8001/mcp`. API docs are available at `/docs` only when `ENV=development`, which the Compose stack sets.

To attach the seeded tasks to your account, sign in once and run the vault seed with your email:

```bash
docker compose exec backend python -m app.seed.vault --owner you@example.com
```

The seed is idempotent. Re-running it rewrites the same rows.

### Supabase

Create a project and enable Email under Authentication > Providers. Google is optional. Set the Site URL to `http://localhost:3000` and add `http://localhost:3000/auth/confirm` as a redirect URL. Put the project URL, publishable key and secret key in `frontend/.env`.

`SITE_URL` is optional locally because the app can fall back to the request origin. In production it is required: auth links and redirects must not be built from an attacker-controlled Host header. Set `MCP_URL` to the public MCP base or `/mcp` address so the Connect page does not depend on the request host.

### Provider keys

The seeded gallery works without any provider key. Chat, generation and image tasks need the services that produce them.

For a block generation, set `OPENAI_API_KEY`, the Cloudinary credentials and the Modal tokens, then deploy the sandbox from `backend/`:

```bash
uv run modal deploy app/harness/modal_app.py
```

`OPENAI_API_KEY` covers the chat, the spec, the harness and the judge. `VOYAGE_API_KEY` adds retrieval and the duplicate guard. `BFL_API_KEY` generates stock images. `GROQ_API_KEY` is the text moderation fallback. Cloudinary stores screenshots and pictures; the frontend needs `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME` to display them.

To generate the seeded screenshots and stock images, run the optional seed tools:

```bash
docker compose exec backend python -m app.seed.screenshots
docker compose exec backend python -m app.seed.stock
```

`backend/.env.example` lists every setting. `backend/mcp.env.example` lists the smaller set an MCP deployment needs. `backend/worker.env.example` lists the set the deployed task worker needs.

## Tests

```bash
cd backend
uv run pytest
uv run pytest tests/unit
uv run ruff check .

cd ../frontend
pnpm test:run
pnpm lint
pnpm build
```

The backend suite runs unit tests without a database and integration tests against PostgreSQL with forged Supabase tokens. The frontend uses Vitest and MSW. Playwright is available with `pnpm test:e2e`; the end-to-end suite needs the stack up and the seed applied.

## Production notes

`docker-compose.yml` is a development stack. The frontend is built for Vercel and the backend for its own service. The backend image has a production stage if you deploy it as a container.

The MCP server gets its own environment in production. Use `backend/mcp.env.example`, not a copy of the API environment. It needs the database, Supabase and the moderation keys, shares `TASKS_PER_MONTH` with the API, and can use Resend for policy notices. It does not need Cloudinary, Modal, Black Forest Labs, Voyage, Chroma or Langfuse credentials.

There is no application-level rate limiter. The monthly quota, provider spend caps and authenticated or verified accounts are the current boundary. An edge rule in Vercel, Cloudflare or Cloud Armor is the next lever if abuse appears. Add Turnstile and a rate limit only if an anonymous chat endpoint is introduced.

The API docs are off unless `ENV=development`. The frontend sends security headers and a content security policy on every app route; the preview route carries its own narrower policy.

## Docs

`PLAN.md` holds the decisions and the execution history. `DESIGN.md` is the visual system. `AGENTS.md` is the working guide for agents in this repository. The backend and frontend READMEs cover each app's setup.

## Origin

GenBlocks grew out of `mcp-stack`, a public template I wrote for agent-native SaaS. The identity layer, the MCP server and the FastAPI scaffolding came from it. The registry, the generation loop, the judge and the wall are new.

## License

MIT. See [LICENSE](./LICENSE).
