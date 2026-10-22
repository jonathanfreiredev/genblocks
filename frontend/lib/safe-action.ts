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
 */
export type ActionErrorReason = "email_not_confirmed" | "rate_limited";

/**
 * Base client with the development delay applied to every action.
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
