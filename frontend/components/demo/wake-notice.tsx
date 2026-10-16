"use client";

import { RobotMark } from "@/components/demo/robot-mark";
import { useDemoWake } from "@/components/demo/wake-provider";
import { cn } from "@/lib/utils";

/**
 * Says what the demo's services are doing, next to whatever the visitor came for.
 *
 * It renders nothing at all until there is something to say, which is the common
 * case: anyone who arrives while somebody else is on the site never learns that the
 * services can sleep. The wait is only worth mentioning to the visitor paying it.
 *
 * A sleeping robot rather than a spinner, because the wait is the demo's own joke:
 * two containers are catching up, and the page says so instead of appearing broken.
 */
export function WakeNotice({ className }: { className?: string }) {
  const { state } = useDemoWake();

  if (state !== "waking" && state !== "unreachable") {
    return null;
  }

  return (
    <p
      role="status"
      aria-live="polite"
      className={cn(
        "text-muted-foreground inline-flex items-center gap-2 text-sm",
        className,
      )}
    >
      <RobotMark asleep className="size-4 shrink-0" />
      <span>
        {state === "waking" ? "Waking the demo" : "The demo is still asleep"}
      </span>
      <span
        aria-hidden="true"
        className="inline-flex items-end gap-0.5 font-mono text-[11px] leading-none"
      >
        <span className="animate-wake-z inline-block motion-reduce:animate-none">
          z
        </span>
        <span className="animate-wake-z inline-block [animation-delay:0.4s] motion-reduce:animate-none">
          z
        </span>
        <span className="animate-wake-z inline-block text-[13px] [animation-delay:0.8s] motion-reduce:animate-none">
          z
        </span>
      </span>
    </p>
  );
}
