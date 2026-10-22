"use server";

import type { AuthError } from "@supabase/supabase-js";
import { returnServerError } from "next-safe-action";

import { createClient } from "@/lib/supabase/server";
import { safeNextPath } from "@/lib/safe-next-path";
import { protectedProcedure, publicProcedure } from "@/lib/safe-action";
import {
  forgotPasswordSchema,
  googleSignInSchema,
  loginFormSchema,
  resendVerificationSchema,
  resetPasswordSchema,
  signupFormSchema,
} from "./auth.schemas";
import { siteUrl } from "./site-url";

const LOGIN_ERROR = "Incorrect email or password.";

/**
 * Ask Supabase to (re)send the signup confirmation email. Shared by the
 * authenticated banner flow and the public pre-auth flow.
 */
async function sendVerificationEmail(email: string): Promise<AuthError | null> {
  const supabase = await createClient();

  const { error } = await supabase.auth.resend({
    type: "signup",
    email,
    options: { emailRedirectTo: `${await siteUrl()}/auth/confirm?next=/` },
  });

  return error;
}

export const signupAction = publicProcedure
  .inputSchema(signupFormSchema.omit({ confirmPassword: true }))
  .action(async ({ parsedInput }) => {
    const supabase = await createClient();

    const { data, error } = await supabase.auth.signUp({
      email: parsedInput.email,
      password: parsedInput.password,
      options: {
        data: { full_name: parsedInput.name },
        emailRedirectTo: `${await siteUrl()}/auth/confirm?next=/`,
      },
    });

    if (error) {
      returnServerError({
        code: error.status ?? 400,
        message: error.message,
      });
    }

    // When email confirmation is required, Supabase returns no session and the
    // user must confirm before they can sign in. Supabase sends the email.
    return { success: true, requiresVerification: !data.session };
  });

export const loginAction = publicProcedure
  .inputSchema(loginFormSchema)
  .action(async ({ parsedInput }) => {
    const supabase = await createClient();

    const { error } = await supabase.auth.signInWithPassword({
      email: parsedInput.email,
      password: parsedInput.password,
    });

    if (error) {
      if (error.code === "email_not_confirmed") {
        returnServerError({
          code: 403,
          message: "Please confirm your email address before logging in.",
          reason: "email_not_confirmed",
        });
      }

      if (error.status === 429) {
        returnServerError({
          code: 429,
          message: "Too many attempts. Please try again later.",
          reason: "rate_limited",
        });
      }

      // Anything else (invalid credentials, unexpected) stays generic so we
      // never reveal whether the email exists.
      returnServerError({ code: error.status ?? 400, message: LOGIN_ERROR });
    }

    return { success: true };
  });

export const logoutAction = publicProcedure.action(async () => {
  const supabase = await createClient();
  await supabase.auth.signOut();

  return { success: true };
});

export const signInWithGoogleAction = publicProcedure
  .inputSchema(googleSignInSchema)
  .action(async ({ parsedInput }) => {
    const supabase = await createClient();

    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        // Validated on this side too: this value decides where the browser
        // lands after signing in.
        redirectTo: `${await siteUrl()}/auth/confirm?next=${encodeURIComponent(
          safeNextPath(parsedInput.next),
        )}`,
      },
    });

    if (error) {
      returnServerError({ code: error.status ?? 400, message: error.message });
    }

    // The client navigates to this URL to start the OAuth dance.
    return { url: data.url };
  });

/**
 * Send the "set a password" link to an account that signs in only with Google.
 *
 * Supabase has no endpoint that adds a password from nothing, but its recovery
 * flow does exactly that: the link lands on `/auth/confirm`, which exchanges
 * the token and forwards to `/auth/reset-password`. The account keeps its
 * Google identity; the password is added beside it.
 */
export const requestPasswordSetupAction = protectedProcedure.action(
  async ({ ctx }) => {
    const supabase = await createClient();

    const { error } = await supabase.auth.resetPasswordForEmail(
      ctx.user.email,
      {
        redirectTo: `${await siteUrl()}/auth/confirm?next=/auth/reset-password`,
      },
    );

    if (error?.status === 429) {
      returnServerError({
        code: 429,
        message: "Too many attempts. Please try again later.",
      });
    }

    if (error) {
      returnServerError({
        code: error.status ?? 400,
        message: "Could not send the password setup link. Please try again.",
      });
    }

    return { success: true };
  },
);

export const forgotPasswordAction = publicProcedure
  .inputSchema(forgotPasswordSchema)
  .action(async ({ parsedInput }) => {
    const supabase = await createClient();

    const { error } = await supabase.auth.resetPasswordForEmail(
      parsedInput.email,
      {
        redirectTo: `${await siteUrl()}/auth/confirm?next=/auth/reset-password`,
      },
    );

    if (error) {
      returnServerError({
        code: error.status ?? 400,
        message: "Could not start the password reset. Please try again.",
      });
    }

    return { success: true };
  });

export const resetPasswordAction = publicProcedure
  .inputSchema(resetPasswordSchema.omit({ confirmPassword: true }))
  .action(async ({ parsedInput }) => {
    const supabase = await createClient();

    const { error } = await supabase.auth.updateUser({
      password: parsedInput.password,
    });

    if (error) {
      returnServerError({
        code: error.status ?? 400,
        message: "This reset link is invalid or has expired.",
      });
    }

    return { success: true };
  });

export const resendVerificationAction = protectedProcedure.action(
  async ({ ctx }) => {
    const error = await sendVerificationEmail(ctx.user.email);

    if (error) {
      returnServerError({
        code: error.status ?? 400,
        message: "Could not resend the verification email. Please try again.",
      });
    }

    return { success: true };
  },
);

/**
 * Public resend used by the pre-auth flows (right after signup and from the
 * login page), where there is no session and therefore no `ctx.user.email`.
 */
export const requestVerificationEmailAction = publicProcedure
  .inputSchema(resendVerificationSchema)
  .action(async ({ parsedInput }) => {
    const error = await sendVerificationEmail(parsedInput.email);

    if (error?.status === 429) {
      returnServerError({
        code: 429,
        message: "Too many attempts. Please try again later.",
        reason: "rate_limited",
      });
    }

    // Any other outcome reports success: never reveal whether the address is
    // registered (avoids user enumeration). Supabase rate-limits the sending.
    return { success: true };
  });
