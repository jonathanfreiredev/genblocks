"use server";

import { revalidatePath } from "next/cache";
import { returnServerError } from "next-safe-action";
import { z } from "zod";

import { backendErrorMessage } from "@/lib/api-error";
import { banAdminUser, unbanAdminUser } from "@/lib/admin/api";
import { protectedProcedure } from "@/lib/safe-action";
import { createAdminClient } from "@/lib/supabase/admin";

const banSchema = z.object({
  userId: z.string().uuid(),
  reason: z.string().trim().max(500).optional(),
});

const unbanSchema = z.object({
  userId: z.string().uuid(),
});

export const banUserAction = protectedProcedure
  .inputSchema(banSchema)
  .action(async ({ parsedInput, ctx }) => {
    if (!ctx.user.isAdmin) {
      returnServerError({ code: 403, message: "Only an operator may ban users." });
    }

    try {
      const user = await banAdminUser(
        ctx.session.token,
        parsedInput.userId,
        parsedInput.reason || undefined,
      );

      // The local flag stops existing tokens immediately. Supabase stops a new
      // login; if that call fails the account is still suspended in this app.
      let warning: string | null = null;
      try {
        const admin = createAdminClient();
        const { error } = await admin.auth.admin.updateUserById(
          user.supabase_user_id,
          { ban_duration: "876000h" },
        );
        if (error) {
          warning =
            "The account is suspended here, but Supabase could not block a new login. Try again.";
        }
      } catch {
        warning =
          "The account is suspended here, but Supabase could not block a new login. Try again.";
      }

      revalidatePath("/admin/users");
      revalidatePath(`/admin/users/${user.id}`);
      return { success: true, warning };
    } catch (error) {
      returnServerError({
        code: 403,
        message: backendErrorMessage(
          error instanceof Error ? error.message : undefined,
          "The user could not be banned.",
        ),
      });
    }
  });

export const unbanUserAction = protectedProcedure
  .inputSchema(unbanSchema)
  .action(async ({ parsedInput, ctx }) => {
    if (!ctx.user.isAdmin) {
      returnServerError({ code: 403, message: "Only an operator may unban users." });
    }

    try {
      const user = await unbanAdminUser(ctx.session.token, parsedInput.userId);
      let warning: string | null = null;
      try {
        const admin = createAdminClient();
        const { error } = await admin.auth.admin.updateUserById(
          user.supabase_user_id,
          { ban_duration: "none" },
        );
        if (error) {
          warning =
            "The local suspension is gone, but Supabase still has the login ban. Try again.";
        }
      } catch {
        warning =
          "The local suspension is gone, but Supabase still has the login ban. Try again.";
      }

      revalidatePath("/admin/users");
      revalidatePath(`/admin/users/${user.id}`);
      return { success: true, warning };
    } catch (error) {
      returnServerError({
        code: 403,
        message: backendErrorMessage(
          error instanceof Error ? error.message : undefined,
          "The user could not be unbanned.",
        ),
      });
    }
  });
