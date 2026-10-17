import { describe, expect, test } from "vitest";

import { SseReader } from "@/lib/sse";

/** One frame, as the backend writes it. */
function frame(name: string, data: string): string {
  return `event: ${name}\ndata: ${data}\n\n`;
}

describe("SseReader", () => {
  test("reads a frame and its name", () => {
    const reader = new SseReader();

    expect(reader.push(frame("token", '{"text":"hi"}'))).toEqual([
      { event: "token", data: '{"text":"hi"}' },
    ]);
  });

  test("reads several frames out of one chunk", () => {
    const reader = new SseReader();

    expect(reader.push(frame("token", "{}") + frame("done", "{}"))).toEqual([
      { event: "token", data: "{}" },
      { event: "done", data: "{}" },
    ]);
  });

  test("waits for the rest of a frame split across chunks", () => {
    const reader = new SseReader();

    // A frame is not a frame until the blank line that ends it: half of one is
    // held, not guessed at.
    expect(reader.push("event: tok")).toEqual([]);
    expect(reader.push('en\ndata: {"te')).toEqual([]);
    expect(reader.push('xt":"hi"}\n\n')).toEqual([
      { event: "token", data: '{"text":"hi"}' },
    ]);
  });

  test("joins a frame's data lines and ignores comments", () => {
    const reader = new SseReader();

    expect(reader.push(": keep-alive\ndata: one\ndata: two\n\n")).toEqual([
      { event: "message", data: "one\ntwo" },
    ]);
  });

  test("tolerates the carriage returns a proxy may add", () => {
    const reader = new SseReader();

    expect(reader.push("event: token\r\ndata: {}\r\n\r\n")).toEqual([
      { event: "token", data: "{}" },
    ]);
  });

  test("drops a frame that carries no data", () => {
    const reader = new SseReader();

    expect(reader.push("event: ping\n\n")).toEqual([]);
  });

  test("names an unnamed frame the way the format does", () => {
    const reader = new SseReader();

    expect(reader.push("data: {} \n\n")).toEqual([
      { event: "message", data: "{} " },
    ]);
  });
});
