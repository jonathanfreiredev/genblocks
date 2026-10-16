"use server";

import { returnServerError } from "next-safe-action";

import { backendErrorMessage } from "@/lib/api-error";
import { env } from "@/lib/env";
import { protectedProcedure } from "@/lib/safe-action";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import {
  deleteUserSchema,
  updateUserPasswordSchema,
  updateUserSchema,
} from "./users.schemas";

export const updateUserAction = protectedProcedure
  .inputSchema(updateUserSchema)
  .action(async ({ parsedInput, ctx }) => {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    // Email lives in Supabase; changing it triggers a confirmation email.
    if (user && parsedInput.email !== user.email) {
      const { error } = await supabase.auth.updateUser({
        email: parsedInput.email,
      });

      if (error) {
        returnServerError({ code: error.status ?? 400, message: error.message });
      }
    }

    // The name is domain data owned by the backend.
    const response = await fetch(`${env.BACKEND_URL}/v1/users/me`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${ctx.session.token}`,
      },
      body: JSON.stringify({ full_name: parsedInput.name }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      returnServerError({
        code: response.status,
        message: backendErrorMessage(
          errorData.detail,
          "An error occurred while updating the profile.",
        ),
      });
    }

    return { success: true, user: await response.json() };
  });

export const updateUserPasswordAction = protectedProcedure
  .inputSchema(updateUserPasswordSchema.omit({ confirmNewPassword: true }))
  .action(async ({ parsedInput, ctx }) => {
    const supabase = await createClient();

    // Re-authenticate with the current password before changing it.
    const { error: reauthError } = await supabase.auth.signInWithPassword({
      email: ctx.user.email,
      password: parsedInput.currentPassword,
    });

    if (reauthError) {
      returnServerError({ code: 400, message: "Incorrect current password." });
    }

    const { error } = await supabase.auth.updateUser({
      password: parsedInput.newPassword,
    });

    if (error) {
      returnServerError({ code: error.status ?? 400, message: error.message });
    }

    return { success: true };
  });

export const deleteUserAction = protectedProcedure
  .inputSchema(deleteUserSchema)
  .action(async ({ parsedInput, ctx }) => {
    const supabase = await createClient();

    // Deleting is irreversible, so re-authenticate before doing anything.
    const { error: reauthError } = await supabase.auth.signInWithPassword({
      email: ctx.user.email,
      password: parsedInput.password,
    });

    if (reauthError) {
      returnServerError({ code: 400, message: "Incorrect password." });
    }

    // 1. Remove the local profile while the access token is still valid.
    const response = await fetch(`${env.BACKEND_URL}/v1/users/me`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${ctx.session.token}` },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      returnServerError({
        code: response.status,
        message: backendErrorMessage(
          errorData.detail,
          "An error occurred while deleting your account.",
        ),
      });
    }

    // 2. Delete the Supabase identity. A user cannot remove their own account
    //    with the anon key, so this goes through the admin API (service role).
    const admin = createAdminClient();
    const { error: deleteError } = await admin.auth.admin.deleteUser(
      ctx.user.id,
    );

    if (deleteError) {
      returnServerError({
        code: deleteError.status ?? 500,
        message:
          "Your profile was deleted, but the account could not be removed. Please contact support.",
      });
    }

    // 3. Clear the session cookies, which are no longer valid.
    await supabase.auth.signOut();

    return { success: true };
  });
