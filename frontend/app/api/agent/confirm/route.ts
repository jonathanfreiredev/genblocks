import { NextResponse } from "next/server";

import { backendErrorMessage } from "@/lib/api-error";
import { confirmBrief } from "@/lib/agent/api";
import { chatRequestSchema } from "@/server/agent/agent.schemas";
import { getSession } from "@/server/auth/auth.lib";

const confirmSchema = chatRequestSchema
  .pick({ message: true })
  .transform((value) => ({ brief: value.message }));

/**
 * The person's confirmation, not the model's.
 *
 * The assistant prepares a brief and sends it to the dialog as a proposal. This
 * route is what the button calls; it is the only way the conversation can turn a
 * brief into a task. A prompt injection in a search result can change the words
 * on screen, but it cannot press this button.
 */
export async function POST(request: Request) {
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Not signed in." }, { status: 401 });
  }

  const body: unknown = await request.json().catch(() => null);
  const parsed = confirmSchema.safeParse(
    body && typeof body === "object"
      ? {
          message:
            "brief" in body && typeof body.brief === "string" ? body.brief : "",
        }
      : null,
  );

  if (!parsed.success) {
    return NextResponse.json(
      { error: "That brief cannot be queued." },
      { status: 422 },
    );
  }

  const force =
    body !== null &&
    typeof body === "object" &&
    "force" in body &&
    body.force === true;

  let upstream: Response;

  try {
    upstream = await confirmBrief(session.session.token, {
      ...parsed.data,
      force,
    });
  } catch {
    return NextResponse.json(
      { error: "The task could not be queued. Nothing was created." },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    const detail: unknown = await upstream
      .json()
      .then((answer) => answer.detail)
      .catch(() => null);

    return NextResponse.json(
      {
        error: backendErrorMessage(
          detail,
          "The task could not be queued. Nothing was created.",
        ),
      },
      {
        status:
          upstream.status === 422 ? 422 : upstream.status === 429 ? 429 : 502,
      },
    );
  }

  return NextResponse.json(await upstream.json(), {
    status: upstream.status,
  });
}
