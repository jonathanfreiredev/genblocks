import { readAgentEvent, type AgentEvent } from "@/lib/agent/events";
import { SseReader } from "@/lib/sse";

/**
 * Read one turn of the conversation off the wire.
 *
 * The body is a stream of bytes that arrives in whatever pieces the network had
 * ready, so frames are assembled here rather than assumed: a token split across
 * two reads is the normal case, not the edge. The wording of the answer is not
 * this function's business — it hands each event to the caller as it lands.
 */
export async function readTurn(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: AgentEvent) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  const frames = new SseReader();

  for (;;) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    for (const frame of frames.push(decoder.decode(value, { stream: true }))) {
      const event = readAgentEvent(frame);

      if (event) {
        onEvent(event);
      }
    }
  }
}
