import { createClient } from "@/lib/supabase/server";

/** An application a user has granted access to, as the profile page shows it. */
export type ConnectedApp = {
  clientId: string;
  name: string;
  scopes: string[];
  /** Already formatted: formatting on the server keeps the render deterministic. */
  grantedAt: string;
};

export type ConnectedAppsResult =
  | { ok: true; apps: ConnectedApp[] }
  /** The grants could not be read: Supabase is unreachable, or its OAuth server is off. */
  | { ok: false };

/**
 * Read the OAuth grants of the signed-in user.
 *
 * A failure is reported rather than swallowed, so the section can say it could
 * not load instead of claiming the user has no connected applications.
 */
export async function listConnectedApps(): Promise<ConnectedAppsResult> {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.oauth.listGrants();

  if (error || !data) {
    console.error("Could not read OAuth grants:", error?.message);
    return { ok: false };
  }

  return {
    ok: true,
    apps: data.map((grant) => ({
      clientId: grant.client.id,
      name: grant.client.name || grant.client.id,
      scopes: grant.scopes,
      grantedAt: formatGrantedAt(grant.granted_at),
    })),
  };
}

function formatGrantedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(date);
}
