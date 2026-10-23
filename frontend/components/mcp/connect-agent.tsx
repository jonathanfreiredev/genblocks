"use client";

import { ArrowUpRight, Bot } from "lucide-react";

import { CopyButton } from "@/components/copy-button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { mcpClients } from "@/lib/mcp-clients";
import type { McpMode } from "@/lib/mcp";

/** One numbered part of the guide: a 12px section label, not a display heading. */
function Step({
  number,
  title,
  id,
  children,
}: {
  number: string;
  title: string;
  id: string;
  children: React.ReactNode;
}) {
  return (
    <section aria-labelledby={id} className="flex flex-col gap-3">
      <h2 id={id} className="flex items-baseline gap-3">
        <span className="text-muted-foreground font-mono text-xs tabular-nums">
          {number}
        </span>
        <span className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
          {title}
        </span>
      </h2>
      {children}
    </section>
  );
}

/**
 * The setup a reader copies, and the one thing that changes with the host.
 *
 * The endpoint is resolved on the server and passed in, so this component never
 * asks the browser which environment it is in and never renders a command that
 * points at the wrong server. Everything else — the four clients, the consent
 * step, the examples — is the same in both modes.
 */
export function ConnectAgent({
  endpoint,
  mode,
}: {
  endpoint: string;
  mode: McpMode;
}) {
  const clients = mcpClients(endpoint);

  return (
    <div className="mt-8 flex flex-col gap-10">
      <div className="bg-card flex flex-col gap-3 rounded-xl border p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
              Endpoint
            </p>
            <p className="mt-1 font-mono text-sm break-all">{endpoint}</p>
          </div>

          <div className="flex shrink-0 items-center gap-1">
            <Badge variant="outline">
              {mode === "local" ? "Local" : "Production"}
            </Badge>
            <CopyButton text={endpoint} idleLabel="Copy the endpoint" />
          </div>
        </div>

        <p className="text-muted-foreground text-xs">
          Streamable HTTP, with OAuth.{" "}
          {mode === "local"
            ? "This page is running locally, so the commands point at the development server on port 8001."
            : "This page is running on the deployment, so the commands point at its published address."}
        </p>
      </div>

      <Step number="01" title="Add the server" id="mcp-step-add">
        <p className="max-w-[68ch] text-sm">
          Pick the client you use. Each one is told about the same endpoint in
          its own way; the rest of the setup happens on the first call.
        </p>

        <Tabs defaultValue={clients[0].id} className="mt-1 gap-4">
          <TabsList
            variant="line"
            aria-label="MCP clients"
            className="max-w-full justify-start overflow-x-auto"
          >
            {clients.map((client) => (
              <TabsTrigger key={client.id} value={client.id}>
                {client.name}
              </TabsTrigger>
            ))}
          </TabsList>

          {clients.map((client) => (
            <TabsContent key={client.id} value={client.id}>
              <div className="flex flex-col gap-4">
                <p className="text-muted-foreground max-w-[68ch] text-sm">
                  {client.where}
                </p>

                <div className="bg-muted/20 relative rounded-lg border">
                  <pre className="overflow-x-auto p-4 pr-12 font-mono text-xs leading-6 break-words whitespace-pre-wrap sm:text-sm">
                    {client.snippet}
                  </pre>
                  <div className="absolute top-2 right-2">
                    <CopyButton
                      text={client.snippet}
                      idleLabel={client.copyLabel}
                    />
                  </div>
                </div>

                <p className="max-w-[68ch] text-sm">{client.next}</p>

                <a
                  href={client.docs}
                  target="_blank"
                  rel="noreferrer"
                  className="decoration-border hover:decoration-foreground inline-flex w-fit items-center gap-1 text-sm font-medium underline underline-offset-4 transition-[text-decoration-color]"
                >
                  {client.name} documentation
                  <ArrowUpRight className="size-3.5" />
                </a>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </Step>

      <Step number="02" title="Approve the first call" id="mcp-step-approve">
        <p className="max-w-[68ch] text-sm">
          The first tool call opens a consent screen on this site. Sign in if
          you have not already, then approve the request. The token that comes
          back can only reach the MCP tools, never the REST API, and you can end
          an agent&apos;s access at any time under{" "}
          <a
            href="/profile"
            className="decoration-border hover:decoration-foreground font-medium underline underline-offset-4 transition-[text-decoration-color]"
          >
            Profile → Connected applications
          </a>
          .
        </p>
      </Step>

      <Step number="03" title="Ask for something" id="mcp-step-ask">
        <p className="max-w-[68ch] text-sm">
          Then talk to the agent as usual. It can search and read the library,
          plan a brief, and queue a block or an image; a write returns a task,
          and{" "}
          <code className="bg-muted rounded-sm px-1 py-0.5 font-mono text-xs">
            get_task
          </code>{" "}
          follows it to the published result.
        </p>

        <ul className="text-muted-foreground flex flex-col gap-2 text-sm">
          <li>“Find a pricing block with three tiers and a dark treatment.”</li>
          <li>“Show me the newest photography about stone and water.”</li>
          <li>
            “Build a testimonial section for a two-person studio; no people in
            the pictures.”
          </li>
        </ul>

        <p className="flex items-center gap-2 text-sm">
          <Bot className="text-muted-foreground size-4" aria-hidden />
          <span>
            Agents and people see the same library: an agent publishes into the
            same registry this site shows.
          </span>
        </p>
      </Step>
    </div>
  );
}
