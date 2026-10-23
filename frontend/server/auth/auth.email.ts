import type { AuthError } from "@supabase/supabase-js";

import { createClient } from "@/lib/supabase/server";
import { siteUrl } from "./site-url";

/**
 * Ask Supabase to (re)send the signup confirmation email.
 *
 * Shared by the authenticated banner and the public pre-auth flow. Kept out of
 * the next-safe-action module so the banner's client component does not pull
 * the validator into every page's bundle.
 */
export async function sendVerificationEmail(
  email: string,
): Promise<AuthError | null> {
  const supabase = await createClient();

  const { error } = await supabase.auth.resend({
    type: "signup",
    email,
    options: { emailRedirectTo: `${await siteUrl()}/auth/confirm?next=/` },
  });

  return error;
}
