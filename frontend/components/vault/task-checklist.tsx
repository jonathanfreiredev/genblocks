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
    <table
      className={cn("type-meta w-full border-collapse text-left", className)}
    >
      <caption className="sr-only">
        The steps this task has run, in order
      </caption>

      <thead>
        <tr className="border-rule-strong border-b">
          <th scope="col" className="type-label text-ink-faint py-2 pr-4">
            №
          </th>
          <th scope="col" className="type-label text-ink-faint py-2 pr-4">
            Step
          </th>
          <th scope="col" className="type-label text-ink-faint py-2 pr-4">
            Status
          </th>
          <th scope="col" className="type-label text-ink-faint py-2 text-right">
            Took
          </th>
        </tr>
      </thead>

      <tbody>
        {steps.map((step, index) => {
          const detail = detailLine(step.detail);

          return (
            <tr
              key={step.id}
              className={cn(
                "border-rule border-b align-top",
                index % 2 === 1 ? "bg-panel-sunken" : "bg-panel",
              )}
            >
              <td className="text-ink-faint py-2.5 pr-4 tabular-nums">
                {step.index + 1}
              </td>
              <td className="text-ink py-2.5 pr-4">
                {step.name}
                {detail ? (
                  <span className="text-ink-faint mt-1 block">{detail}</span>
                ) : null}
              </td>
              <td className="py-2.5 pr-4">
                <StatusWord
                  label={STEP_STATUS_LABELS[step.status]}
                  running={step.status === "running"}
                  failed={step.status === "failed"}
                  muted={step.status === "pending"}
                />
              </td>
              <td className="text-ink-soft py-2.5 text-right tabular-nums">
                {elapsed(step.started_at, step.finished_at)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
