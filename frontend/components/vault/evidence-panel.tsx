"use client";

import { CopyButton } from "@/components/copy-button";
import { ScoreReadout } from "@/components/ui/score-readout";
import { VerdictStamp } from "@/components/ui/verdict-stamp";
import { cn } from "@/lib/utils";
import { checkRows } from "@/lib/vault/checks";
import type { Judged } from "@/lib/vault/judged";
import { scoresFor, stampFor } from "@/lib/vault/rubric";
import type { Kind } from "@/lib/vault/types";

function Group({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
        {label}
      </h2>
      {children}
    </section>
  );
}

function Row({
  label,
  children,
}: {
  label: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-t py-2.5 first:border-t-0">
      <dt className="text-muted-foreground min-w-0 text-sm">{label}</dt>
      <dd className="shrink-0">{children}</dd>
    </div>
  );
}

/**
 * The evidence half of an item: what the judge decided and how it decided it.
 *
 * The same panel serves a block, an image and a task. `details` is what the item
 * view puts above the numbers — description, category, date, model and trace —
 * so the panel itself does not repeat facts the page already knows. A task page
 * passes nothing and gets the original header, because a run can be a refusal
 * and its verdict belongs on screen.
 */
export function EvidencePanel({
  kind,
  judged,
  showVerdict = true,
  showModel = true,
  showTrace = true,
  details,
  action,
  className,
}: {
  kind: Kind;
  judged: Judged;
  showVerdict?: boolean;
  showModel?: boolean;
  showTrace?: boolean;
  details?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  const stamp = stampFor(judged.verdict);
  const rows = scoresFor(kind, judged.scores);
  const harness = checkRows(judged.checks);
  const traceHost = process.env.NEXT_PUBLIC_LANGFUSE_HOST?.replace(/\/+$/, "");
  const traceUrl =
    traceHost && judged.traceId ? `${traceHost}/trace/${judged.traceId}` : null;
  const header = Boolean(action || showVerdict || showModel);

  return (
    <div
      className={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border p-4",
        className,
      )}
    >
      {header ? (
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            {action}
            {showVerdict ? (
              stamp ? (
                <VerdictStamp verdict={stamp} />
              ) : (
                <span className="text-muted-foreground text-xs">
                  Not judged
                </span>
              )
            ) : null}
          </div>
          {showModel ? (
            <p className="text-muted-foreground text-xs">
              {judged.model ?? "No model ran"}
              {judged.rubricVersion ? ` · ${judged.rubricVersion}` : null}
            </p>
          ) : null}
        </div>
      ) : null}

      {details}

      <Group label="Judge">
        {rows.length > 0 ? (
          <dl className="flex flex-col">
            {rows.map(({ dimension, value }) => (
              <Row key={dimension.key} label={dimension.label}>
                <ScoreReadout value={value} />
              </Row>
            ))}
          </dl>
        ) : (
          <p className="text-muted-foreground text-sm">
            No scores yet. The judge writes them once an attempt is finished.
          </p>
        )}
      </Group>

      {showTrace ? (
        <Group label="Trace">
          <div className="flex items-center justify-between gap-3">
            {traceUrl ? (
              <a
                href={traceUrl}
                target="_blank"
                rel="noreferrer"
                aria-label="Open the trace in Langfuse"
                className="text-muted-foreground hover:text-foreground truncate text-xs underline-offset-4 hover:underline"
              >
                {judged.traceId}
              </a>
            ) : (
              <p className="text-muted-foreground truncate text-xs">
                {judged.traceId ?? "Not recorded"}
              </p>
            )}
            {judged.traceId ? (
              <CopyButton text={judged.traceId} idleLabel="Copy the trace id" />
            ) : null}
          </div>
        </Group>
      ) : null}

      {harness.length > 0 ? (
        <Group label="Harness">
          <dl className="flex flex-col">
            {harness.map((row) => (
              <Row
                key={row.label}
                label={
                  <>
                    {row.label}
                    {row.detail && !row.ok ? (
                      <span className="text-muted-foreground/80 mt-1 block max-w-[40ch] text-xs">
                        {row.detail}
                      </span>
                    ) : null}
                  </>
                }
              >
                <span
                  className={cn(
                    "text-sm font-medium",
                    row.ok ? "text-muted-foreground" : "text-destructive",
                  )}
                >
                  {row.ok ? "ok" : "failed"}
                </span>
              </Row>
            ))}
          </dl>

          {judged.checks && judged.checks.violations.length > 0 ? (
            <ul className="flex flex-col gap-1.5 border-t pt-3">
              {judged.checks.violations.map((violation) => (
                <li
                  // The same rule can be recorded once per ground, so the id
                  // alone is not unique. The scheme is what tells the two rows
                  // apart, in the key and in the sentence.
                  key={`${violation.scheme ?? "light"}-${violation.id}`}
                  className="text-muted-foreground text-xs"
                >
                  <span className="text-foreground">{violation.id}</span>
                  {violation.impact ? ` · ${violation.impact}` : null}
                  {violation.nodes > 0 ? ` · ${violation.nodes} nodes` : null}
                  {violation.scheme === "dark" ? " · dark page" : null}
                </li>
              ))}
            </ul>
          ) : null}
        </Group>
      ) : null}
    </div>
  );
}
