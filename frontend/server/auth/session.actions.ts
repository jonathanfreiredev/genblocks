"use server";

import { createClient } from "@/lib/supabase/server";
import { sendVerificationEmail } from "./auth.email";
import { getSession } from "./auth.lib";

/**
 * The two session actions the shell calls from client components.
 *
 * They are plain `"use server"` functions rather than next-safe-action
 * procedures: neither takes input, and the header and verification banner are
 * part of every page. Importing the full action client there put Zod into the
 * initial catalogue bundle for no validation benefit.
 */
export async function logoutAction(): Promise<{ success: boolean }> {
  const supabase = await createClient();
  await supabase.auth.signOut();

  return { success: true };
}

export async function resendVerificationEmail(): Promise<{
  success: boolean;
  message?: string;
}> {
  const session = await getSession();

  if (!session) {
    return {
      success: false,
      message: "Sign in again to resend the verification email.",
    };
  }

  const error = await sendVerificationEmail(session.user.email);

  if (error) {
    return {
      success: false,
      message: "Could not resend the verification email. Please try again.",
    };
  }

  return { success: true };
}
