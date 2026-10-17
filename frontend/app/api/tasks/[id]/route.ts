import { NextResponse } from "next/server";

import { VaultUnreadable, getTask } from "@/lib/vault/api";
import { getSession } from "@/server/auth/auth.lib";

/**
 * One of the caller's tasks, as JSON, so the dialog can watch it work.
 *
 * A route handler rather than a server action because this is a read on an
 * interval and not an intent: nothing here writes and nothing here decides who
 * may read. The session's token is what the API checks, and a task belonging to
 * someone else answers exactly as an unknown id does — one 404 for both.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Not signed in." }, { status: 401 });
  }

  try {
    const task = await getTask(session.session.token, id);

    if (!task) {
      return NextResponse.json({ error: "No such task." }, { status: 404 });
    }

    return NextResponse.json(task);
  } catch (error) {
    if (!(error instanceof VaultUnreadable)) {
      throw error;
    }

    return NextResponse.json({ error: error.message }, { status: 502 });
  }
}
