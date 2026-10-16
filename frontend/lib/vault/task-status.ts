import type { TaskStatus } from "@/lib/vault/types";

/** A task's state, in words, for the surfaces that print it. */
export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  pending: "Queued",
  running: "Running",
  succeeded: "Succeeded",
  failed: "Failed",
  interrupted: "Interrupted",
};
