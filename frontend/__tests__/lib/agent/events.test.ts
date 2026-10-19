import { describe, expect, test } from "vitest";

import { readAgentEvent } from "@/lib/agent/events";
import type { Task } from "@/lib/vault/types";

const TASK: Task = {
  id: "0b9c1e2a-1111-2222-3333-444455556666",
  kind: "generate_component",
  status: "pending",
  brief: "A pricing page",
  component_id: null,
  created_at: "2026-10-17T09:12:00Z",
  finished_at: null,
  error: null,
  langfuse_trace_id: null,
  cached: false,
  steps: [],
};

describe("readAgentEvent", () => {
  test("reads the words", () => {
    expect(
      readAgentEvent({ event: "token", data: '{"text":"Queued"}' }),
    ).toEqual({
      type: "token",
      text: "Queued",
    });
  });

  test("reads a tool being reached for, and being done with", () => {
    expect(
      readAgentEvent({
        event: "tool",
        data: '{"name":"search_components","state":"started"}',
      }),
    ).toEqual({ type: "tool", name: "search_components", state: "started" });

    expect(
      readAgentEvent({
        event: "tool",
        data: '{"name":"create_component","state":"finished"}',
      }),
    ).toEqual({ type: "tool", name: "create_component", state: "finished" });
  });

  test("reads the task a tool queued", () => {
    expect(
      readAgentEvent({ event: "task", data: JSON.stringify(TASK) }),
    ).toEqual({ type: "task", task: TASK });
  });

  test("reads what the agent found, so the rail can draw it", () => {
    const items = [
      {
        kind: "component",
        id: "0b9c1e2a-aaaa-bbbb-cccc-ddddeeeeffff",
        title: "Tiered pricing",
        detail: "Three plans in a ruled table",
        path: "genblocks/screenshots/abc-1",
        width: null,
        height: null,
      },
      {
        kind: "image",
        id: "0b9c1e2a-9999-8888-7777-666655554444",
        title: "A coastal path at dawn",
        detail: "960×640",
        path: "genblocks/images/xyz",
        width: 960,
        height: 640,
      },
    ];

    expect(
      readAgentEvent({ event: "suggestions", data: JSON.stringify({ items }) }),
    ).toEqual({ type: "suggestions", items });
  });

  test("keeps the cards it can draw and drops the ones it cannot", () => {
    const data = JSON.stringify({
      items: [
        { kind: "component", id: "a", title: "A block", detail: "" },
        // No id: a card that would link nowhere.
        { kind: "component", title: "Nameless", detail: "" },
        // No kind: neither a block nor a picture.
        { id: "b", title: "A thing", detail: "" },
      ],
    });

    expect(readAgentEvent({ event: "suggestions", data })).toEqual({
      type: "suggestions",
      items: [{ kind: "component", id: "a", title: "A block", detail: "" }],
    });
  });

  test("says nothing when a suggestions frame holds nothing drawable", () => {
    expect(
      readAgentEvent({ event: "suggestions", data: '{"items":[]}' }),
    ).toBeNull();
  });

  test("reads an error and an end", () => {
    expect(
      readAgentEvent({
        event: "error",
        data: '{"message":"Nothing was queued."}',
      }),
    ).toEqual({ type: "error", message: "Nothing was queued." });

    expect(readAgentEvent({ event: "done", data: "{}" })).toEqual({
      type: "done",
    });
  });

  test("drops a task it could not render", () => {
    // A task with no steps would draw a checklist of work that is not there.
    expect(
      readAgentEvent({ event: "task", data: '{"id":"x","status":"pending"}' }),
    ).toBeNull();
  });

  test("drops a frame whose body is not JSON", () => {
    expect(readAgentEvent({ event: "token", data: "not json" })).toBeNull();
  });

  test("drops an event nobody has heard of", () => {
    // Forward compatible on purpose: a later phase may add events, and this
    // dialog should ignore them rather than break on them.
    expect(readAgentEvent({ event: "trace", data: "{}" })).toBeNull();
  });
});
