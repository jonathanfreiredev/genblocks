import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// The product's "agent console": a near-black panel with mono text and small
// status chips. Used for the running task, the trace and code.
function ConsolePanel({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      data-slot="console-panel"
      className={cn(
        "type-code bg-ink-strong text-band-foreground rounded-md p-4",
        className,
      )}
      {...props}
    />
  );
}

export { ConsolePanel };
