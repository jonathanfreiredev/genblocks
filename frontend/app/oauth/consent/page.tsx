import { redirect } from "next/navigation";

import { OAuthConsent, OAuthConsentError } from "@/components/oauth-consent";
import { createClient } from "@/lib/supabase/server";
import { getSession } from "@/server/auth/auth.lib";

export const metadata = {
  title: "Authorize an application",
};

/**
 * The consent screen Supabase redirects to during an OAuth authorization.
 *
 * It is the one place where a user can see what an AI agent is asking for before
 * it gets a token, so it says plainly that the agent will act with the user's own
 * access rather than implying a narrower grant.
 */
export default async function OAuthConsentPage({
  searchParams,
}: {
  searchParams: Promise<{ authorization_id?: string; error?: string }>;
}) {
  const { authorization_id: authorizationId, error: failed } =
    await searchParams;

  if (!authorizationId) {
    return (
      <OAuthConsentError message="This consent link is missing its authorization id." />
    );
  }

  // Approving has to be attributable to somebody, so there must be a session.
  // The authorization id rides along in `next` so the flow resumes after login.
  const session = await getSession();
  if (!session) {
    const resumePath = `/oauth/consent?authorization_id=${encodeURIComponent(authorizationId)}`;
    redirect(`/auth/login?next=${encodeURIComponent(resumePath)}`);
  }

  const supabase = await createClient();
  const { data, error } =
    await supabase.auth.oauth.getAuthorizationDetails(authorizationId);

  if (error || !data) {
    return (
      <OAuthConsentError message="This authorization request is not valid any more. Start it again from the application." />
    );
  }

  // A response without an authorization id means the client was approved before,
  // so there is nothing to ask: send the user straight back with a fresh code.
  if ("redirect_url" in data) {
    redirect(data.redirect_url);
  }

  return (
    <OAuthConsent
      authorizationId={data.authorization_id}
      clientName={data.client.name}
      clientUri={data.client.uri}
      redirectUri={data.redirect_uri}
      scope={data.scope}
      failed={Boolean(failed)}
    />
  );
}
