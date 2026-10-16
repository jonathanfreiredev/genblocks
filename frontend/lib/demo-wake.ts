/**
 * The two primitives the wake-up is built from: one question, and a wait.
 *
 * The playground's services are allowed to sleep while nobody is looking, which is
 * what makes them affordable and also what makes the first visit of the day a slow
 * one. Waking them is the page's job, and it starts here.
 */

/** How long one question waits before it counts as unanswered. */
export const PROBE_TIMEOUT_MS = 12_000;

/** This app's own door to the API's warm-up endpoint. */
const WARMUP_PATH = "/api/warmup";

/**
 * What the warm-up answered.
 *
 * `waking` covers everything that is not a plain "both services are up": a slept
 * container the platform is still starting, a refusal, a body of the wrong shape, a
 * timeout. The caller is polling, so a wrong `waking` costs one more round, while a
 * wrong `ready` would send a visitor into a run that cannot finish.
 */
export type DemoProbe = "ready" | "waking";

/**
 * Ask whether the demo's services are up, waking them as a side effect.
 *
 * The question goes to this app's own `/api/warmup` rather than straight to the API:
 * the API's address is a server-side concern, and inside compose it is one a browser
 * cannot resolve at all.
 *
 * Never rejects. Every failure is the same answer, because from the page they are the
 * same situation: it is not ready yet, ask again.
 */
export async function probeDemoServices(): Promise<DemoProbe> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);

  try {
    const response = await fetch(WARMUP_PATH, {
      cache: "no-store",
      signal: controller.signal,
    });

    if (!response.ok) {
      return "waking";
    }

    const answer = (await response.json()) as { ready?: unknown };

    return answer.ready === true ? "ready" : "waking";
  } catch {
    return "waking";
  } finally {
    clearTimeout(timer);
  }
}

/** Wait, for the polling loops that give the services room to come up. */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
