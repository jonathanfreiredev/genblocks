import {
  Activity,
  Database,
  Fingerprint,
  Monitor,
  Plug,
  Server,
  ShieldCheck,
} from "lucide-react";

import { Section, SectionHeading } from "@/components/landing/section";

/**
 * One row per layer, separated by hairlines rather than boxed into cards.
 *
 * Icons are drawn from the icon set in one stroke weight; the tool names stay in
 * the sans face, because monospace belongs to code and measurements, not to a
 * list of product names.
 */
const LAYERS = [
  {
    icon: Monitor,
    name: "Product UI",
    value: "Pages rendered on the server, with one schema validating each input on both sides.",
    tools:
      "Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Motion, React Hook Form, Zod, next-safe-action",
  },
  {
    icon: Fingerprint,
    name: "Identity",
    value: "Credentials, sessions and agent authorization, all delegated.",
    tools:
      "Supabase Auth (OIDC), @supabase/ssr, asymmetric JWTs verified against JWKS",
  },
  {
    icon: Server,
    name: "API",
    value: "One validated HTTP door into the domain, async end to end.",
    tools: "FastAPI, Pydantic v2, SQLAlchemy 2 (async), asyncpg, PyJWT",
  },
  {
    icon: Plug,
    name: "Agent access",
    value: "A second door into the same domain, with the user approving first.",
    tools: "FastMCP, MCP over streamable HTTP, OAuth 2.1 consent",
  },
  {
    icon: Database,
    name: "Data",
    value: "The tenant model, versioned and reversible.",
    tools: "PostgreSQL 17, Alembic",
  },
  {
    icon: Activity,
    name: "Observability",
    value: "Logs you can read in dev and ship as JSON in production.",
    tools: "structlog, request id and access log middleware",
  },
  {
    icon: ShieldCheck,
    name: "Engineering",
    value:
      "Nothing merges unlinted or untested, and the whole loop runs in one command.",
    tools:
      "pytest, Vitest, Playwright, MSW, ruff, ESLint, Prettier, Docker Compose, GitHub Actions",
  },
];

export function StackList() {
  return (
    <Section>
      <SectionHeading
        title="What is already wired"
        lead="Seven layers, and you replace any of them without unpicking the rest."
      />

      <ul className="divide-border/70 divide-y">
        {LAYERS.map((layer) => (
          <li
            key={layer.name}
            className="group grid gap-x-10 gap-y-2 py-6 sm:grid-cols-[12rem_minmax(0,1fr)]"
          >
            <div className="flex items-center gap-2.5">
              <layer.icon
                className="text-muted-foreground group-hover:text-foreground size-4 transition-colors"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              <span className="text-sm font-medium">{layer.name}</span>
            </div>

            <div className="space-y-1.5">
              <p className="max-w-[62ch] text-sm text-pretty">{layer.value}</p>
              <p className="text-muted-foreground max-w-[62ch] text-xs text-pretty">
                {layer.tools}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </Section>
  );
}
