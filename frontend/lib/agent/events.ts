import type { SseEvent } from "@/lib/sse";
import type { Suggestion, Task } from "@/lib/vault/types";

/**
 * What the agent says while it works, as the dialog understands it.
 *
 * A union rather than the wire shapes: the dialog switches on seven cases, and an
 * event nobody has heard of is dropped instead of drawn as a blank. The names on
 * the left are the backend's contract (`app/agent/stream.py`).
 */
export type AgentEvent =
  | { type: "token"; text: string }
  | { type: "tool"; name: string; state: "started" | "finished" }
  | { type: "suggestions"; items: Suggestion[] }
  | {
      type: "proposal";
      kind: "component" | "image";
      brief: string;
      force: boolean;
      width: number | null;
      height: number | null;
      category: string | null;
    }
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

    case "suggestions": {
      const items = Array.isArray(payload.items)
        ? payload.items.filter(isSuggestion)
        : [];

      return items.length > 0 ? { type: "suggestions", items } : null;
    }

    case "proposal":
      return typeof payload.brief === "string"
        ? {
            type: "proposal",
            kind: payload.kind === "image" ? "image" : "component",
            brief: payload.brief,
            force: payload.force === true,
            width: typeof payload.width === "number" ? payload.width : null,
            height: typeof payload.height === "number" ? payload.height : null,
            category:
              typeof payload.category === "string" ? payload.category : null,
          }
        : null;

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

/**
 * Whether one item is a card this dialog can draw.
 *
 * Checked rather than trusted for the same reason a task is: a card without an id
 * is a link that goes nowhere, and one without a title is an empty tile.
 */
function isSuggestion(value: unknown): value is Suggestion {
  if (!value || typeof value !== "object") {
    return false;
  }

  const item = value as Record<string, unknown>;

  return (
    (item.kind === "component" || item.kind === "image") &&
    typeof item.id === "string" &&
    typeof item.title === "string" &&
    typeof item.detail === "string" &&
    // A missing picture is the same as none: the card falls back to its words.
    (item.path === undefined ||
      item.path === null ||
      typeof item.path === "string")
  );
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
