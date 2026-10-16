"use server";

import { returnServerError } from "next-safe-action";
import { z } from "zod";

import { env } from "@/lib/env";
import { publicProcedure } from "@/lib/safe-action";
import { getSession } from "@/server/auth/auth.lib";

/**
 * How long this waits for the API before it gives up and reports the demo as still
 * coming up.
 *
 * Short on purpose. The API may be a slept container that is still starting, and
 * holding the connection here would spend this function's own lifetime on the wait —
 * which is a budget the platform caps, and one the browser can outspend by asking
 * again. Giving up early hands the retry to the page, where every attempt gets a
 * fresh allowance.
 */
const UPSTREAM_TIMEOUT_MS = 8_000;

const runDemoSchema = z.object({
  // Both are set when the visitor is answering a run that stopped to ask them
  // something: the id is the run, and the decision is the answer.
  thread_id: z.string().max(64).optional(),
  decision: z.enum(["accept", "reject"]).optional(),
});

// The statuses an edge returns for a container that is not serving yet, which are
// the same wait as a timeout rather than a failure of the run.
const NOT_READY_STATUSES = [502, 503, 504];

/**
 * Run the playground once, or carry on with a run that stopped to ask something.
 *
 * Public on purpose: the half of the demo worth watching is what the MCP door does
 * when nobody is signed in. The session token rides along when there is one and the
 * backend reports the refusal when there is not, so the browser never sees the token
 * and the refusal is the server's answer rather than ours.
 */
export const runDemoAction = publicProcedure
  .inputSchema(runDemoSchema)
  .action(async ({ parsedInput }) => {
    const session = await getSession();

    const response = await fetch(`${env.BACKEND_URL}/v1/demo/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(session
          ? { Authorization: `Bearer ${session.session.token}` }
          : {}),
      },
      body: JSON.stringify(parsedInput),
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    }).catch(() => null);

    if (!response) {
      // Nothing answered. A slept container is the likely reason and a real outage is
      // the unlikely one, but from here they are the same wait, and the page retries
      // this call rather than the visitor.
      returnServerError({
        code: 503,
        reason: "service_waking",
        message: "The API did not answer in time.",
      });
    }

    if (!response.ok) {
      const waking = NOT_READY_STATUSES.includes(response.status);

      returnServerError({
        code: response.status,
        ...(waking ? { reason: "service_waking" as const } : {}),
        message: waking
          ? "The API did not answer in time."
          : "The playground could not reach the API.",
      });
    }

    return await response.json();
  });
