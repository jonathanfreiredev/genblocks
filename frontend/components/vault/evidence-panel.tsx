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
    <div>
      <h2 className="type-label text-ink-faint">{label}</h2>
      {children}
    </div>
  );
}

/**
 * The evidence half of an item: what the judge decided and how it decided it.
 *
 * The same panel serves a block, an image and a task — the rubric differs, the
 * shape does not — because the whole claim of the product is that every artifact
 * carries the numbers it earned, in one form a reader learns once.
 *
 * ``showVerdict`` is for the library, where everything on show has already
 * passed: a stamp that always says PASS is decoration, and the item being there
 * is the verdict. A task page keeps it, because a run there can be a refusal.
 *
 * ``action`` is the panel's own control, at the head of the panel rather than
 * floating over the content: the item view puts its collapse there, and the task
 * page passes nothing.
 */
export function EvidencePanel({
  kind,
  judged,
  showVerdict = true,
  action,
}: {
  kind: Kind;
  judged: Judged;
  showVerdict?: boolean;
  action?: React.ReactNode;
}) {
  const stamp = stampFor(judged.verdict);
  const rows = scoresFor(kind, judged.scores);
  const harness = checkRows(judged.checks);

  return (
    <div className="bg-panel flex flex-col gap-8 p-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          {action}
          {showVerdict ? (
            stamp ? (
              <VerdictStamp verdict={stamp} />
            ) : (
              <span className="type-label text-ink-faint">Not judged</span>
            )
          ) : null}
        </div>

        <p className="type-meta text-ink-faint">
          {/* "Unknown" would read as a gap in the record. A null model is not
              unknown — it is a fact: nothing generated this one. */}
          {judged.model ?? "No model ran"}
          {judged.rubricVersion ? ` · ${judged.rubricVersion}` : null}
        </p>
      </div>

      <Group label="Judge">
        {rows.length > 0 ? (
          <dl className="mt-3 flex flex-col">
            {rows.map(({ dimension, value }) => (
              <div
                key={dimension.key}
                className="border-rule flex items-baseline justify-between gap-6 border-t py-2.5"
              >
                <dt className="type-meta text-ink-soft">{dimension.label}</dt>
                <dd>
                  <ScoreReadout value={value} />
                </dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="type-meta text-ink-soft mt-3">
            No scores yet. The judge writes them once an attempt is finished.
          </p>
        )}
      </Group>

      <Group label="Trace">
        <div className="mt-2 flex items-center justify-between gap-4">
          <p className="type-meta text-ink-soft truncate">
            {judged.traceId ?? "Not recorded"}
          </p>
          {judged.traceId ? (
            <CopyButton text={judged.traceId} idleLabel="Copy the trace id" />
          ) : null}
        </div>
      </Group>

      {harness.length > 0 ? (
        <Group label="Harness">
          <dl className="mt-3 flex flex-col">
            {harness.map((row) => (
              <div
                key={row.label}
                className="border-rule flex items-baseline justify-between gap-6 border-t py-2.5"
              >
                <dt className="type-meta text-ink-soft">
                  {row.label}
                  {row.detail && !row.ok ? (
                    <span className="text-ink-faint mt-1 block max-w-[42ch]">
                      {row.detail}
                    </span>
                  ) : null}
                </dt>
                <dd
                  className={cn(
                    "type-label shrink-0",
                    row.ok ? "text-ink-faint" : "text-ink",
                  )}
                >
                  {row.ok ? "ok" : "failed"}
                </dd>
              </div>
            ))}
          </dl>

          {judged.checks && judged.checks.violations.length > 0 ? (
            <ul className="border-rule mt-3 flex flex-col gap-1.5 border-t pt-3">
              {judged.checks.violations.map((violation) => (
                <li key={violation.id} className="type-meta text-ink-soft">
                  <span className="text-ink">{violation.id}</span>
                  {violation.impact ? ` · ${violation.impact}` : null}
                  {violation.nodes > 0 ? ` · ${violation.nodes} nodes` : null}
                </li>
              ))}
            </ul>
          ) : null}
        </Group>
      ) : null}
    </div>
  );
}
