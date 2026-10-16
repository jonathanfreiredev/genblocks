/**
 * Human-readable labels for the scopes an OAuth client can request.
 *
 * Supabase's OAuth server supports the standard OIDC scopes, so this covers
 * everything a client can ask for today. A scope with no label is shown as it
 * arrived rather than hidden: the consent screen is the last place the user can
 * see what they are agreeing to.
 */
const SCOPE_LABELS: Record<string, string> = {
  openid: "Confirm who you are",
  email: "See your email address",
  profile: "See your name and profile",
  phone: "See your phone number",
  offline_access: "Stay connected without asking again",
};

export type DescribedScope = {
  id: string;
  label: string;
};

export function describeScopes(
  scope: string | null | undefined,
): DescribedScope[] {
  return (scope ?? "")
    .split(" ")
    .map((id) => id.trim())
    .filter(Boolean)
    .map((id) => ({ id, label: SCOPE_LABELS[id] ?? id }));
}
