import type { ComponentProps } from "react"

import { cn } from "@/lib/utils"
import { VerdictStamp } from "@/components/ui/verdict-stamp"

type Verdict = "pass" | "retry" | "fail"

type Attempt = {
  attempt: number
  timestamp: string
  score: number
  verdict: Verdict
}

// One row per attempt. This table is a first-class surface: it is the product's
// argument, so it gets rules, tabular figures and the verdict stamp, not a list
// of cards.
function AttemptLedger({
  className,
  attempts,
  ...props
}: ComponentProps<"table"> & { attempts: Attempt[] }) {
  return (
    <table
      data-slot="attempt-ledger"
      className={cn("w-full border-collapse type-meta text-left", className)}
      {...props}
    >
      <thead>
        <tr className="border-b border-rule-strong">
          <th className="type-label py-2 pr-4 text-ink-faint">№</th>
          <th className="type-label py-2 pr-4 text-ink-faint">Attempted</th>
          <th className="type-label py-2 pr-4 text-right text-ink-faint">
            Score
          </th>
          <th className="type-label py-2 text-ink-faint">Verdict</th>
        </tr>
      </thead>
      <tbody>
        {attempts.map((row, index) => (
          <tr
            key={row.attempt}
            className={cn(
              "border-b border-rule",
              index % 2 === 1 ? "bg-panel-sunken" : "bg-panel"
            )}
          >
            <td className="py-2 pr-4 text-ink-faint tabular-nums">
              {row.attempt}
            </td>
            <td className="py-2 pr-4 text-ink-soft tabular-nums">
              {row.timestamp}
            </td>
            <td className="py-2 pr-4 text-right text-ink tabular-nums">
              {row.score}
            </td>
            <td className="py-2">
              <VerdictStamp verdict={row.verdict} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export { AttemptLedger }
export type { Attempt }
