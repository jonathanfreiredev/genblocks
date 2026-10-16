import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";
import { VerdictStamp } from "@/components/ui/verdict-stamp";

type Verdict = "pass" | "retry" | "fail";

type Attempt = {
  attempt: number;
  timestamp: string;
  /** The number the row is read by; `null` when there is nothing to read yet. */
  score: number | null;
  /**
   * What the number is when it is not a plain score. The vault writes the
   * rubric dimension that decided the verdict beside it, because a mean would
   * hide the one number that mattered.
   */
  scoreNote?: string;
  /** `null` while nobody has judged the attempt yet. */
  verdict: Verdict | null;
};

// One row per attempt. This table is a first-class surface: it is the product's
// argument, so it gets rules, tabular figures and the verdict stamp, not a list
// of cards. With `onSelectAttempt` it becomes the way a reader walks the attempt
// history, so the number is a control rather than a cell.
function AttemptLedger({
  className,
  attempts,
  scoreHeading = "Score",
  onSelectAttempt,
  selectedAttempt,
  ...props
}: ComponentProps<"table"> & {
  attempts: Attempt[];
  scoreHeading?: string;
  /**
   * Named away from `onSelect` on purpose: a `<table>` already has a DOM
   * `onSelect` handler and the two cannot share one prop.
   */
  onSelectAttempt?: (attempt: number) => void;
  selectedAttempt?: number;
}) {
  return (
    <table
      data-slot="attempt-ledger"
      className={cn("type-meta w-full border-collapse text-left", className)}
      {...props}
    >
      <thead>
        <tr className="border-rule-strong border-b">
          <th className="type-label text-ink-faint py-2 pr-4">№</th>
          <th className="type-label text-ink-faint py-2 pr-4">Attempted</th>
          <th className="type-label text-ink-faint py-2 pr-4 text-right">
            {scoreHeading}
          </th>
          <th className="type-label text-ink-faint py-2">Verdict</th>
        </tr>
      </thead>
      <tbody>
        {attempts.map((row, index) => {
          const selected = row.attempt === selectedAttempt;

          return (
            <tr
              key={row.attempt}
              data-selected={selected ? true : undefined}
              className={cn(
                "border-rule border-b",
                selected || index % 2 === 1 ? "bg-panel-sunken" : "bg-panel",
              )}
            >
              <td className="text-ink-faint py-2 pr-4 tabular-nums">
                {onSelectAttempt ? (
                  <button
                    type="button"
                    onClick={() => onSelectAttempt(row.attempt)}
                    aria-current={selected ? "true" : undefined}
                    className="text-ink-faint hover:text-ink aria-[current]:text-ink underline-offset-4 hover:underline aria-[current]:font-bold"
                  >
                    {row.attempt}
                    <span className="sr-only">
                      {` — show attempt ${row.attempt}`}
                    </span>
                  </button>
                ) : (
                  row.attempt
                )}
              </td>
              <td className="text-ink-soft py-2 pr-4 tabular-nums">
                {row.timestamp}
              </td>
              <td
                className={cn(
                  "py-2 pr-4 text-right tabular-nums",
                  row.score === null ? "text-ink-faint" : "text-ink",
                )}
              >
                {row.score ?? "—"}
                {row.scoreNote ? (
                  <span className="text-ink-faint ml-2">{row.scoreNote}</span>
                ) : null}
              </td>
              <td className="py-2">
                {row.verdict ? (
                  <VerdictStamp verdict={row.verdict} />
                ) : (
                  <span className="type-label text-ink-faint">Not judged</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export { AttemptLedger };
export type { Attempt };
