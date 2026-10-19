import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// The judge's score: tabular numerals, right-aligned, with a short track under
// it. A figure to compare down a column, not a gauge.
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
      <span className="text-lg leading-none font-semibold tabular-nums">
        {clamped}
      </span>
      <span
        role="meter"
        aria-label="Score"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={max}
        className="bg-muted block h-1 w-14 overflow-hidden rounded-full"
      >
        <span
          className="bg-foreground block h-full rounded-full"
          style={{ width: `${percent}%` }}
        />
      </span>
    </div>
  );
}

export { ScoreReadout };
