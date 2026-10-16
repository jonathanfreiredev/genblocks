import { cn } from "@/lib/utils";

/**
 * A state, in words.
 *
 * A running operation carries the system's one working cue — a mono caret
 * against the line — instead of a spinner, and a failed one borrows the verdict
 * triad, because a failure is a verdict on that step.
 */
export function StatusWord({
  label,
  running,
  failed,
  muted,
}: {
  label: string;
  running?: boolean;
  failed?: boolean;
  muted?: boolean;
}) {
  return (
    <span
      className={cn(
        "type-label inline-flex items-center gap-2",
        failed
          ? "text-verdict-fail"
          : running
            ? "text-ink"
            : muted
              ? "text-ink-faint"
              : "text-ink-soft",
      )}
    >
      {running ? (
        <span
          aria-hidden
          className="animate-caret bg-ink h-3.5 w-0.5 motion-reduce:animate-none"
        />
      ) : null}
      {label}
    </span>
  );
}
