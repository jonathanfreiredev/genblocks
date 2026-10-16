import { createSafeActionClient } from "next-safe-action";
import { env } from "./env";
import { getSession } from "@/server/auth/auth.lib";

/**
 * Helper to simulate network latency in development mode
 */
const simulateDelay = async () => {
  if (env.NODE_ENV === "development") {
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
};

/**
 * Machine-readable reasons a server error can carry, so clients can branch on
 * the cause without matching on the human-readable message.
 *
 * `service_waking` means the API did not answer in time, which is what a slept
 * container starting looks like from here. It is worth its own reason because it
 * is the one failure a client is expected to retry instead of reporting.
 */
export type ActionErrorReason =
  | "email_not_confirmed"
  | "rate_limited"
  | "service_waking";

/**
 * Base client with global middleware for logging and delay
 */
export const actionClient = createSafeActionClient({
  // Global error handler
  handleServerError: (
    error,
  ): {
    code: number;
    message: string;
    reason?: ActionErrorReason;
  } => ({
    code: 500,
    message: error.message || "An unexpected server error occurred.",
  }),
}).use(async ({ next }) => {
  await simulateDelay();
  return next();
});

/**
 * Procedure: Public Action
 * Available for everyone, but includes the global delay and validation
 */
export const publicProcedure = actionClient;

/**
 * Procedure: Protected Action
 * Verifies the user session before executing the action logic
 */
export const protectedProcedure = actionClient.use(async ({ next }) => {
  const session = await getSession();

  if (!session) {
    throw new Error(
      "Unauthorized: You must be logged in to perform this action",
    );
  }

  // Inject the user session into the context (ctx)
  return next({
    ctx: {
      user: session.user,
      session: session.session,
    },
  });
});
