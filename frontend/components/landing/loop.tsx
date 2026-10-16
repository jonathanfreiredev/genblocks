import { Section, SectionHeading } from "@/components/landing/section";

/**
 * The steps in the order they happen, which is what the numbers are for.
 */
const STEPS = [
  {
    title: "Bring the stack up",
    body: "Postgres, the API, the MCP server and the web app, all with reload.",
    command: "docker compose up",
  },
  {
    title: "Point your agent at the door",
    body: "Any client that speaks MCP. Claude Code, opencode, Cursor and n8n all do.",
    command: "http://localhost:8001/mcp",
  },
  {
    title: "Call a tool",
    body: "The client opens a consent screen in the browser.",
    command: "whoami",
  },
  {
    title: "Approve it",
    body: "The tool answers with the profile behind the token.",
    command: null,
  },
];

export function Loop() {
  return (
    <Section>
      <SectionHeading
        title="See it work in five minutes"
        lead="From a clone to an agent reading your domain, with the consent screen in between."
      />

      <ol className="max-w-[62ch] space-y-8">
        {STEPS.map((step, index) => (
          <li key={step.title} className="flex gap-5">
            <span
              aria-hidden="true"
              className="border-border text-muted-foreground mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full border font-mono text-xs"
            >
              {index + 1}
            </span>

            <div className="space-y-2">
              <h3 className="text-sm font-medium">{step.title}</h3>
              <p className="text-muted-foreground text-sm text-pretty">
                {step.body}
              </p>
              {step.command ? (
                <code className="border-border inline-block rounded-md border px-2 py-1 font-mono text-xs">
                  {step.command}
                </code>
              ) : null}
            </div>
          </li>
        ))}
      </ol>

      <p className="text-muted-foreground mt-12 font-mono text-xs">
        # Supabase is the only service you sign up for. The rest runs in Docker.
      </p>
    </Section>
  );
}
