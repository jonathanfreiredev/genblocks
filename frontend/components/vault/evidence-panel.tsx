"use client";

import { CopyButton } from "@/components/copy-button";
import { AttemptLedger } from "@/components/ui/attempt-ledger";
import { ScoreReadout } from "@/components/ui/score-readout";
import { VerdictStamp } from "@/components/ui/verdict-stamp";
import { cn } from "@/lib/utils";
import { attemptRows } from "@/lib/vault/attempts";
import { checkRows } from "@/lib/vault/checks";
import { scoresFor, stampFor } from "@/lib/vault/rubric";
import type {
  Generation,
  HarnessChecks,
  Kind,
  Verdict,
} from "@/lib/vault/types";

/** What one judged artifact says about itself. */
export interface Judged {
  scores: Record<string, number> | null;
  verdict: Verdict;
  rubricVersion: string | null;
  model: string | null;
  traceId: string | null;
  /** What the sandbox found, when the artifact came out of one. */
  checks: HarnessChecks | null;
}

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
 */
export function EvidencePanel({
  kind,
  judged,
  attempts,
  selectedAttempt,
  onSelectAttempt,
}: {
  kind: Kind;
  judged: Judged;
  /** The attempts, oldest first. */
  attempts?: Generation[];
  selectedAttempt?: number;
  onSelectAttempt?: (attempt: number) => void;
}) {
  const stamp = stampFor(judged.verdict);
  const rows = scoresFor(kind, judged.scores);
  const harness = checkRows(judged.checks);

  return (
    <div className="bg-panel flex flex-col gap-8 p-6">
      <div className="flex flex-col gap-2">
        {stamp ? (
          <VerdictStamp verdict={stamp} />
        ) : (
          <span className="type-label text-ink-faint">Not judged</span>
        )}

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

      {attempts && attempts.length > 0 ? (
        <Group label="Attempts">
          <AttemptLedger
            className="mt-3"
            attempts={attemptRows(attempts)}
            scoreHeading="Lowest"
            selectedAttempt={selectedAttempt}
            onSelectAttempt={onSelectAttempt}
          />
        </Group>
      ) : null}
    </div>
  );
}
