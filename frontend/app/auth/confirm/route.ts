import type { EmailOtpType } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

import { safeNextPath } from "@/lib/safe-next-path";
import { createClient } from "@/lib/supabase/server";

/**
 * Landing point for the links Supabase sends by email (signup confirmation,
 * password recovery) and for the OAuth callback. It exchanges the credential
 * for a session (writing the auth cookies) and then redirects to `next`.
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const tokenHash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;
  // Validated: this is appended to the origin below, and an unchecked `next`
  // would turn this route into an open redirect.
  const next = safeNextPath(searchParams.get("next"));

  const supabase = await createClient();

  if (tokenHash && type) {
    const { error } = await supabase.auth.verifyOtp({
      type,
      token_hash: tokenHash,
    });

    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  } else if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/auth/login?error=link`);
}
