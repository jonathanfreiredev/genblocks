import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

import { env } from "@/lib/env";
import { cookieOptions } from "./cookie-options";

/**
 * Supabase client for the server (Server Components, Server Actions and Route
 * Handlers). The session lives in cookies managed by `@supabase/ssr`.
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    {
      cookieOptions,
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              cookieStore.set(name, value, options);
            }
          } catch {
            // `setAll` throws when called from a Server Component. Session
            // refresh is handled by proxy.ts, so this is safe to ignore here.
          }
        },
      },
    },
  );
}
