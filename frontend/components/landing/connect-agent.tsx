"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { CopyButton } from "@/components/landing/copy-button";
import { Section, SectionHeading } from "@/components/landing/section";
import { MCP_CLIENTS } from "@/lib/mcp-clients";
import { cn } from "@/lib/utils";

/**
 * How to point a client at the server, one client at a time.
 *
 * Clients disagree on how they are told about a server, so each tab shows
 * whatever that one needs: a command, a config file, or the URL and the node
 * settings. The snippet in the panel is the string the copy button hands over.
 */
export function ConnectAgent() {
  const [activeId, setActiveId] = useState(MCP_CLIENTS[0].id);
  const active = MCP_CLIENTS.find((client) => client.id === activeId) ?? MCP_CLIENTS[0];

  return (
    <Section>
      <SectionHeading
        title="Connect your agent"
        lead="Four ways to tell a client where the server is. The sign-in is the same in all of them: the first call opens a consent screen in the browser, and the token that comes back can only reach the tools."
      />

      <div className="border-border flex flex-wrap gap-1 border-b">
        {MCP_CLIENTS.map((client) => {
          const isActive = client.id === active.id;

          return (
            <button
              key={client.id}
              type="button"
              aria-pressed={isActive}
              onClick={() => setActiveId(client.id)}
              className={cn(
                "-mb-px border-b-2 px-3 py-2 text-sm transition-colors",
                isActive
                  ? "border-foreground text-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground border-transparent",
              )}
            >
              {client.name}
            </button>
          );
        })}
      </div>

      <div
        role="group"
        aria-label={`${active.name} setup`}
        className="mt-8 max-w-3xl space-y-5"
      >
        <p className="text-muted-foreground text-sm text-pretty">{active.where}</p>

        <div className="border-border rounded-xl border p-5">
          <div className="flex items-start justify-between gap-4">
            <pre className="min-w-0 font-mono text-xs leading-6 break-words whitespace-pre-wrap sm:text-sm">
              {active.snippet}
            </pre>
            <CopyButton
              text={active.snippet}
              idleLabel={active.copyLabel}
              className="-mt-1 shrink-0"
            />
          </div>
        </div>

        <p className="text-muted-foreground text-sm text-pretty">{active.next}</p>

        <p className="text-sm">
          <Link
            href={active.docs}
            target="_blank"
            rel="noreferrer"
            className="decoration-border hover:decoration-foreground inline-flex items-center gap-1 font-medium underline underline-offset-4 transition-[text-decoration-color]"
          >
            {active.name} documentation
            <ArrowUpRight className="size-3.5" />
          </Link>
        </p>
      </div>
    </Section>
  );
}
