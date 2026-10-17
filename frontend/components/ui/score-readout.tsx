import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// The judge's score: tabular mono numerals, right-aligned, over a hairline bar
// that reads the value on the track. Data — not a donut, not a ring, not a gauge.
function ScoreReadout({
  className,
  value,
  max = 100,
  ...props
}: Omit<ComponentProps<"div">, "children"> & { value: number; max?: number }) {
  const clamped = Math.min(Math.max(value, 0), max);
  const percent = (clamped / max) * 100;

  return (
    <div
      data-slot="score-readout"
      className={cn("flex flex-col items-end gap-1.5", className)}
      {...props}
    >
      <span className="type-score">{clamped}</span>
      <span
        role="meter"
        aria-label="Score"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={max}
        className="bg-hairline block h-px w-16"
      >
        <span className="bg-ink block h-px" style={{ width: `${percent}%` }} />
      </span>
    </div>
  );
}

export { ScoreReadout };
