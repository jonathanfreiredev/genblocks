import { NextResponse } from "next/server";

import { backendErrorMessage } from "@/lib/api-error";
import { streamTurn } from "@/lib/agent/api";
import { chatRequestSchema } from "@/server/agent/agent.schemas";
import { getSession } from "@/server/auth/auth.lib";

/**
 * The conversation, passed through to the browser as it happens.
 *
 * A route handler rather than a server action because a turn answers over
 * seconds and a server action answers once, at the end. It is also the only
 * place the session's token can be attached: that token lives in an httpOnly
 * cookie, so the browser cannot call the backend itself, and a stream cannot be
 * buffered into a return value on the way through.
 */
export async function POST(request: Request) {
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Not signed in." }, { status: 401 });
  }

  const parsed = chatRequestSchema.safeParse(
    await request.json().catch(() => null),
  );

  if (!parsed.success) {
    return NextResponse.json(
      { error: "That message cannot be sent." },
      { status: 422 },
    );
  }

  let upstream: Response;

  try {
    upstream = await streamTurn(
      session.session.token,
      parsed.data,
      request.signal,
    );
  } catch {
    return NextResponse.json(
      { error: "The agent did not answer. Nothing was queued." },
      { status: 502 },
    );
  }

  if (!upstream.ok || !upstream.body) {
    const detail: unknown = await upstream
      .json()
      .then((body) => body.detail)
      .catch(() => null);

    return NextResponse.json(
      {
        error: backendErrorMessage(
          detail,
          "The agent did not answer. Nothing was queued.",
        ),
      },
      { status: 502 },
    );
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      // Nothing between here and the browser may hold the frames back or rewrite
      // them: a stream that arrives whole is not a stream.
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
