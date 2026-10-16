import { cache } from "react";

import { env } from "@/lib/env";
import { createClient } from "@/lib/supabase/server";

export type Session = {
  session: {
    token: string;
    expiresAt: string | null;
  };
  user: {
    id: string;
    email: string;
    name: string;
    isVerified: boolean;
  };
};

/**
 * Resolve the current session. The access token is verified locally (cached
 * JWKS) via `getClaims()` instead of calling the Auth server on every request;
 * the domain profile is fetched from the backend, which provisions it on first
 * use.
 */
export const getSession = cache(async (): Promise<Session | null> => {
  const supabase = await createClient();

  // Verifies the JWT signature locally and refreshes the token first when it is
  // close to expiry, writing the updated cookies back through `setAll`.
  const { data: claimsData, error } = await supabase.auth.getClaims();
  const claims = claimsData?.claims;

  if (error || !claims) {
    return null;
  }

  // The raw token is not part of the claims; it is needed for the backend call.
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData.session?.access_token ?? "";
  const expiresAt = sessionData.session?.expires_at
    ? new Date(sessionData.session.expires_at * 1000).toISOString()
    : null;

  let name = (claims.user_metadata?.full_name as string | undefined) ?? "";
  if (token) {
    const response = await fetch(`${env.BACKEND_URL}/v1/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (response.ok) {
      const profile = await response.json();
      name = profile.full_name ?? name;
    }
  }

  return {
    session: { token, expiresAt },
    user: {
      id: claims.sub,
      email: claims.email ?? "",
      name,
      // Email confirmation is not a top-level JWT claim; Supabase mirrors it
      // into user_metadata.email_verified. A missing flag means verified.
      isVerified: claims.user_metadata?.email_verified !== false,
    },
  };
});
