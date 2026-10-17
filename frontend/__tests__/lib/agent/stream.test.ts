import { describe, expect, test } from "vitest";

import { readTurn } from "@/lib/agent/stream";
import type { AgentEvent } from "@/lib/agent/events";

/** A body that arrives in the pieces the network happened to have ready. */
function body(...pieces: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();

  return new ReadableStream({
    start(controller) {
      for (const piece of pieces) {
        controller.enqueue(encoder.encode(piece));
      }

      controller.close();
    },
  });
}

async function read(...pieces: string[]): Promise<AgentEvent[]> {
  const events: AgentEvent[] = [];

  await readTurn(body(...pieces), (event) => events.push(event));

  return events;
}

describe("readTurn", () => {
  test("hands the events over in the order they arrive", async () => {
    const events = await read(
      'event: tool\ndata: {"name":"search_components","state":"started"}\n\n',
      'event: token\ndata: {"text":"Nothing"}\n\n',
      "event: done\ndata: {}\n\n",
    );

    expect(events).toEqual([
      { type: "tool", name: "search_components", state: "started" },
      { type: "token", text: "Nothing" },
      { type: "done" },
    ]);
  });

  test("assembles a frame that arrived in three pieces", async () => {
    // A token split across reads is the normal case on a slow connection.
    expect(await read("event: tok", 'en\ndata: {"text":"hi"}\n', "\n")).toEqual(
      [{ type: "token", text: "hi" }],
    );
  });

  test("says nothing about an event it does not know", async () => {
    expect(await read("event: trace\ndata: {}\n\n")).toEqual([]);
  });

  test("ends when the stream does, whatever it was in the middle of", async () => {
    // The last frame of a cut-off stream is dropped: half an event is not one.
    expect(await read('event: token\ndata: {"te')).toEqual([]);
  });
});
