import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { securityHeaders } from "@/lib/security-headers";
import { isPrivatePath } from "@/lib/seo/indexability";
import { cookieOptions } from "@/lib/supabase/cookie-options";

const LEGACY_ID_PATH =
  /^\/(blocks|images)\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i;

/**
 * An old item link carries a UUID; the readable address is the slug.
 *
 * The page can also resolve the alias, but a redirect thrown after the React
 * tree starts streaming reaches the browser as a 200 with a client-side
 * destination. Resolving it here makes the old address a real 308 and keeps the
 * canonical signal unambiguous. A slow or unavailable API falls through to the
 * page, which still has its own redirect and canonical metadata.
 */
async function legacyAlias(request: NextRequest): Promise<NextResponse | null> {
  const match = request.nextUrl.pathname.match(LEGACY_ID_PATH);

  if (!match) {
    return null;
  }

  const backend = process.env.BACKEND_URL?.replace(/\/+$/, "");
  if (!backend) {
    return null;
  }

  const [, section, id] = match;
  const resource = section === "blocks" ? "components" : "images";

  try {
    const response = await fetch(`${backend}/v1/${resource}/${id}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(2000),
    });

    if (!response.ok) {
      return null;
    }

    const item = (await response.json()) as { slug?: string };
    if (!item.slug) {
      return null;
    }

    return NextResponse.redirect(
      new URL(`/${section}/${item.slug}`, request.url),
      308,
    );
  } catch {
    return null;
  }
}

/**
 * Refreshes the Supabase session on every request so Server Components always
 * see a valid token. Without this, an expired access token cannot be refreshed
 * from a Server Component (cookies are read-only there).
 */
export async function proxy(request: NextRequest) {
  const alias = await legacyAlias(request);
  if (alias) {
    return alias;
  }

  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookieOptions,
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet, headers) {
          for (const { name, value } of cookiesToSet) {
            request.cookies.set(name, value);
          }
          response = NextResponse.next({ request });
          for (const { name, value, options } of cookiesToSet) {
            response.cookies.set(name, value, options);
          }
          // Responses that write session cookies must not be cached by a CDN
          // or reverse proxy, or one user's token could be served to another.
          for (const [key, value] of Object.entries(headers)) {
            response.headers.set(key, value);
          }
        },
      },
    },
  );

  // Verify the session locally (JWKS, cached) instead of calling Supabase on
  // every request. This still refreshes the token when it is close to expiry
  // and writes the updated cookies back through `setAll` above.
  await supabase.auth.getClaims();

  // Applied after the session refresh: `setAll` may replace `response`, and the
  // preview route is excluded by this matcher because it sets its own policy.
  for (const [name, value] of Object.entries(securityHeaders())) {
    response.headers.set(name, value);
  }

  // Account and operator pages are not part of the index. The header covers the
  // redirect and the rendered page alike; the page metadata repeats it because
  // a crawler that already has the HTML should not have to trust the transport.
  if (isPrivatePath(request.nextUrl.pathname)) {
    response.headers.set("X-Robots-Tag", "noindex, nofollow, noarchive");
  }

  return response;
}

export const config = {
  matcher: [
    // Run on everything except static assets, images, and the block previews:
    // a preview is a public document, and asking Supabase about the visitor's
    // session before serving one would add a round trip to every item view for
    // an answer the route does not use.
    "/((?!_next/static|_next/image|api/previews|sitemap.xml|robots.txt|manifest.webmanifest|opengraph-image|twitter-image|apple-icon|icon|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
