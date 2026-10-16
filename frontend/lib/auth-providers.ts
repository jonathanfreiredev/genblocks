export type AuthProvider = "email" | "google";

const ALLOWED_PROVIDERS: AuthProvider[] = ["email", "google"];

function parseProviders(raw: string | undefined): AuthProvider[] {
  const values = (raw ?? "email")
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter((value): value is AuthProvider =>
      (ALLOWED_PROVIDERS as string[]).includes(value),
    );

  // Never leave the app without a way to log in.
  return values.length > 0 ? values : ["email"];
}

/**
 * Login methods enabled for this deployment, controlled by
 * NEXT_PUBLIC_AUTH_PROVIDERS (e.g. "email,google"). Supabase remains the source
 * of truth: a provider must also be enabled in the Supabase dashboard.
 */
export const authProviders = parseProviders(
  process.env.NEXT_PUBLIC_AUTH_PROVIDERS,
);

export const isProviderEnabled = (provider: AuthProvider) =>
  authProviders.includes(provider);
