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
    /** A configured operator: the report queue and takedown actions. */
    isAdmin: boolean;
    /**
     * Whether the account also has a password. A sign-up through Google has
     * none, so the screens that re-enter one have to offer an alternative.
     */
    hasPassword: boolean;
  };
};

/**
 * Whether the account can also sign in with a password.
 *
 * Supabase mirrors the linked identities into the token's `app_metadata`, so a
 * Google-only sign-up lists `google` alone and an email account lists `email`.
 * A token without the claim predates it or comes from another issuer: it is
 * treated as password-backed so the stricter re-authentication stays the
 * fallback rather than the exception.
 */
function hasPasswordIdentity(providers: string[] | undefined): boolean {
  if (!providers) {
    return true;
  }

  return providers.includes("email");
}

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
  let isAdmin = false;
  if (token) {
    const response = await fetch(`${env.BACKEND_URL}/v1/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (response.ok) {
      const profile = await response.json();
      name = profile.full_name ?? name;
      isAdmin = profile.is_admin === true;
    } else if (response.status === 403) {
      // The backend refuses a suspended account even when its Supabase token is
      // still cryptographically valid. Treat it as anonymous: public pages keep
      // working, authenticated ones redirect to the login screen.
      return null;
    }
  }

  return {
    session: { token, expiresAt },
    user: {
      id: claims.sub,
      email: claims.email ?? "",
      name,
      // Email confirmation is not a top-level JWT claim; Supabase mirrors it
      // into user_metadata.email_verified. A missing flag is not evidence of
      // verification, so it is treated as unverified.
      isVerified: claims.user_metadata?.email_verified === true,
      isAdmin,
      hasPassword: hasPasswordIdentity(claims.app_metadata?.providers),
    },
  };
});
