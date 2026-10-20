import "server-only";

import { env } from "@/lib/env";

/**
 * One turn of the conversation, asked of the API.
 *
 * The token is the whole of the request: the API decides who is talking and
 * whose task it will be, and nothing here is allowed to guess. The response body
 * is left unread on purpose — it is the stream, and it belongs to the browser.
 */
export async function confirmBrief(
  token: string,
  proposal: { brief: string; force?: boolean },
): Promise<Response> {
  return fetch(`${env.BACKEND_URL}/v1/agent/confirm`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(proposal),
  });
}

export async function streamTurn(
  token: string,
  turn: { message: string; threadId: string },
  signal: AbortSignal,
): Promise<Response> {
  return fetch(`${env.BACKEND_URL}/v1/agent/chat`, {
    method: "POST",
    // Nothing may hold this answer until it is complete, or there is no answer
    // until the turn is over.
    cache: "no-store",
    signal,
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message: turn.message, thread_id: turn.threadId }),
  });
}
