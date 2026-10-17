import type { SseEvent } from "@/lib/sse";
import type { Task } from "@/lib/vault/types";

/**
 * What the agent says while it works, as the dialog understands it.
 *
 * A union rather than the wire shapes: the dialog switches on five cases, and an
 * event nobody has heard of is dropped instead of drawn as a blank. The names on
 * the left are the backend's contract (`app/agent/stream.py`).
 */
export type AgentEvent =
  | { type: "token"; text: string }
  | { type: "tool"; name: string; state: "started" | "finished" }
  | { type: "task"; task: Task }
  | { type: "error"; message: string }
  | { type: "done" };

/** Decode one frame, or nothing when it is not an event this dialog knows. */
export function readAgentEvent(frame: SseEvent): AgentEvent | null {
  const payload = body(frame.data);

  switch (frame.event) {
    case "token":
      return typeof payload.text === "string"
        ? { type: "token", text: payload.text }
        : null;

    case "tool":
      if (typeof payload.name !== "string") {
        return null;
      }

      return {
        type: "tool",
        name: payload.name,
        state: payload.state === "finished" ? "finished" : "started",
      };

    case "task":
      return isTask(payload) ? { type: "task", task: payload } : null;

    case "error":
      return typeof payload.message === "string"
        ? { type: "error", message: payload.message }
        : null;

    case "done":
      return { type: "done" };

    default:
      return null;
  }
}

/** A frame's body, or an empty shape when it is not JSON at all. */
function body(data: string): Record<string, unknown> {
  try {
    const parsed: unknown = JSON.parse(data);
    return parsed && typeof parsed === "object"
      ? (parsed as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

/**
 * Whether a body is a task this app can render.
 *
 * The task drives a checklist, links and a poll, so it is checked rather than
 * trusted: a payload missing its steps would render as a lie about work that is
 * not there, and the backend's own type is the only thing that knows the rest.
 */
function isTask(
  payload: Record<string, unknown>,
): payload is Record<string, unknown> & Task {
  return (
    typeof payload.id === "string" &&
    typeof payload.kind === "string" &&
    typeof payload.status === "string" &&
    typeof payload.brief === "string" &&
    Array.isArray(payload.steps)
  );
}
