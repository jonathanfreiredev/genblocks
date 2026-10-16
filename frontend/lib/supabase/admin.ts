import { createClient } from "@supabase/supabase-js";

import { env } from "@/lib/env";

/**
 * Supabase admin client, for operations the anon key cannot perform — deleting a
 * user, for example. It authenticates with the service role key, which bypasses
 * RLS, so it must only be imported from server code (Server Actions, Route
 * Handlers) and never from a Client Component. It does not read the session
 * cookies.
 */
export function createAdminClient() {
  return createClient(env.NEXT_PUBLIC_SUPABASE_URL, env.SUPABASE_SECRET_KEY, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}
