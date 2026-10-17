/**
 * Server-sent events, read a chunk at a time.
 *
 * The stream arrives in whatever pieces the network had ready, so a frame can
 * be split across two reads and two frames can arrive in one: this assembles
 * them. It is one file rather than part of the agent's code because the format
 * is not the agent's — it is the format, and the next stream will use it too.
 */

export interface SseEvent {
  /** The frame's `event:` name, or `"message"` when it did not name one. */
  event: string;
  /** The frame's `data:` lines, joined with newlines. */
  data: string;
}

const FRAME_END = "\n\n";

export class SseReader {
  private buffer = "";

  /** Take whatever arrived, and return the frames it completed. */
  push(chunk: string): SseEvent[] {
    // A frame ends at a blank line, and a proxy is entitled to send CRLF.
    this.buffer += chunk.replaceAll("\r\n", "\n");

    const complete: SseEvent[] = [];
    let end = this.buffer.indexOf(FRAME_END);

    while (end !== -1) {
      const frame = readFrame(this.buffer.slice(0, end));
      this.buffer = this.buffer.slice(end + FRAME_END.length);

      if (frame) {
        complete.push(frame);
      }

      end = this.buffer.indexOf(FRAME_END);
    }

    return complete;
  }
}

/** One frame's lines, as an event — or nothing, for a frame that says nothing. */
function readFrame(frame: string): SseEvent | null {
  let name = "";
  const data: string[] = [];

  for (const line of frame.split("\n")) {
    // A comment is a line the server may use to keep a connection warm.
    if (line === "" || line.startsWith(":")) {
      continue;
    }

    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    const raw = colon === -1 ? "" : line.slice(colon + 1);
    const value = raw.startsWith(" ") ? raw.slice(1) : raw;

    if (field === "event") {
      name = value;
    } else if (field === "data") {
      data.push(value);
    }
  }

  return data.length > 0
    ? { event: name || "message", data: data.join("\n") }
    : null;
}
