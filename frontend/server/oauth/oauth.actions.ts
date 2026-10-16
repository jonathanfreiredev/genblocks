"use server";

import { returnServerError } from "next-safe-action";

import { protectedProcedure } from "@/lib/safe-action";
import { createClient } from "@/lib/supabase/server";
import { revokeAppSchema } from "./oauth.schemas";

/**
 * Disconnect an application the user had granted access to.
 *
 * Unlike deleting an account this is not destructive — the same client can be
 * granted again — so it does not ask for the password. It does cut the agent
 * off: Supabase invalidates its refresh token, so it cannot keep renewing
 * access. The access token it already holds stays valid until it expires, which
 * is the normal trade-off of stateless verification.
 */
export const revokeAppAction = protectedProcedure
  .inputSchema(revokeAppSchema)
  .action(async ({ parsedInput }) => {
    const supabase = await createClient();

    const { error } = await supabase.auth.oauth.revokeGrant({
      clientId: parsedInput.clientId,
    });

    if (error) {
      returnServerError({
        code: error.status ?? 400,
        message: error.message || "The application could not be disconnected.",
      });
    }

    return { success: true };
  });
