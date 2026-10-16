import { NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";
import { getSession } from "@/server/auth/auth.lib";

/**
 * Approve or deny a pending OAuth authorization.
 *
 * A route handler receiving a plain form POST rather than a server action: the
 * decision is an OAuth protocol step whose only job is to send the user back to
 * the client, and this keeps the consent screen working without JavaScript.
 */
export async function POST(request: Request) {
  const formData = await request.formData();
  const authorizationId = formData.get("authorization_id");
  const decision = formData.get("decision");

  if (typeof authorizationId !== "string" || !authorizationId) {
    return NextResponse.json(
      { error: "Missing authorization_id" },
      { status: 400 },
    );
  }

  // The session cookie is SameSite=Lax, so a cross-site POST cannot arrive here
  // carrying a session: only the user themselves can answer the prompt.
  const session = await getSession();
  if (!session) {
    return NextResponse.redirect(new URL("/auth/login", request.url), {
      status: 303,
    });
  }

  const supabase = await createClient();
  // `skipBrowserRedirect` because the SDK would navigate the browser itself; on
  // the server we return the redirect and let the browser follow it.
  const { data, error } =
    decision === "approve"
      ? await supabase.auth.oauth.approveAuthorization(authorizationId, {
          skipBrowserRedirect: true,
        })
      : await supabase.auth.oauth.denyAuthorization(authorizationId, {
          skipBrowserRedirect: true,
        });

  if (error || !data) {
    const retry = new URL("/oauth/consent", request.url);
    retry.searchParams.set("authorization_id", authorizationId);
    retry.searchParams.set("error", "1");
    return NextResponse.redirect(retry, { status: 303 });
  }

  // Back to the client: with an authorization code when approved, and with an
  // error when denied. Supabase builds that URL from the registered redirect.
  return NextResponse.redirect(data.redirect_url, { status: 303 });
}
