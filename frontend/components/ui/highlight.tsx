import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// The ochre marker. Inline only — it flags a key figure or the winning attempt,
// and never becomes a full-width band.
function Highlight({ className, ...props }: ComponentProps<"mark">) {
  return (
    <mark
      data-slot="highlight"
      className={cn("bg-coral-soft text-on-coral px-0.5", className)}
      {...props}
    />
  );
}

export { Highlight };
