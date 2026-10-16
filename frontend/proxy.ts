import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { cookieOptions } from "@/lib/supabase/cookie-options";

/**
 * Refreshes the Supabase session on every request so Server Components always
 * see a valid token. Without this, an expired access token cannot be refreshed
 * from a Server Component (cookies are read-only there).
 */
export async function proxy(request: NextRequest) {
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

  return response;
}

export const config = {
  matcher: [
    // Run on everything except static assets and images.
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
