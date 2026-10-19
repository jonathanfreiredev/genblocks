import { StatusWord } from "@/components/vault/status-word";
import { cn } from "@/lib/utils";
import { elapsed } from "@/lib/vault/format";
import type { StepStatus, TaskStep } from "@/lib/vault/types";

const STEP_STATUS_LABELS: Record<StepStatus, string> = {
  pending: "Queued",
  running: "Running",
  succeeded: "Done",
  failed: "Failed",
};

/** The step's own detail, as the key/value line the worker wrote it as. */
function detailLine(detail: Record<string, unknown> | null): string | null {
  if (!detail) {
    return null;
  }

  const parts = Object.entries(detail)
    .filter(([, value]) => typeof value !== "object")
    .map(([key, value]) => `${key} ${String(value)}`);

  return parts.length > 0 ? parts.join(" · ") : null;
}

/**
 * The checklist a task is followed by.
 *
 * A task is read as a record: numbered steps, each closing as the worker reaches
 * it, and the state in a word rather than an icon nobody has learned yet.
 */
export function TaskChecklist({
  steps,
  className,
}: {
  steps: TaskStep[];
  className?: string;
}) {
  return (
    <div className={cn("overflow-x-auto rounded-xl border", className)}>
      <table className="w-full border-collapse text-left text-sm">
        <caption className="sr-only">
          The steps this task has run, in order
        </caption>

        <thead>
          <tr className="bg-muted/40 border-b">
            {["№", "Step", "Status", "Took"].map((label) => (
              <th
                key={label}
                scope="col"
                className={cn(
                  "text-muted-foreground px-3 py-2 text-xs font-medium tracking-wide uppercase",
                  label === "Took" && "text-right",
                )}
              >
                {label}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {steps.map((step, index) => {
            const detail = detailLine(step.detail);

            return (
              <tr
                key={step.id}
                className={cn(
                  "border-b align-top last:border-b-0",
                  index % 2 === 1 ? "bg-muted/20" : "bg-background",
                )}
              >
                <td className="text-muted-foreground px-3 py-2.5 tabular-nums">
                  {step.index + 1}
                </td>
                <td className="px-3 py-2.5">
                  {step.name}
                  {detail ? (
                    <span className="text-muted-foreground mt-1 block text-xs">
                      {detail}
                    </span>
                  ) : null}
                </td>
                <td className="px-3 py-2.5">
                  <StatusWord
                    label={STEP_STATUS_LABELS[step.status]}
                    running={step.status === "running"}
                    failed={step.status === "failed"}
                    muted={step.status === "pending"}
                  />
                </td>
                <td className="text-muted-foreground px-3 py-2.5 text-right tabular-nums">
                  {elapsed(step.started_at, step.finished_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
