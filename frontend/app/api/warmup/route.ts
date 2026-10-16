import { env } from "@/lib/env";

/**
 * How long this waits for the API before it reports the demo as not up yet.
 *
 * Short on purpose: keeping the connection open here spends a serverless function's
 * lifetime on the wait, which the platform caps. Giving up early hands the retry back
 * to the page, where every attempt gets a fresh allowance.
 */
const UPSTREAM_TIMEOUT_MS = 8_000;

/**
 * The page's wake-up question, asked of the page's own origin.
 *
 * Forwarded to the API instead of being asked by the browser for one reason that
 * shows up twice: `BACKEND_URL` is not always an address a browser can use. Inside
 * compose it is a container name the browser cannot resolve, and in production it is
 * a different host from the page's, which would make every visitor pay for a CORS
 * negotiation first. Here the browser talks to its own origin and this talks to the
 * API.
 *
 * Always 200 and always the same shape: the page polls it, and `ready` is the only
 * answer it acts on.
 */
export async function GET() {
  return Response.json(
    { ready: await apiAndMcpAreUp() },
    { headers: { "Cache-Control": "no-store" } },
  );
}

/**
 * Whether the API says both of the demo's services are up.
 *
 * The API is asked rather than the API and the MCP separately, because the API is what
 * has to reach the MCP: one request starts both containers, and the answer says
 * whether the chain is ready rather than whether half of it is.
 */
async function apiAndMcpAreUp(): Promise<boolean> {
  try {
    const response = await fetch(`${env.BACKEND_URL}/warmup`, {
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });

    if (!response.ok) {
      return false;
    }

    const answer = (await response.json()) as { api?: unknown; mcp?: unknown };

    return answer.api === "ok" && answer.mcp === "ok";
  } catch {
    // A slept container the platform is still starting and an API that is not there at
    // all are the same answer from here: not yet.
    return false;
  }
}
